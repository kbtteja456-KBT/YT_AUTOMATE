"""Comprehensive regression and unit tests for Python Quiz Shorts content pivot."""

import pytest
from pathlib import Path
from PIL import Image

from backend.app.models.video import (
    ResearchReport, Script, Storyboard, Scene, VisualType, QCReport
)
from backend.app.renderers.quiz_card import QuizCardRenderer
from backend.app.agents.idea import IdeaAgent, PYTHON_QUIZ_POOL
from backend.app.agents.research import ResearchAgent, FactCheckAgent, CodeSandboxSecurityError
from backend.app.agents.script import ScriptAgent
from backend.app.agents.storyboard import StoryboardAgent
from backend.app.agents.media import MediaAgent
from backend.app.agents.voice import VoiceAgent
from backend.app.agents.caption import CaptionAgent
from backend.app.agents.title import TitleAgent, DescriptionAgent
from backend.app.agents.qc import QCAgent
from backend.app.providers.storage.local_storage import LocalStorageProvider
from backend.app.config import settings
from backend.app.core.errors import AutopilotError


class DummyAI:
    async def generate_structured(self, **kwargs):
        return {}
    async def generate_text(self, **kwargs):
        return ""


@pytest.mark.anyio
async def test_fact_check_sandboxed_subprocess_execution():
    """Verify that FactCheckAgent uses real subprocess execution without in-process exec/eval."""
    agent = FactCheckAgent(ai_provider=DummyAI())

    # 1. Valid code snippet execution
    code = "a = [1, 2]\nb = a\nb.append(3)\nprint(a)"
    rc, stdout, stderr, dur = agent.execute_snippet_sandboxed(code)
    assert rc == 0
    assert stdout == "[1, 2, 3]"
    assert dur < 3.0

    # 2. Match real stdout to option
    options = ["A) [1, 2]", "B) [1, 2, 3]", "C) [3]", "D) Error"]
    matched = agent._match_stdout_to_option(stdout, options)
    assert matched == "B"

    # 3. Complete verify_and_prune flow
    report = ResearchReport(
        topic="Python Quiz: List Mutation #Shorts",
        niche="Python",
        content_format="quiz_card",
        question_code=code,
        options=options,
        correct_option="A",  # Deliberately wrong initial claim
        explanation="Lists in Python are mutable references."
    )
    verified = await agent.verify_and_prune(report)
    assert verified.verified_output == "[1, 2, 3]"
    assert verified.correct_option == "B"  # Overwritten with verified ground truth


@pytest.mark.anyio
async def test_fact_check_sandbox_security_rejections():
    """Verify that forbidden imports, dangerous builtins, and infinite loops are strictly rejected."""
    agent = FactCheckAgent(ai_provider=DummyAI())

    # 1. Blocked import 'os'
    with pytest.raises(CodeSandboxSecurityError) as exc_info:
        agent.execute_snippet_sandboxed("import os\nprint(os.getcwd())")
    assert "Blocked import 'os'" in str(exc_info.value)

    # 2. Blocked import 'sys'
    with pytest.raises(CodeSandboxSecurityError):
        agent.execute_snippet_sandboxed("import sys\nprint(sys.version)")

    # 3. Blocked builtin call 'open'
    with pytest.raises(CodeSandboxSecurityError) as exc_info:
        agent.execute_snippet_sandboxed("f = open('secret.txt', 'w')")
    assert "Blocked dangerous builtin" in str(exc_info.value)

    # 4. Blocked builtin call 'eval'
    with pytest.raises(CodeSandboxSecurityError):
        agent.execute_snippet_sandboxed("eval('1 + 1')")

    # 5. Infinite loop hard timeout (3.0s)
    with pytest.raises(CodeSandboxSecurityError) as exc_info:
        agent.execute_snippet_sandboxed("while True: pass")
    assert "timed out" in str(exc_info.value).lower()


