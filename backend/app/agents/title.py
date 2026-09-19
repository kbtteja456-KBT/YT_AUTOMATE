"""TitleAgent and DescriptionAgent generating high-CTR metadata for Python quizzes and standard Shorts."""

import re
from typing import Any, Optional
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Script
from backend.app.core.language_detector import detect_language_from_niche


def format_viral_title(base_title: str, hashtags: list[str], max_len: int = 95) -> str:
    """Format a high-CTR YouTube Short title with curiosity hook and viral hashtags.

    Rules:
    1. Strip existing hashtags from base_title to get a clean hook.
    2. Must include '#Shorts' and '#viral'.
    3. Include 1-2 top relevant niche hashtags from `hashtags`.
    4. Never exceed `max_len` (defaults to 95 characters, safely below YouTube's 100 limit).
    """
    clean_hook = re.sub(r'#\w+', '', base_title).strip()
    clean_hook = re.sub(r'\s+[-–—|:]\s*$', '', clean_hook).strip()
    if not clean_hook:
        clean_hook = "Watch This Coding Puzzle 💻"

    # Truncate clean hook if it is too long to fit viral hashtags
    if len(clean_hook) > 55:
        cut = clean_hook[:52].rsplit(' ', 1)[0]
        clean_hook = (cut or clean_hook[:52]).strip()

    # Build prioritized hashtags list: #Shorts and #viral are mandatory
    priority_tags = ["#Shorts", "#viral"]
    seen = {t.lower() for t in priority_tags}

    if hashtags:
        for tag in hashtags:
            clean_tag = tag.strip()
            if not clean_tag.startswith("#"):
                clean_tag = f"#{clean_tag}"
            if clean_tag.lower() not in seen and len(clean_tag) > 2:
                priority_tags.append(clean_tag)
                seen.add(clean_tag.lower())

    current_title = clean_hook
    for tag in priority_tags:
        candidate = f"{current_title} {tag}"
        if len(candidate) <= max_len:
            current_title = candidate
        else:
            break

    # If #Shorts somehow didn't fit, force it at the end
    if "#shorts" not in current_title.lower():
        avail = max_len - 8
        current_title = f"{current_title[:avail].strip()} #Shorts"

    return current_title


