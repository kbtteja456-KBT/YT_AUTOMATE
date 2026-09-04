"""Real unit tests for Phases 8 & 9: Idea, Research, Hook, and Script agents."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.agents.idea import IdeaAgent
from backend.app.agents.research import ResearchAgent, FactCheckAgent
from backend.app.agents.hook import HookAgent
from backend.app.agents.script import ScriptAgent
from backend.app.models.video import ResearchReport, ResearchItem


@pytest.mark.anyio
async def test_idea_agent_similarity_and_deduplication():
    """Verify IdeaAgent selects original topics and rejects duplicates from history."""
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={
        "candidates": [
            {"topic": "5 AI Tools Students Need in 2026", "angle": "Productivity", "why_viral": "Fast hacks", "estimated_interest_score": 9.2},
            {"topic": "Quantum Computing Breakthrough Explained Simply", "angle": "Deep Tech", "why_viral": "Mind blowing", "estimated_interest_score": 8.8}
        ]
    })

    agent = IdeaAgent(ai_provider=mock_ai)

    # Past topics contain the exact first topic
    past = ["5 AI Tools Students Need in 2026", "Best Python Tips"]
    result = await agent.generate_daily_topic(
        niche="AI Tools",
        target_audience="Students",
        past_topics=past,
        slot_index=1
    )

    # Should have selected the second candidate because the first is an exact duplicate
    assert result["topic"] == "Quantum Computing Breakthrough Explained Simply"
    assert result["similarity_score"] < 0.60


@pytest.mark.anyio
async def test_research_and_fact_check_pipeline():
    """Verify ResearchAgent formats items and FactCheckAgent rejects unverified claims."""
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={
        "items": [
            {"fact": "Transformers utilize self-attention mechanisms to process sequence data.", "source": "Attention is All You Need paper (2017)", "interpretation": "Core foundation of LLMs."},
            {"fact": "AI will replace 100% of jobs tomorrow.", "source": "", "interpretation": "Unsupported claim."}
        ],
        "key_takeaway": "Self-attention powers modern generative AI."
    })

    researcher = ResearchAgent(ai_provider=mock_ai)
    report = await researcher.conduct_research("Transformer Architecture", "AI & ML")
    assert len(report.items) == 2

    # Fact check audit
    checker = FactCheckAgent(ai_provider=mock_ai)
    audited = await checker.verify_and_prune(report)

    # Second item had no source and was pruned
    assert len(audited.items) == 1
    assert "Transformers utilize self-attention" in audited.items[0].fact


@pytest.mark.anyio
async def test_hook_agent_generates_and_scores_5_hooks():
    """Verify HookAgent creates >= 5 hooks and calculates composite retention scores."""
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={
        "hooks": [
            {"text": "Stop scrolling right now or you'll miss this AI breakthrough.", "curiosity": 9.5, "clarity": 9.0, "specificity": 8.5, "emotional_impact": 8.8, "retention_potential": 9.6, "speed": 9.0},
            {"text": "Here are 5 tools you probably didn't know.", "curiosity": 7.0, "clarity": 8.0, "specificity": 7.5, "emotional_impact": 6.5, "retention_potential": 7.0, "speed": 8.0},
            {"text": "99% of students do their assignments completely wrong.", "curiosity": 9.2, "clarity": 9.0, "specificity": 8.8, "emotional_impact": 8.5, "retention_potential": 9.3, "speed": 9.2},
            {"text": "This secret software saves 10 hours a week.", "curiosity": 8.8, "clarity": 9.1, "specificity": 8.5, "emotional_impact": 8.0, "retention_potential": 8.9, "speed": 9.0},
            {"text": "If you write code, watch this before your next build.", "curiosity": 8.6, "clarity": 8.9, "specificity": 8.2, "emotional_impact": 8.1, "retention_potential": 8.7, "speed": 8.8}
        ]
    })

    hook_agent = HookAgent(ai_provider=mock_ai)
    hooks = await hook_agent.generate_and_score_hooks("5 AI Tools", "Save 10 hours a week")

    assert len(hooks) == 5
    # The first hook had the highest composite score and must be selected
    selected_hook = next(h for h in hooks if h.selected)
    assert selected_hook.total_score >= 9.0
    assert "Stop scrolling" in selected_hook.text


@pytest.mark.anyio
async def test_script_agent_structure_and_duration():
    """Verify ScriptAgent produces complete 5-stage retention script with proper word counts."""
    mock_ai = MagicMock()
    mock_ai.generate_structured = AsyncMock(return_value={
        "hook": "Stop scrolling right now.",
        "problem": "Writing essays and researching manually wastes hundreds of hours every semester.",
        "value": "Tool number one is Paper Digest, which summarizes 40 page research papers in bullet points. Tool two is Consensus, an AI search engine pulling findings exclusively from peer reviewed scientific papers.",
        "payoff": "Using these two in tandem lets you complete comprehensive literature reviews in twenty minutes instead of three days.",
        "cta": "Save this video for your upcoming finals."
    })

    script_agent = ScriptAgent(ai_provider=mock_ai)
    research_mock = ResearchReport(
        topic="5 AI Tools for Students",
        niche="Education",
        items=[ResearchItem(fact="Consensus searches 200M papers", source="Consensus.app", interpretation="Academic validation")],
        key_takeaway="Accelerate research with AI"
    )

    script = await script_agent.generate_script(
        topic="5 AI Tools for Students",
        hook="Stop scrolling right now.",
        research=research_mock,
        target_duration_sec=45.0
    )

    assert script.hook == "Stop scrolling right now."
    assert script.word_count > 40
    assert "Paper Digest" in script.full_narration
    assert "Save this video" in script.cta
