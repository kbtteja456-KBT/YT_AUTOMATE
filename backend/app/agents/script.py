"""ScriptAgent generating high-retention, strictly structured 30-60s narration."""

from typing import Any
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Script, ResearchReport


class ScriptAgent(BaseAgent):
    """Drafts viral spoken scripts tailored for high watch time and zero filler."""

    name = "ScriptAgent"

    async def generate_script(
        self,
        topic: str,
        hook: str,
        research: ResearchReport,
        target_duration_sec: float = 45.0
    ) -> Script:
        """Construct full narration script with explicit time-stamped retention sections."""
        self.log(f"Scripting narration for '{topic}' with target duration {target_duration_sec}s...")

        target_word_count = int(target_duration_sec * 2.8)  # ~2.8 words per second

        prompt = (
            f"Topic: '{topic}'.\n"
            f"Selected Hook (0-3s): '{hook}'.\n"
            f"Verified Research Facts:\n{[i.fact for i in research.items]}\n\n"
            f"Write a high-retention YouTube Shorts narration script targeting {target_duration_sec}s (~{target_word_count} words total).\n"
            f"Structure required:\n"
            f"1. 'hook': Use the selected hook verbatim.\n"
            f"2. 'problem': 3 to 8s (creates urgency or reveals friction).\n"
            f"3. 'value': 8 to 35s (rapid-fire actionable tools/walkthrough).\n"
            f"4. 'payoff': 35 to 42s (unexpected result or key secret).\n"
            f"5. 'cta': Final 3s (brief call to action, e.g. 'Save this before your next project').\n"
            f"Rules:\n"
            f"- Short, punchy conversational sentences.\n"
            f"- Zero filler intros ('Hey everyone', 'Welcome back', 'In today's video').\n"
            f"- Spoken English flow (easy to pronounce for TTS)."
        )

        schema = {
            "type": "object",
            "properties": {
                "hook": {"type": "string"},
                "problem": {"type": "string"},
                "value": {"type": "string"},
                "payoff": {"type": "string"},
                "cta": {"type": "string"}
            },
            "required": ["hook", "problem", "value", "payoff", "cta"]
        }

        response = await self.ai.generate_structured(
            prompt=prompt,
            response_schema=schema,
            system_prompt="You are an elite short-form scriptwriter. Keep sentences concise, punchy, and compelling."
        )

        hook_text = response.get("hook", hook).strip()
        problem_text = response.get("problem", "Most people do this the slow way.").strip()
        value_text = response.get("value", research.key_takeaway).strip()
        payoff_text = response.get("payoff", "This one shortcut changes everything.").strip()
        cta_text = response.get("cta", "Save this video so you don't forget.").strip()

        full_narration = f"{hook_text} {problem_text} {value_text} {payoff_text} {cta_text}"
        word_count = len(full_narration.split())

        script = Script(
            topic=topic,
            hook=hook_text,
            problem=problem_text,
            value=value_text,
            payoff=payoff_text,
            cta=cta_text,
            full_narration=full_narration,
            target_duration_sec=target_duration_sec,
            word_count=word_count
        )

        self.log(f"Script created: {word_count} words (~{word_count / 2.8:.1f}s spoken narration)")
        return script
