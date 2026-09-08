"""Tests verifying custom niches (Trivia, Riddles, Quotes) and strict BYOK trial quota enforcement."""

import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import MagicMock, patch

from backend.app.core.language_detector import detect_content_archetype, detect_language_from_niche
from backend.app.models.video import ResearchReport, Script
from backend.app.renderers.quiz_card import QuizCardRenderer
from backend.app.agents.idea import IdeaAgent, TRIVIA_QUIZ_POOL, QUOTE_POOL
from backend.app.agents.research import FactCheckAgent
from backend.app.agents.script import ScriptAgent
from backend.app.agents.title import TitleAgent, DescriptionAgent
from backend.app.celery_app.tasks import _build_orchestrator, _get_authenticated_youtube_provider
from backend.app.core.errors import AutopilotError


class DummyAI:
    def __init__(self, responses: dict | None = None):
        self.responses = responses or {}

    async def generate_structured(self, **kwargs):
        return self.responses.get("structured", {})

    async def generate_text(self, **kwargs):
        return self.responses.get("text", "")


def test_niche_archetype_classification():
    """Verify that detect_content_archetype correctly segments diverse niches."""
    # 1. Quotes / Stoicism / Motivation
    assert detect_content_archetype("Stoic Quotes").archetype == "quote_card"
    assert detect_content_archetype("motivational quotes").archetype == "quote_card"
    assert detect_content_archetype("Daily Wisdom & Philosophy").archetype == "quote_card"

    # 2. Trivia / Riddles / GK
    assert detect_content_archetype("General Knowledge Quiz").archetype == "trivia_quiz"
    assert detect_content_archetype("brain teaser riddles").archetype == "trivia_quiz"
    assert detect_content_archetype("Science Trivia").archetype == "trivia_quiz"
    assert detect_content_archetype("movie quiz").archetype == "trivia_quiz"

    # 3. Coding (C, Python, Java, etc.)
    assert detect_content_archetype("c program puzzles").archetype == "code_quiz"
    assert detect_content_archetype("Java Interview Questions").archetype == "code_quiz"
    assert detect_content_archetype("Python Programming").archetype == "code_quiz"

    # 4. Default / Owner preserves code_quiz with python
    assert detect_content_archetype(None).archetype == "code_quiz"
    assert detect_content_archetype("").archetype == "code_quiz"


@pytest.mark.anyio
async def test_idea_agent_trivia_and_quotes():
    """Verify IdeaAgent produces trivia and quotes concepts based on user niche."""
    ai = DummyAI()
    agent = IdeaAgent(ai_provider=ai)

    # Trivia quiz
    trivia_topic = await agent.generate_daily_topic(niche="General Knowledge Quiz")
    assert trivia_topic["content_format"] == "trivia_quiz"
    assert any(q["question_code"] == trivia_topic["question_code"] for q in TRIVIA_QUIZ_POOL)
    assert len(trivia_topic["options"]) == 4

    # Quote card
    quote_topic = await agent.generate_daily_topic(niche="Stoic Quotes")
    assert quote_topic["content_format"] == "quote_card"
    assert any(q["quote_text"] == quote_topic["quote_text"] for q in QUOTE_POOL)
    assert quote_topic["quote_author"] != ""


@pytest.mark.anyio
async def test_script_and_title_agents_trivia_and_quotes():
    """Verify ScriptAgent and TitleAgent generate proper formats for trivia and quotes."""
    ai = DummyAI()
    script_agent = ScriptAgent(ai_provider=ai)
    title_agent = TitleAgent(ai_provider=ai)
    desc_agent = DescriptionAgent()

    # 1. Trivia Quiz Script & Title
    trivia_report = ResearchReport(
        topic="Trivia Quiz: Strongest Muscle",
        niche="Science Trivia",
        content_format="trivia_quiz",
        question_text="Which is the strongest muscle in the human body?",
        options=["A) Biceps", "B) Jaw", "C) Heart", "D) Glutes"],
        correct_option="B",
        explanation="The masseter jaw muscle exerts up to 200 lbs of force."
    )
    t_script = await script_agent.generate_script(topic=trivia_report.topic, hook="", research=trivia_report)
    assert t_script.content_format == "trivia_quiz"
    assert "trivia quizzes" in t_script.cta.lower() or "subscribe" in t_script.cta.lower()

    t_meta = await title_agent.generate_title_and_tags(t_script)
    assert any("#trivia" in h.lower() for h in t_meta["hashtags"])
    t_desc = await desc_agent.generate_description(t_script, title=t_meta["title"], hashtags=t_meta["hashtags"])
    assert "QUESTION:" in t_desc
    assert "CORRECT ANSWER:" in t_desc

    # 2. Quote Card Script & Title
    quote_report = ResearchReport(
        topic="Stoic Wisdom: Marcus Aurelius",
        niche="Stoic Quotes",
        content_format="quote_card",
        quote_text="You have power over your mind - not outside events.",
        quote_author="Marcus Aurelius",
        explanation="Master your reaction to become unstoppable."
    )
    q_script = await script_agent.generate_script(topic=quote_report.topic, hook="", research=quote_report)
    assert q_script.content_format == "quote_card"
    assert "Marcus Aurelius" in q_script.hook or "Marcus Aurelius" in q_script.problem

    q_meta = await title_agent.generate_title_and_tags(q_script)
    assert any("#quotes" in h.lower() or "#wisdom" in h.lower() for h in q_meta["hashtags"])
    q_desc = await desc_agent.generate_description(q_script, title=q_meta["title"], hashtags=q_meta["hashtags"])
    assert "Marcus Aurelius" in q_desc
    assert "REFLECTION:" in q_desc