class TitleAgent(BaseAgent):
    """Generates viral, curiosity-inducing titles, tags, and hashtags."""

    name = "TitleAgent"

    async def generate_title_and_tags(self, script: Script) -> dict[str, Any]:
        """Produce high-CTR title under 60 chars and optimized hashtag mix."""
        c_format = getattr(script, "content_format", "general")
        self.log(f"Generating title and hashtags for '{script.topic}' (format: {c_format})...")

        # -------------------------------------------------------------
        # 1. QUOTE CARD FORMAT
        # -------------------------------------------------------------
        if c_format == "quote_card":
            author = script.quote_author or "Wisdom"
            hashtags = ["#quotes", "#motivation", "#wisdom", "#stoicism", "#shorts"]
            tags = ["quotes", "motivation", "wisdom", "stoic", author.lower(), "life lessons", "shorts"]
            title = format_viral_title(f"{author} On How To Live 🧠", hashtags)
            return {
                "title": title,
                "hashtags": hashtags,
                "tags": tags
            }

        # -------------------------------------------------------------
        # 2. TRIVIA QUIZ FORMAT
        # -------------------------------------------------------------
        if c_format == "trivia_quiz":
            hashtags = ["#trivia", "#quiz", "#generalknowledge", "#riddles", "#shorts"]
            tags = ["trivia", "quiz", "general knowledge", "brain teaser", "riddles", "shorts"]
            title = "Only 1% Can Answer This Question 🧠"
            prompt = (
                f"Topic: '{script.topic}'.\n"
                f"Question: {script.question_text or script.question_code}\n\n"
                f"Generate:\n"
                f"1. 'title': Catchy trivia YouTube Short title under 60 chars ending in #Shorts.\n"
                f"2. 'hashtags': 5 viral trivia hashtags (e.g. #trivia #quiz #gk #shorts).\n"
                f"3. 'tags': 6 to 10 search tags."
            )
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["title", "hashtags", "tags"]
            }
            try:
                resp = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
                title = resp.get("title", title).strip()
                hashtags = resp.get("hashtags", hashtags)
                tags = resp.get("tags", tags)
            except Exception:
                pass

            title = format_viral_title(title, hashtags)
            return {"title": title, "hashtags": hashtags, "tags": tags}

        # -------------------------------------------------------------
        # 3. CODE QUIZ FORMAT (Python for Owner, Language for Tenants)
        # -------------------------------------------------------------
        is_quiz = (c_format in ("quiz_card", "code_quiz")) or bool(getattr(script, "question_code", None))
        if is_quiz:
            lang_profile = detect_language_from_niche(getattr(script, "language", None) or script.topic)
            is_python = (lang_profile.slug == "python")
            lang_name = lang_profile.display_name

            concept = getattr(script, "concept_tag", None) or f"{lang_profile.slug}_quiz"
            clean_concept = concept.replace("_", " ").title()

            prompt_example = "You'll get this Python question wrong 🐍" if is_python else f"You'll get this {lang_name} question wrong 💻"
            prompt = (
                f"Topic: '{script.topic}'.\n"
                f"Language: '{lang_name}'.\n"
                f"Concept: '{clean_concept}'.\n"
                f"Question Code:\n{script.question_code}\n\n"
                f"Generate:\n"
                f"1. 'title': Short, curiosity-driven YouTube Short title under 60 chars (e.g. \"{prompt_example}\" or \"{lang_name} Quiz: {clean_concept} #Shorts\").\n"
                f"2. 'hashtags': Mix of broad ({lang_profile.default_hashtag}, #coding, #programming, #shorts) and specific (#{lang_profile.slug}quiz, #codingchallenge, #{concept.replace('_', '')}).\n"
                f"3. 'tags': 6 to 10 search keyword tags."
            )
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["title", "hashtags", "tags"]
            }

            if is_python:
                title = f"Python Quiz: {clean_concept} 🐍" if len(f"Python Quiz: {clean_concept} 🐍") <= 50 else "You'll get this Python question wrong 🐍"
                hashtags = ["#python", "#coding", "#programming", "#shorts", "#pythonquiz", f"#{concept.replace('_', '')}"]
                tags = ["python", "python quiz", "coding challenge", "python tricks", clean_concept, "learn python", "shorts"]
            else:
                title = f"You'll get this {lang_name} question wrong 💻"
                hashtags = [lang_profile.default_hashtag, "#coding", "#programming", "#shorts", f"#{lang_profile.slug}quiz", f"#{concept.replace('_', '')}"]
                tags = [lang_profile.slug, f"{lang_profile.slug} programming", f"{lang_profile.slug} quiz", "coding challenge", clean_concept, "shorts"]

            try:
                resp = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
                cand_title = resp.get("title", "").strip()
                if cand_title:
                    # Enforce language name in title for unmistakable branding
                    if lang_profile.slug in cand_title.lower() or lang_name.lower() in cand_title.lower():
                        title = cand_title
                    else:
                        title = f"{lang_name} Quiz: {cand_title}"
                hashtags = resp.get("hashtags", hashtags)
                tags = resp.get("tags", tags)
            except Exception:
                pass

            title = format_viral_title(title, hashtags)
            self.log(f"Quiz Title generated: '{title}' ({len(title)} chars)")
            return {
                "title": title,
                "hashtags": hashtags,
                "tags": tags
            }

        # General format fallback
        target_audience = "curious tech learners"
        prompt = (
            f"Topic: '{script.topic}'.\n"
            f"Key Takeaway: '{script.payoff}'.\n"
            f"Target Audience: {target_audience}.\n\n"
            f"Generate a high-converting YouTube Short metadata package:\n"
            f"1. 'title': Punchy, curiosity-driven title under 60 characters with high emotional appeal.\n"
            f"2. 'hashtags': 3 to 5 viral, broad hashtags (must include #Shorts).\n"
            f"3. 'tags': 5 to 8 search tags."
        )
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["title", "hashtags", "tags"]
        }
        import re
        clean_top = re.sub(r'#\w+', '', script.topic).strip()
        title = f"{clean_top} in 60 Seconds #Shorts" if len(clean_top) < 45 else f"{clean_top} #Shorts"
        clean_words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in clean_top.split() if len(w) > 3]
        topic_tags = [w for w in clean_words if w.lower() not in {"shorts", "about", "with", "this", "that", "from", "into"}][:4]
        hashtags = ["#Shorts"] + [f"#{t.capitalize()}" for t in topic_tags[:3]]
        tags = [clean_top] + topic_tags + ["Trending", "Discovery"]
        try:
            resp = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
            title = resp.get("title", title).strip()
            hashtags = resp.get("hashtags", hashtags)
            tags = resp.get("tags", tags)
        except Exception:
            pass

        return {
            "title": title,
            "hashtags": hashtags,
            "tags": tags
        }


