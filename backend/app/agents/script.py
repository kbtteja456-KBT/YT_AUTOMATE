"""ScriptAgent generating high-retention Python quiz and standard 20-45s scripts."""

from typing import Any
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Script, ResearchReport
from backend.app.core.language_detector import detect_language_from_niche


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
        c_format = getattr(research, "content_format", "general")
        is_quiz = (c_format in ("quiz_card", "trivia_quiz"))
        is_quote = (c_format == "quote_card")
        eff_duration = 24.0 if (is_quiz or is_quote) else target_duration_sec

        lang_profile = detect_language_from_niche(research.niche)
        lang_name = lang_profile.display_name

        self.log(f"Scripting narration for '{topic}' (format: {c_format}, {eff_duration}s)...")

        # -------------------------------------------------------------
        # 1. QUOTE CARD FORMAT
        # -------------------------------------------------------------
        if is_quote:
            quote_str = research.quote_text or research.question_code or "Wisdom speaks quietly."
            author_str = research.quote_author or "Unknown"
            expl_str = research.explanation or "Master your mind and guard your time."
            hook_text = hook.strip() if hook else f"A quote from {author_str} that will change how you think."
            prob_text = f"\"{quote_str}\""
            val_text = f"Take a second to absorb that. {expl_str}"
            payoff_text = "Most people drift through life on autopilot. Choose intention instead."
            cta_text = "Double tap if you needed this reminder today, and subscribe for daily wisdom."
            full_narration = f"{hook_text} {prob_text} {val_text} {payoff_text} {cta_text}"
            return Script(
                topic=topic,
                hook=hook_text,
                problem=prob_text,
                value=val_text,
                payoff=payoff_text,
                cta=cta_text,
                full_narration=full_narration,
                target_duration_sec=eff_duration,
                word_count=len(full_narration.split()),
                content_format="quote_card",
                question_code=research.question_code,
                quote_text=quote_str,
                quote_author=author_str,
                options=[],
                correct_option="",
                explanation=expl_str,
                concept_tag=research.concept_tag,
                verified_output=author_str,
                language="quotes"
            )

        # -------------------------------------------------------------
        # 2. TRIVIA QUIZ FORMAT
        # -------------------------------------------------------------
        if c_format == "trivia_quiz":
            q_text = research.question_text or research.question_code or "Can you answer this?"
            corr_opt = research.correct_option or "A"
            expl = research.explanation or "Think carefully."
            hook_text = hook.strip() if hook else "Only 1 in 10 people get this question right!"
            prob_text = f"{q_text} Pause the video now to think!"
            val_text = "Watch out, the obvious answer might trick you."
            payoff_text = f"The correct answer is Option {corr_opt}! {expl}"
            cta_text = "Comment what you got and subscribe for daily trivia quizzes!"
            full_narration = f"{hook_text} {prob_text} {val_text} {payoff_text} {cta_text}"
            return Script(
                topic=topic,
                hook=hook_text,
                problem=prob_text,
                value=val_text,
                payoff=payoff_text,
                cta=cta_text,
                full_narration=full_narration,
                target_duration_sec=eff_duration,
                word_count=len(full_narration.split()),
                content_format="trivia_quiz",
                question_code=research.question_code,
                question_text=q_text,
                options=research.options,
                correct_option=corr_opt,
                explanation=expl,
                concept_tag=research.concept_tag,
                verified_output=corr_opt,
                language="trivia"
            )

        # -------------------------------------------------------------
        # 3. CODE QUIZ FORMAT (Python for Owner, Language for Tenants)
        # -------------------------------------------------------------
        if is_quiz:
            # Deterministic, punchy structure for quiz Shorts
            hook_text = hook.strip() if hook else f"Would you get this {lang_name} question right?"
            corr_opt = research.correct_option or "A"
            expl = research.explanation or f"{lang_name} evaluates expressions step-by-step."

            prompt = (
                f"Topic: '{topic}'.\n"
                f"Hook: '{hook_text}'.\n"
                f"{lang_name} Code:\n{research.question_code}\n"
                f"Options: {research.options}\n"
                f"Correct Option: {corr_opt}\n"
                f"Explanation: {expl}\n\n"
                f"Write a 20-24 second quiz narration:\n"
                f"1. 'hook': 0-3s hook.\n"
                f"2. 'problem': 3-8s read code focus and prompt viewer to pause.\n"
                f"3. 'value': 8-15s remind viewer to think carefully before the reveal.\n"
                f"4. 'payoff': 15-20s state that correct answer is {corr_opt} with one-sentence explanation.\n"
                f"5. 'cta': 20-24s 'Comment your answer before you scroll, and follow for daily {lang_name} quizzes.'"
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
                cta_text = resp.get("cta", f"Comment what you got and follow for daily {lang_name} quizzes!").strip()
            except Exception:
                problem_text = "What will this code print? Pause if you need a moment."
                value_text = "Watch out for common beginner misconceptions."
                payoff_text = f"The correct answer is {corr_opt}! {expl}"
                cta_text = f"Comment your answer before you scroll and follow for daily {lang_name} quizzes!"

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
                correct_option=corr_opt,
                explanation=expl,
                concept_tag=research.concept_tag,
                verified_output=research.verified_output,
                language=lang_profile.slug
            )
            self.log(f"Quiz script finalized: {script.word_count} words (~{eff_duration}s)")
            return script

        # -------------------------------------------------------------
        # 4. DOCUMENTARY / TECH NEWS FORMAT
        # -------------------------------------------------------------
        if c_format in ("documentary", "documentary_cinematic"):
            eff_duration = target_duration_sec or 45.0
            target_word_count = int(eff_duration * 2.6)
            hook_hint = hook.strip() if hook else f"Here is what you need to know about {topic}."
            facts_list = [i.fact for i in research.items] if research.items else [research.key_takeaway or topic]
            facts_str = "\n".join(f"- {f}" for f in facts_list)

            prompt = (
                f"Topic: '{topic}'.\n"
                f"Opening Hook: '{hook_hint}'.\n"
                f"Core Facts/Points:\n{facts_str}\n\n"
                f"Target duration: ~{eff_duration}s (~{target_word_count} spoken words).\n"
                f"Tone: Fast-paced, punchy, engaging science & tech journalism with zero filler.\n"
                f"Write high-retention narration split into 5 sections:\n"
                f"1. 'hook': 0-3s bold opener that immediately grabs attention.\n"
                f"2. 'problem': 3-10s setup introducing the breakthrough or news event.\n"
                f"3. 'value': 10-25s the core details and why this matters.\n"
                f"4. 'payoff': 25-38s the surprising insight or future implication.\n"
                f"5. 'cta': 38-45s punchy call-to-action asking viewers to comment and subscribe."
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
                h = resp.get("hook", hook_hint).strip()
                p = resp.get("problem", "The tech world just reached a massive milestone.").strip()
                v = resp.get("value", research.key_takeaway or facts_list[0]).strip()
                po = resp.get("payoff", "This fundamentally shifts how we interact with technology.").strip()
                c = resp.get("cta", "What do you think about this breakthrough? Let me know in the comments and subscribe!").strip()
            except Exception:
                import re
                clean_t = re.sub(r'#\w+', '', topic).strip()
                h = hook_hint or f"Here is what just happened with {clean_t}."
                p = f"Researchers and builders just reached a massive milestone in {clean_t}."
                v = research.key_takeaway or (facts_list[0] if facts_list else clean_t)
                po = "This fundamentally accelerates real-world capability and changes what is possible this decade."
                c = "What are your thoughts on this? Comment below and subscribe for more updates!"

            full_narration = f"{h} {p} {v} {po} {c}"
            return Script(
                topic=topic,
                hook=h,
                problem=p,
                value=v,
                payoff=po,
                cta=c,
                full_narration=full_narration,
                target_duration_sec=eff_duration,
                word_count=len(full_narration.split()),
                content_format="documentary",
                concept_tag=research.concept_tag or "tech_news",
                language="tech_documentary",
                visual_keywords=getattr(research, "visual_keywords", [])
            )

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
