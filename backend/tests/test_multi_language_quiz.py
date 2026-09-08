"""Tests for multi-language dynamic quiz support (C, C++, Java, JS, Python) for tenant workspaces."""

import pytest
from pathlib import Path
from PIL import Image

from backend.app.core.language_detector import detect_language_from_niche
from backend.app.models.video import ResearchReport, Script, Storyboard, VisualType
from backend.app.renderers.quiz_card import QuizCardRenderer
from backend.app.agents.idea import IdeaAgent, C_QUIZ_POOL, PYTHON_QUIZ_POOL
from backend.app.agents.research import FactCheckAgent
from backend.app.agents.script import ScriptAgent
from backend.app.agents.title import TitleAgent, DescriptionAgent
from backend.app.agents.storyboard import StoryboardAgent
from backend.app.agents.media import MediaAgent
from backend.app.providers.storage.local_storage import LocalStorageProvider


class DummyAI:
    def __init__(self, responses: dict | None = None):
        self.responses = responses or {}

    async def generate_structured(self, **kwargs):
        return self.responses.get("structured", {})

    async def generate_text(self, **kwargs):
        return self.responses.get("text", "")


def test_language_detection():
    """Verify detect_language_from_niche resolves niches to correct language profiles."""
    assert detect_language_from_niche("c program puzzles").slug == "c"
    assert detect_language_from_niche("C Programming").slug == "c"
    assert detect_language_from_niche("C++ Tips & Tricks").slug == "cpp"
    assert detect_language_from_niche("Java Interview Puzzles").slug == "java"
    assert detect_language_from_niche("JavaScript Hacks").slug == "javascript"
    assert detect_language_from_niche("Go Concurrency").slug == "go"
    assert detect_language_from_niche("Rust Memory Safety").slug == "rust"

    # Default / owner preserves python
    assert detect_language_from_niche("Python Programming").slug == "python"
    assert detect_language_from_niche("").slug == "python"
    assert detect_language_from_niche(None).slug == "python"
    assert detect_language_from_niche("General Coding").slug == "python"


@pytest.mark.anyio
async def test_idea_agent_c_programming_quiz():
    """Verify IdeaAgent selects C quiz pool and prompts when niche is 'c program puzzles'."""
    ai = DummyAI()
    agent = IdeaAgent(ai_provider=ai)

    # Empty AI fallback must pick from C_QUIZ_POOL, not PYTHON_QUIZ_POOL
    topic = await agent.generate_daily_topic(niche="c program puzzles")
    assert topic["content_format"] == "quiz_card"
    assert topic["topic"].startswith("C Quiz:")
    assert any(c["question_code"] == topic["question_code"] for c in C_QUIZ_POOL)
    assert "#include" in topic["question_code"] or "printf" in topic["question_code"]


@pytest.mark.anyio
async def test_fact_check_c_programming():
    """Verify FactCheckAgent handles C programming verification with compiler or LLM logic check."""
    ai = DummyAI(responses={
        "structured": {
            "exact_terminal_output": "6",
            "correct_option_letter": "B",
            "explanation": "arr[1] is 2, ptr + 2 points to arr[2] which is 3. 2 * 3 = 6."
        }
    })
    agent = FactCheckAgent(ai_provider=ai)

    c_report = ResearchReport(
        topic="C Quiz: Pointer Arithmetic",
        niche="c program puzzles",
        language="c",
        content_format="quiz_card",
        question_code="int a = 5;\nprintf(\"%d\", a++);",
        options=["A) 5", "B) 6", "C) Garbage", "D) Error"],
        correct_option="A",
        explanation="Postfix increment returns the value before incrementing."
    )

    verified = await agent.verify_and_prune(c_report)
    assert verified.verified_output == "6"
    assert verified.correct_option == "B"
    assert verified.language == "c"


@pytest.mark.anyio
async def test_script_and_title_agents_c_quiz():
    """Verify ScriptAgent and TitleAgent dynamically emit C hashtags and title structures."""
    ai = DummyAI()
    script_agent = ScriptAgent(ai_provider=ai)

    report = ResearchReport(
        topic="C Quiz: Pointer Math",
        niche="c program puzzles",
        language="c",
        content_format="quiz_card",
        question_code="int x = 10;\nprintf(\"%d\", x);",
        options=["A) 10", "B) 0", "C) Trash", "D) Error"],
        correct_option="A",
        explanation="x is initialized to 10."
    )

    script = await script_agent.generate_script(topic=report.topic, hook="", research=report)
    assert script.language == "c"
    assert "C" in script.hook
    assert "C" in script.cta

    title_agent = TitleAgent(ai_provider=ai)
    title_res = await title_agent.generate_title_and_tags(script)
    assert any(tag in [t.lower() for t in title_res["hashtags"]] for tag in ["#cprogramming", "#cquiz", "#clanguage"])
    assert "C" in title_res["title"]

    desc_agent = DescriptionAgent()
    desc = await desc_agent.generate_description(script, title=title_res["title"], hashtags=title_res["hashtags"])
    assert "```c" in desc
    assert "daily C quizzes" in desc


def test_quiz_card_renderer_c_language(tmp_path):
    """Verify QuizCardRenderer renders 'C PROGRAMMING QUIZ' and 'main.c' on the card."""
    q_path, r_path = QuizCardRenderer.render_quiz_cards(
        question_code='#include <stdio.h>\nint main() {\n    printf("C Quiz");\n    return 0;\n}',
        options=["A) C Quiz", "B) 0", "C) None", "D) Error"],
        correct_option="A",
        explanation="printf outputs formatted string to stdout.",
        output_dir=str(tmp_path),
        job_id="test_c_quiz_card",
        language="c"
    )

    assert Path(q_path).exists()
    assert Path(r_path).exists()

    img_q = Image.open(q_path)
    assert img_q.size == (1080, 1920)
    assert img_q.mode == "RGB"