class DescriptionAgent(BaseAgent):
    """Generates clean, SEO-optimized YouTube descriptions.

    When a CC BY (attribution-required) music track is used, the credit line
    MUST appear in the real YouTube description — not just in internal metadata.
    Pass the credit text via music_attribution; only CC0 tracks may pass None.
    """

    name = "DescriptionAgent"

    async def generate_description(
        self,
        script: Script,
        title: str,
        hashtags: list[str],
        music_attribution: Optional[str] = None,
    ) -> str:
        """Construct full YouTube Shorts description with answers, explanation, and tags.

        Args:
            music_attribution: The CC BY credit line from VoiceAgent.last_music_attribution,
                               or None for CC0/public-domain/TTS-narrated videos.
                               When non-None, this credit block is appended to the description
                               BEFORE the hashtags so it appears in the actual published video.
        """
        self.log(f"Generating description for '{title}'...")
        c_format = getattr(script, "content_format", "general")
        is_quiz = (c_format in ("quiz_card", "trivia_quiz"))
        is_quote = (c_format == "quote_card")
        tag_str = " ".join(hashtags) if hashtags else "#Shorts #Trending"

        # Build the music credit block (only for CC BY tracks)
        music_credit_block = ""
        if music_attribution:
            music_credit_block = f"\n-----------------------------------------\n🎵 MUSIC CREDIT\n{music_attribution}\n-----------------------------------------\n"

        if is_quote:
            quote_text = script.quote_text or script.question_code or ""
            author = script.quote_author or "Wisdom"
            description = (
                f"{title}\n\n"
                f"“{quote_text}”\n"
                f"— {author}\n\n"
                f"-----------------------------------------\n"
                f"💡 REFLECTION:\n{script.explanation}\n"
                f"-----------------------------------------\n\n"
                f"💬 Did you need to hear this today? Comment your thoughts below!\n"
                f"🔔 Subscribe for daily life wisdom and inspiration!\n"
                f"{music_credit_block}\n"
                f"{tag_str}"
            )

        elif c_format == "trivia_quiz":
            opt_text = "\n".join(script.options) if script.options else ""
            description = (
                f"{title}\n\n"
                f"❓ QUESTION:\n{script.question_text or script.question_code or ''}\n\n"
                f"{opt_text}\n\n"
                f"-----------------------------------------\n"
                f"✅ CORRECT ANSWER: Option {script.correct_option}\n"
                f"💡 EXPLANATION: {script.explanation}\n"
                f"-----------------------------------------\n\n"
                f"💬 Did you get it right? Comment your answer below!\n"
                f"🔔 Subscribe for daily trivia quizzes and brain teasers!\n"
                f"{music_credit_block}\n"
                f"{tag_str}"
            )

        elif is_quiz:
            lang_profile = detect_language_from_niche(getattr(script, "language", None) or getattr(script, "niche", None) or title)
            lang_name = lang_profile.display_name
            opt_text = "\n".join(script.options) if script.options else ""
            description = (
                f"{title}\n\n"
                f"🧠 What will be the output of this {lang_name} code snippet?\n\n"
                f"```{lang_profile.code_fence}\n{script.question_code or ''}\n```\n\n"
                f"{opt_text}\n\n"
                f"-----------------------------------------\n"
                f"✅ CORRECT ANSWER: Option {script.correct_option}\n"
                f"💡 EXPLANATION: {script.explanation}\n"
                f"-----------------------------------------\n\n"
                f"💬 Did you get it right? Comment your answer below!\n"
                f"🔔 Subscribe for daily {lang_name} quizzes and coding challenges!\n"
                f"{music_credit_block}\n"
                f"{tag_str}"
            )

        else:
            # General format fallback
            description = (
                f"{title}\n\n"
                f"{script.value}\n\n"
                f"🔔 Follow for daily discoveries and insights.\n"
                f"{music_credit_block}\n"
                f"{tag_str}"
            )

        # YouTube Data API strictly forbids '<' and '>' in descriptions
        return description.replace("<", "[").replace(">", "]")[:5000]

