"""Real unit tests for Phase 6: OpenRouter AI Provider and Zero-Cost validation."""

import pytest
from unittest.mock import patch, AsyncMock

from backend.app.core.errors import ZeroCostModeViolationError, ProviderError
from backend.app.providers.ai.openrouter import OpenRouterProvider, KNOWN_FREE_MODELS
from backend.app.models.provider import ProviderStatus


def test_openrouter_zero_cost_model_detection():
    """Verify that models with :free tag and known free models are flagged zero-cost."""
    p_free1 = OpenRouterProvider(model="meta-llama/llama-3.3-70b-instruct:free")
    assert p_free1.is_zero_cost is True
    assert p_free1.is_paid is False

    p_free2 = OpenRouterProvider(model="openrouter/free")
    assert p_free2.is_zero_cost is True
    assert p_free2.is_paid is False

    p_paid1 = OpenRouterProvider(model="openai/gpt-4o")
    assert p_paid1.is_zero_cost is False
    assert p_paid1.is_paid is True

    p_paid2 = OpenRouterProvider(model="anthropic/claude-3.5-sonnet")
    assert p_paid2.is_zero_cost is False
    assert p_paid2.is_paid is True


@pytest.mark.anyio
async def test_zero_cost_mode_blocks_paid_openrouter_model():
    """Verify that calling a paid model while Zero-Cost Mode is active raises ZeroCostModeViolationError."""
    paid_provider = OpenRouterProvider(model="openai/gpt-4o")

    with patch("backend.app.config.settings.zero_cost_mode", True):
        with pytest.raises(ZeroCostModeViolationError) as exc_info:
            await paid_provider.generate_text("Explain quantum gravity in 5 seconds.")
        assert "Paid provider blocked by Zero-Cost Mode." in str(exc_info.value)


def test_json_markdown_cleaning_and_repair():
    """Verify JSON cleaning handles code blocks, preambles, and malformed syntax."""
    p = OpenRouterProvider(model="openrouter/free")

    # 1. Clean markdown fences
    raw_markdown = "Here is your script:\n```json\n{\"hook\": \"Stop scrolling!\", \"seconds\": 3}\n```\nHope you like it!"
    cleaned = p._clean_json_markdown(raw_markdown)
    assert cleaned == '{"hook": "Stop scrolling!", "seconds": 3}'

    # 2. Trailing commas repair
    malformed_trailing = '{"items": ["A", "B", ], "topic": "Tech", }'
    repaired = p._attempt_json_repair(malformed_trailing)
    assert repaired is not None
    assert repaired["items"] == ["A", "B"]
    assert repaired["topic"] == "Tech"

    # 3. Missing closing braces repair
    truncated_json = '{"hook": "Did you know this?", "details": {"score": 95'
    repaired_braces = p._attempt_json_repair(truncated_json)
    assert repaired_braces is not None
    assert repaired_braces["details"]["score"] == 95


@pytest.mark.anyio
async def test_generate_structured_json():
    """Verify generate_structured parses schema-compliant JSON response."""
    p = OpenRouterProvider(api_key="mock_key", model="meta-llama/llama-3.3-70b-instruct:free")

    mock_resp_content = '```json\n{"topic": "5 AI Tools", "hooks": ["Hook 1", "Hook 2"]}\n```'
    mock_http_resp = {
        "choices": [
            {"message": {"content": mock_resp_content}}
        ]
    }

    with patch("httpx.AsyncClient.post") as mock_post, \
         patch("backend.app.config.settings.zero_cost_mode", True):
        mock_post.return_value = AsyncMock(status_code=200, json=lambda: mock_http_resp)

        schema = {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "hooks": {"type": "array"}
            }
        }

        result = await p.generate_structured(
            prompt="Generate 2 hooks for 5 AI tools",
            response_schema=schema
        )

        assert result["topic"] == "5 AI Tools"
        assert len(result["hooks"]) == 2


@pytest.mark.anyio
async def test_openrouter_health_check_not_configured():
    """Verify check_health returns NOT_CONFIGURED when api_key is missing."""
    p = OpenRouterProvider(api_key="", model="openrouter/free")
    health = await p.check_health()
    assert health.status == ProviderStatus.NOT_CONFIGURED
    assert "OPENROUTER_API_KEY is not set" in health.error_message
