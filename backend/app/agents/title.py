"""TitleAgent and DescriptionAgent generating high-CTR metadata for Python quizzes and standard Shorts."""

from typing import Any
from backend.app.agents.base import BaseAgent
from backend.app.models.video import Script


class TitleAgent(BaseAgent):
    """Generates punchy, high-CTR titles and relevant viral hashtags."""

    name = "TitleAgent"

    async def generate_title_and_tags(self, script: Script) -> dict[str, Any]:
        """Generate optimized title (<60 characters) and tags."""
        is_quiz = (getattr(script, "content_format", "general") == "quiz_card")
        self.log(f"Generating title and hashtags for '{script.topic}' (format: {'quiz_card' if is_quiz else 'general'})...")

        if is_quiz:
            concept = getattr(script, "concept_tag", "python_quiz")
            clean_concept = concept.replace("_", " ").title()

            prompt = (
                f"Topic: '{script.topic}'.\n"
                f"Concept: '{clean_concept}'.\n"
                f"Question Code:\n{script.question_code}\n\n"
                f"Generate:\n"
                f"1. 'title': Short, curiosity-driven YouTube Short title under 60 chars (e.g. \"You'll get this Python question wrong 🐍\").\n"
                f"2. 'hashtags': Mix of broad (#python, #coding, #programming, #shorts) and specific (#pythonquiz, #codingchallenge, #{concept.replace('_', '')}).\n"
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

            title = f"You'll get this Python question wrong 🐍 #Shorts"
            hashtags = ["#python", "#coding", "#programming", "#shorts", "#pythonquiz", f"#{concept.replace('_', '')}"]
            tags = ["python", "python quiz", "coding challenge", "python tricks", clean_concept, "learn python", "shorts"]

            try:
                resp = await self.ai.generate_structured(prompt=prompt, response_schema=schema)
                title = resp.get("title", title).strip()
                if not title.endswith("#Shorts") and len(title) < 52:
                    title = f"{title} #Shorts"
                hashtags = resp.get("hashtags", hashtags)
                tags = resp.get("tags", tags)
            except Exception:
                pass

            self.log(f"Quiz Title generated: '{title}' ({len(title)} chars)")
            return {
                "title": title,
                "hashtags": hashtags,
                "tags": tags
            }

        # General format fallback
        prompt = (
            f"Topic: '{script.topic}'.\n"
            f"Narration Script:\n'{script.full_narration}'\n\n"
            f"Generate:\n"
            f"1. 'title': High-CTR YouTube Short title under 60 characters.\n"
            f"2. 'hashtags': 3 to 5 trending tags (e.g. #Shorts, #AI, #Tech).\n"
            f"3. 'tags': 5 to 8 search keyword tags."
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
        title = f"{script.topic} in 60 Seconds"
        hashtags = ["#Shorts", "#AI", "#Productivity"]
        tags = [script.topic, "AI", "Tech Tools", "Productivity"]
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
    """Generates clean, SEO-optimized YouTube descriptions."""

    name = "DescriptionAgent"

    async def generate_description(self, script: Script, title: str, hashtags: list[str]) -> str:
        """Construct full YouTube Shorts description with answers, explanation, and tags."""
        self.log(f"Generating description for '{title}'...")
        is_quiz = (getattr(script, "content_format", "general") == "quiz_card")
        tag_str = " ".join(hashtags) if hashtags else "#Shorts #Python #Coding"

        if is_quiz:
            opt_text = "\n".join(script.options) if script.options else ""
            description = (
                f"{title}\n\n"
                f"🧠 What will be the output of this Python code snippet?\n\n"
                f"```python\n{script.question_code or ''}\n```\n\n"
                f"{opt_text}\n\n"
                f"-----------------------------------------\n"
                f"✅ CORRECT ANSWER: Option {script.correct_option}\n"
                f"💡 EXPLANATION: {script.explanation}\n"
                f"-----------------------------------------\n\n"
                f"💬 Did you get it right? Comment your answer below!\n"
                f"🔔 Subscribe for daily Python quizzes and coding challenges!\n\n"
                f"{tag_str}"
            )
            return description

        # General format fallback
        description = (
            f"{title}\n\n"
            f"{script.value}\n\n"
            f"🔔 Follow for daily autonomous tech and AI discoveries.\n\n"
            f"{tag_str}"
        )
        return description