def test_trivia_and_quote_card_rendering(tmp_path):
    """Verify QuizCardRenderer produces valid 1080x1920 PNG cards for trivia and quotes."""
    # 1. Trivia Cards
    t_q, t_r = QuizCardRenderer.render_trivia_cards(
        question_text="Which planet in our solar system has the most moons?",
        options=["A) Jupiter", "B) Saturn", "C) Uranus", "D) Neptune"],
        correct_option="B",
        explanation="Saturn has 146 confirmed moons, overtaking Jupiter.",
        output_dir=str(tmp_path),
        job_id="test_trivia"
    )
    assert Path(t_q).exists()
    assert Path(t_r).exists()
    img_t = Image.open(t_q)
    assert img_t.size == (1080, 1920)

    # 2. Quote Cards
    q_q, q_r = QuizCardRenderer.render_quote_cards(
        quote_text="The only way to do great work is to love what you do.",
        author="Steve Jobs",
        explanation="When your work aligns with purpose, greatness follows.",
        output_dir=str(tmp_path),
        job_id="test_quote"
    )
    assert Path(q_q).exists()
    assert Path(q_r).exists()
    img_q = Image.open(q_q)
    assert img_q.size == (1080, 1920)


def test_strict_byok_enforcement_after_three_videos():
    """Verify that tenant with 3+ videos generated CANNOT use owner key and MUST have BYOK."""
    mock_db = MagicMock()

    # Case 1: Tenant has 3 videos generated and NO BYOK key
    tenant_ws = {
        "_id": "6a9fd659f2e1cbccfc7a8e84",
        "is_legacy_default": False,
        "trial_quota": {"videos_generated": 3, "max_videos": 3, "is_exhausted": True}
    }
    mock_db.workspaces.find_one.return_value = tenant_ws
    mock_db.workspace_api_keys.find_one.return_value = None  # No BYOK key!

    with pytest.raises(AutopilotError) as exc_info:
        _build_orchestrator(db=mock_db, workspace_id="6a9fd659f2e1cbccfc7a8e84")
    assert "Free trial quota exhausted" in str(exc_info.value)
    assert "Vault" in str(exc_info.value)

    # Case 2: Tenant with valid BYOK key succeeds
    mock_db.workspace_api_keys.find_one.return_value = {
        "workspace_id": "6a9fd659f2e1cbccfc7a8e84",
        "provider": "openrouter",
        "is_valid": True,
        "encrypted_key": "encrypted_dummy_token"
    }
    with patch("backend.app.core.security.decrypt_token", return_value="sk-or-v1-tenant-custom-key"):
        orch = _build_orchestrator(db=mock_db, workspace_id="6a9fd659f2e1cbccfc7a8e84")
        assert orch is not None

    # Case 3: Owner workspace is unaffected and uses default platform key
    owner_ws = {
        "_id": "legacy_owner_ws",
        "is_legacy_default": True,
        "trial_quota": {"videos_generated": 100, "max_videos": 999999}
    }
    mock_db.workspaces.find_one.return_value = owner_ws
    mock_db.workspace_api_keys.find_one.return_value = None
    orch_owner = _build_orchestrator(db=mock_db, workspace_id="legacy_owner_ws")
    assert orch_owner is not None


def test_youtube_channel_isolation():
    """Verify that tenant workspace never falls back to owner's YouTube channel."""
    mock_db = MagicMock()

    # Tenant has no connected channel
    mock_db.youtube_channels.find_one.return_value = None

    client = _get_authenticated_youtube_provider(db=mock_db, workspace_id="tenant_no_channel")
    # Must NOT have credentials (cannot publish to owner channel)
    assert client.credentials is None