def test_quiz_card_renderer_visual_output(tmp_path):
    """Verify that QuizCardRenderer generates high-res 1080x1920 distinct PNG cards."""
    q_card, r_card = QuizCardRenderer.render_quiz_cards(
        question_code="x = 10\ny = 20\nprint(x + y)",
        options=["A) 1020", "B) 30", "C) None", "D) Error"],
        correct_option="B",
        explanation="Integers in Python are added mathematically.",
        output_dir=str(tmp_path),
        job_id="unit_test_cards"
    )

    assert Path(q_card).exists()
    assert Path(r_card).exists()

    img_q = Image.open(q_card)
    img_r = Image.open(r_card)

    assert img_q.size == (1080, 1920)
    assert img_r.size == (1080, 1920)

    # Confirm visual distinctness (question vs reveal card are NOT identical)
    assert img_q.tobytes() != img_r.tobytes()


@pytest.mark.anyio
async def test_idea_agent_quiz_generation():
    """Verify IdeaAgent generates Python quiz schema and deduplicates."""
    agent = IdeaAgent(ai_provider=DummyAI())
    res = await agent.generate_daily_topic(slot_index=1)

    assert res["content_format"] == "quiz_card"
    assert "question_code" in res and len(res["question_code"]) > 0
    assert len(res["options"]) == 4
    assert res["correct_option"] in ("A", "B", "C", "D")
    assert "explanation" in res and len(res["explanation"]) > 0


@pytest.mark.anyio
async def test_storyboard_and_media_agent_quiz_cards(tmp_path):
    """Verify StoryboardAgent creates 2 scenes and MediaAgent attaches quiz PNGs."""
    script = Script(
        topic="Python Quiz: List Mutation #Shorts",
        hook="Would you get this right?",
        problem="What will this print?",
        value="Pause and think.",
        payoff="The correct answer is B!",
        cta="Follow for more quizzes!",
        full_narration="Would you get this right? What will this print? Pause and think. The answer is B! Follow for more quizzes!",
        content_format="quiz_card",
        question_code="a = [1, 2]\nb = a\nb.append(3)\nprint(a)",
        options=["A) [1, 2]", "B) [1, 2, 3]", "C) [3]", "D) Error"],
        correct_option="B",
        explanation="Lists in Python are mutable references."
    )

    sb_agent = StoryboardAgent(ai_provider=DummyAI())
    storyboard = await sb_agent.create_storyboard(script=script)

    assert len(storyboard.scenes) == 2
    assert storyboard.scenes[0].visual_type == VisualType.QUIZ_CARD_QUESTION
    assert storyboard.scenes[1].visual_type == VisualType.QUIZ_CARD_REVEAL

    # MediaAgent renders and attaches
    storage = LocalStorageProvider(str(tmp_path))
    class DummyStock:
        async def search_and_acquire(self, **kwargs):
            return Scene(scene_id=1, start=0, end=1, narration="", visual_prompt="")

    media_agent = MediaAgent(stock_provider=DummyStock(), storage_provider=storage)
    storyboard_assets = await media_agent.collect_scene_assets(storyboard, job_id="test_job", script=script)

    assert storyboard_assets.scenes[0].asset_local_path.endswith(".png")
    assert storyboard_assets.scenes[1].asset_local_path.endswith(".png")
    assert Path(storyboard_assets.scenes[0].asset_local_path).exists()
    assert Path(storyboard_assets.scenes[1].asset_local_path).exists()


