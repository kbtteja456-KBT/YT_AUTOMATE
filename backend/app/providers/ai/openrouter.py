"""OpenRouter AI Provider with free-tier defaults, exponential backoff, and JSON repair."""

import json
import re
import time
import httpx
from typing import Any, Optional

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import (
    ProviderError,
    ProviderUnavailableError,
    RateLimitExceededError,
    ZeroCostModeViolationError
)
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import AIProvider

# Curated list of known zero-cost free models on OpenRouter
KNOWN_FREE_MODELS = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "deepseek/deepseek-r1:free",
    "meta-llama/llama-3.1-8b-instruct:free"
]


class OpenRouterProvider(AIProvider):
    """OpenRouter provider implementation conforming strictly to AIProvider abstraction."""

    name = "openrouter"
    provider_type = ProviderType.AI

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 3
    ):
        self.api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.model = model if model is not None else settings.openrouter_model
        self.base_url = (base_url if base_url is not None else settings.openrouter_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        # Validate if current model is free
        self.is_zero_cost = self._is_model_zero_cost(self.model)
        self.is_paid = not self.is_zero_cost

    def _is_model_zero_cost(self, model_name: str) -> bool:
        """Verify whether a model tag indicates zero cost."""
        clean = model_name.strip().lower()
        if clean.endswith(":free") or clean == "openrouter/free":
            return True
        return clean in [m.lower() for m in KNOWN_FREE_MODELS]

    def _clean_json_markdown(self, raw_text: str) -> str:
        """Extract and clean JSON payload from markdown fences or conversational preambles."""
        text = raw_text.strip()
        # 1. Search for fenced ```json ... ``` blocks first
        if "```" in text:
            json_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            for block in reversed(json_blocks):
                b = block.strip()
                if (b.startswith("{") and b.endswith("}")) or (b.startswith("[") and b.endswith("]")):
                    return b

        # 2. Strip thinking blocks if present
        clean = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()

        # Find outermost { or [ and last } or ]
        first_brace = clean.find("{")
        first_bracket = clean.find("[")
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = clean.rfind("}")
            if last_brace != -1:
                clean = clean[first_brace:last_brace + 1]
        elif first_bracket != -1:
            last_bracket = clean.rfind("]")
            if last_bracket != -1:
                clean = clean[first_bracket:last_bracket + 1]

        return clean

    def _attempt_json_repair(self, text: str) -> Optional[dict[str, Any]]:
        """Attempt heuristic recovery of slightly malformed or truncated JSON."""
        cleaned = self._clean_json_markdown(text)
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Try removing trailing commas before closing braces/brackets
        repaired = re.sub(r",\s*([}\]])", r"\1", cleaned)
        try:
            return json.loads(repaired)
        except Exception:
            pass

        # Try auto-closing open brackets/braces
        open_braces = repaired.count("{") - repaired.count("}")
        open_brackets = repaired.count("[") - repaired.count("]")
        if open_braces > 0:
            repaired += "}" * open_braces
        if open_brackets > 0:
            repaired += "]" * open_brackets
        try:
            return json.loads(repaired)
        except Exception:
            return None

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> str:
        """Call OpenRouter with exponential backoff and Zero-Cost verification."""
        self.verify_zero_cost_compliance(
            zero_cost_mode=settings.zero_cost_mode,
            paid_providers_enabled=settings.paid_providers_enabled
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ai-youtube-shorts-autopilot",
            "X-Title": "AI YouTube Shorts Autopilot"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        url = f"{self.base_url}/chat/completions"
        delay = 1.0

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.post(url, json=payload, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                    raise ProviderError("OpenRouter returned empty choices array.")

                if resp.status_code == 429:
                    logger.warning(f"OpenRouter Rate Limit (429) encountered. Backing off {delay}s...")
                    time.sleep(delay)
                    delay *= 2.0
                    continue

                if resp.status_code >= 500:
                    logger.warning(f"OpenRouter Server Error ({resp.status_code}). Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2.0
                    continue

                raise ProviderError(f"OpenRouter API error ({resp.status_code}): {resp.text}")

            except httpx.RequestError as req_err:
                logger.warning(f"OpenRouter connection error on attempt {attempt}: {req_err}")
                if attempt == self.max_retries:
                    raise ProviderUnavailableError(f"OpenRouter unreachable after {self.max_retries} attempts: {req_err}")
                time.sleep(delay)
                delay *= 2.0

        raise ProviderUnavailableError("Exhausted retries calling OpenRouter.")

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.4
    ) -> dict[str, Any]:
        """Generate structured JSON adhering to response_schema with automatic repair."""
        schema_instruction = (
            f"\nCRITICAL: Respond ONLY with a valid, raw JSON object matching this schema:\n"
            f"{json.dumps(response_schema, indent=2)}\n"
            f"Do NOT include conversational preambles, comments, or explanations outside the JSON."
        )
        full_system = f"{system_prompt or ''}\n{schema_instruction}".strip()

        raw_output = await self.generate_text(
            prompt=prompt,
            system_prompt=full_system,
            temperature=temperature,
            max_tokens=2500
        )

        parsed = self._attempt_json_repair(raw_output)
        if parsed is not None and isinstance(parsed, dict):
            return parsed

        logger.warning(f"First JSON parse failed. Raw: {raw_output[:120]}... Requesting repair...")
        # Self-correction fallback attempt
        repair_prompt = (
            f"Your previous response was malformed JSON:\n{raw_output}\n"
            f"Fix it and return strictly valid JSON matching this schema:\n{json.dumps(response_schema)}"
        )
        corrected_raw = await self.generate_text(
            prompt=repair_prompt,
            system_prompt="You are a strict JSON formatting corrector. Output raw JSON only.",
            temperature=0.1
        )
        repaired_parsed = self._attempt_json_repair(corrected_raw)
        if repaired_parsed is not None and isinstance(repaired_parsed, dict):
            return repaired_parsed

        raise ProviderError(f"Failed to produce valid JSON adhering to schema. Raw output: {raw_output}")

    async def check_health(self) -> ProviderHealth:
        """Perform real connection check to OpenRouter."""
        start_time = time.time()
        if not self.api_key:
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.NOT_CONFIGURED,
                is_zero_cost=self.is_zero_cost,
                is_paid=self.is_paid,
                error_message="OPENROUTER_API_KEY is not set."
            )

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/models"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
            latency = (time.time() - start_time) * 1000

            if resp.status_code == 200:
                return ProviderHealth(
                    provider_name=self.name,
                    provider_type=self.provider_type,
                    status=ProviderStatus.CONNECTED,
                    is_zero_cost=self.is_zero_cost,
                    is_paid=self.is_paid,
                    latency_ms=round(latency, 1),
                    details={"model": self.model}
                )
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.DEGRADED,
                is_zero_cost=self.is_zero_cost,
                is_paid=self.is_paid,
                latency_ms=round(latency, 1),
                error_message=f"Status code {resp.status_code}: {resp.text[:100]}"
            )
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.OFFLINE,
                is_zero_cost=self.is_zero_cost,
                is_paid=self.is_paid,
                error_message=str(e)
            )
