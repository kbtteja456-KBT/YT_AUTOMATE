"""ScriptAgent generating high-retention Python quiz and standard 20-45s scripts."""

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
        """Construct narration script with explicit time-stamped retention sections."""
        is_quiz = (getattr(research, "content_format", "general") == "quiz_card")
        eff_duration = 24.0 if is_quiz else target_duration_sec

        self.log(f"Scripting narration for '{topic}' (format: {'quiz_card' if is_quiz else 'general'}, {eff_duration}s)...")

        if is_quiz:
            # Deterministic, punchy structure for Python quiz Shorts
            hook_text = hook.strip() if hook else "Would you get this Python question right?"
            corr_opt = research.correct_option or "A"
            expl = research.explanation or "Python evaluates expressions step-by-step."

            prompt = (
                f"Topic: '{topic}'.\n"
                f"Hook: '{hook_text}'.\n"
                f"Python Code:\n{research.question_code}\n"
                f"Options: {research.options}\n"
                f"Correct Option: {corr_opt}\n"
                f"Explanation: {expl}\n\n"
                f"Write a 20-24 second quiz narration:\n"
                f"1. 'hook': 0-3s hook.\n"
                f"2. 'problem': 3-8s read code focus and prompt viewer to pause.\n"
                f"3. 'value': 8-15s remind viewer to think carefully before the reveal.\n"
                f"4. 'payoff': 15-20s state that correct answer is {corr_opt} with one-sentence explanation.\n"
                f"5. 'cta': 20-24s 'Comment your answer before you scroll, and follow for daily Python quizzes.'"
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

            try:
                resp = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
                hook_text = resp.get("hook", hook_text).strip()
                problem_text = resp.get("problem", "What will this code print? Pause now to think.").strip()
                value_text = resp.get("value", "Look closely at how the values are being updated.").strip()
                payoff_text = resp.get("payoff", f"The correct answer is {corr_opt}! {expl}").strip()
                cta_text = resp.get("cta", "Comment what you got and follow for daily Python quizzes!").strip()
            except Exception:
                problem_text = "What will this code print? Pause if you need a moment."
                value_text = "Watch out for common beginner misconceptions."
                payoff_text = f"The correct answer is {corr_opt}! {expl}"
                cta_text = "Comment your answer before you scroll and follow for daily quizzes!"

            full_narration = f"{hook_text} {problem_text} {value_text} {payoff_text} {cta_text}"
            script = Script(
                topic=topic,
                hook=hook_text,
                problem=problem_text,
                value=value_text,
                payoff=payoff_text,
                cta=cta_text,
                full_narration=full_narration,
                target_duration_sec=eff_duration,
                word_count=len(full_narration.split()),
                content_format="quiz_card",
                question_code=research.question_code,
                options=research.options,
                correct_option=research.correct_option,
                explanation=research.explanation,
                concept_tag=research.concept_tag,
                verified_output=research.verified_output
            )
            self.log(f"Quiz script finalized: {script.word_count} words (~{eff_duration}s)")
            return script

        # Standard general format fallback
        target_word_count = int(target_duration_sec * 2.8)
        prompt = (
            f"Topic: '{topic}'.\n"
            f"Selected Hook (0-3s): '{hook}'.\n"
            f"Verified Research Facts:\n{[i.fact for i in research.items]}\n\n"
            f"Write a high-retention YouTube Shorts narration script targeting {target_duration_sec}s (~{target_word_count} words total)."
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
        resp = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
        h = resp.get("hook", hook).strip()
        p = resp.get("problem", "Most people do this the slow way.").strip()
        v = resp.get("value", research.key_takeaway).strip()
        po = resp.get("payoff", "This shortcut changes everything.").strip()
        c = resp.get("cta", "Save this video so you don't forget.").strip()
        full = f"{h} {p} {v} {po} {c}"
        return Script(
            topic=topic,
            hook=h,
            problem=p,
            value=v,
            payoff=po,
            cta=c,
            full_narration=full,
            target_duration_sec=target_duration_sec,
            word_count=len(full.split()),
            content_format="general"
        )