@pytest.mark.anyio
async def test_voice_and_caption_agents_quiz_simplification(tmp_path):
    """Verify VoiceAgent selects background music without TTS and CaptionAgent is a no-op."""
    script = Script(
        topic="Python Quiz #Shorts",
        hook="Test hook",
        problem="Test prob",
        value="Test val",
        payoff="Test payoff",
        cta="Test cta",
        full_narration="Full narration",
        content_format="quiz_card",
        target_duration_sec=24.0
    )

    storage = LocalStorageProvider(str(tmp_path))
    class DummyTTS:
        async def synthesize_speech(self, **kwargs):
            raise RuntimeError("TTS should NOT be called for quiz_card format!")

    voice_agent = VoiceAgent(tts_provider=DummyTTS(), storage_provider=storage)
    audio_path = await voice_agent.generate_voiceover(script=script, job_id="quiz_audio_test")

    assert Path(audio_path).exists()
    assert "bg_music_" in audio_path

    # CaptionAgent no-op check
    class DummySTT:
        async def transcribe_audio(self, *args):
            raise RuntimeError("STT should NOT be called for quiz_card format!")

    caption_agent = CaptionAgent(stt_provider=DummySTT(), storage_provider=storage)
    ass_path, segments = await caption_agent.generate_captions(audio_filepath=audio_path, job_id="quiz_caption_test")

    assert ass_path == ""
    assert segments == []


@pytest.mark.anyio
async def test_title_and_description_agent_quiz_output():
    """Verify TitleAgent and DescriptionAgent generate rich quiz metadata and SEO hashtags."""
    script = Script(
        topic="Python Quiz: List Mutation #Shorts",
        hook="Would you get this right?",
        problem="What will this print?",
        value="Pause and think.",
        payoff="The answer is B!",
        cta="Follow for more quizzes!",
        full_narration="Narration text",
        content_format="quiz_card",
        concept_tag="list_mutation",
        question_code="a = [1, 2]\nb = a\nb.append(3)\nprint(a)",
        options=["A) [1, 2]", "B) [1, 2, 3]", "C) [3]", "D) Error"],
        correct_option="B",
        explanation="Lists in Python are mutable references, so modifying b changes a."
    )

    t_agent = TitleAgent(ai_provider=DummyAI())
    title_data = await t_agent.generate_title_and_tags(script)
    assert len(title_data["title"]) > 0
    assert any("#python" in h.lower() for h in title_data["hashtags"])
    assert any("python" in t.lower() for t in title_data["tags"])

    d_agent = DescriptionAgent(ai_provider=DummyAI())
    desc = await d_agent.generate_description(script, title_data["title"], title_data["hashtags"])
    assert "✅ CORRECT ANSWER: Option B" in desc
    assert "💡 EXPLANATION:" in desc
    assert "```python" in desc
    assert "#python" in desc


@pytest.mark.anyio
async def test_qc_agent_quiz_cards_distinctness(tmp_path):
    """Verify QCAgent checks image distinctness and passes format-aware checks."""
    # Render two distinct quiz cards
    q_card, r_card = QuizCardRenderer.render_quiz_cards(
        question_code="x = 1\nprint(x)",
        options=["A) 1", "B) 2", "C) 0", "D) Error"],
        correct_option="A",
        explanation="x is 1.",
        output_dir=str(tmp_path / "media_storage" / "assets" / "job_qc_test"),
        job_id="qc_test"
    )

    # Synthesize dummy audio/video for QC probe
    video_dir = tmp_path / "media_storage" / "rendered"
    video_dir.mkdir(parents=True, exist_ok=True)
    dummy_video = video_dir / "short_qc_test.mp4"

    # Create 20s 1080x1920 test mp4 with audio
    import subprocess
    from backend.app.core.ffmpeg_utils import get_ffmpeg_binary
    ffmpeg_bin = get_ffmpeg_binary()
    subprocess.run([
        ffmpeg_bin, "-y",
        "-f", "lavfi", "-i", "testsrc=size=1080x1920:rate=30",
        "-f", "lavfi", "-i", "sine=f=440:d=22",
        "-t", "22",
        "-c:v", "libx264", "-c:a", "aac",
        str(dummy_video)
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    qc_agent = QCAgent(ai_provider=DummyAI())
    report = await qc_agent.audit_video(video_path=str(dummy_video), min_duration=20.0, max_duration=30.0, content_format="quiz_card")

    assert report.resolution_valid is True
    assert report.duration_valid is True
    assert report.audio_present is True
    assert report.quiz_cards_distinct is True
    assert report.passed is True
