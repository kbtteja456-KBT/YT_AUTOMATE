"""MediaAgent acquiring stock media or rendering procedural 1080x1920 quiz card PNGs."""

from pathlib import Path
from typing import Any, Optional

from backend.app.agents.base import BaseAgent
from backend.app.models.video import Storyboard, Scene, VisualType, Script
from backend.app.providers.base import StockMediaProvider, StorageProvider
from backend.app.renderers.quiz_card import QuizCardRenderer
from backend.app.agents.idea import PYTHON_QUIZ_POOL


class MediaAgent(BaseAgent):
    """Acquires licensed stock assets or renders procedural hand-drawn quiz cards."""

    name = "MediaAgent"

    def __init__(self, stock_provider: StockMediaProvider, storage_provider: StorageProvider):
        self.stock = stock_provider
        self.storage = storage_provider

    async def _fetch_quiz_data(self, job_id: str, script: Optional[Script] = None) -> dict[str, Any]:
        """Resolve quiz question code, options, correct option, and explanation."""
        if script and getattr(script, "question_code", None):
            return {
                "question_code": script.question_code,
                "options": script.options,
                "correct_option": script.correct_option,
                "explanation": script.explanation
            }

        # Query MongoDB content_ideas for the active job or latest record
        try:
            from backend.app.core.db import SyncMongoDB
            db = SyncMongoDB.get_db()
            doc = db.content_ideas.find_one({"content_format": "quiz_card"}, sort=[("created_at", -1)])
            if doc and doc.get("question_code"):
                return doc
        except Exception:
            pass

        return PYTHON_QUIZ_POOL[0]

    async def collect_scene_assets(
        self,
        storyboard: Storyboard,
        job_id: str,
        script: Optional[Script] = None
    ) -> Storyboard:
        """Process each scene in storyboard, generating quiz PNG cards or stock clips."""
        self.log(f"Collecting visual assets for {len(storyboard.scenes)} scenes (job: {job_id})...")

        target_dir = self.storage.get_path("assets", f"job_{job_id}")
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        # Check if storyboard contains quiz card scenes
        has_quiz_scenes = any(
            s.visual_type in (VisualType.QUIZ_CARD_QUESTION, VisualType.QUIZ_CARD_REVEAL, "quiz_card_question", "quiz_card_reveal")
            for s in storyboard.scenes
        )

        q_card_path: Optional[str] = None
        r_card_path: Optional[str] = None

        if has_quiz_scenes:
            quiz_data = await self._fetch_quiz_data(job_id, script)
            self.log(f"Rendering 1080x1920 hand-drawn quiz cards for job {job_id}...")
            q_card_path, r_card_path = QuizCardRenderer.render_quiz_cards(
                question_code=quiz_data.get("question_code", "print('Python')"),
                options=quiz_data.get("options", ["A) None", "B) 0", "C) Output", "D) Error"]),
                correct_option=quiz_data.get("correct_option", "A"),
                explanation=quiz_data.get("explanation", "Python evaluates code step-by-step."),
                output_dir=target_dir,
                job_id=job_id
            )

        updated_scenes: list[Scene] = []
        for scene in storyboard.scenes:
            v_type = scene.visual_type.value if hasattr(scene.visual_type, "value") else str(scene.visual_type)

            if v_type in ("quiz_card_question", VisualType.QUIZ_CARD_QUESTION.value) and q_card_path:
                scene.asset_local_path = q_card_path
                scene.license_info = "Procedural Pillow Hand-drawn Render (Zero-Cost, CC-0)"
                scene.attribution = "Internal Engine"
            elif v_type in ("quiz_card_reveal", VisualType.QUIZ_CARD_REVEAL.value) and r_card_path:
                scene.asset_local_path = r_card_path
                scene.license_info = "Procedural Pillow Hand-drawn Render (Zero-Cost, CC-0)"
                scene.attribution = "Internal Engine"
            else:
                duration = scene.end - scene.start
                acquired_scene = await self.stock.search_and_acquire(
                    query=scene.visual_prompt,
                    duration_sec=duration,
                    target_dir=target_dir,
                    visual_type=v_type
                )
                scene.asset_local_path = acquired_scene.asset_local_path
                scene.license_info = acquired_scene.license_info
                scene.attribution = acquired_scene.attribution

            updated_scenes.append(scene)

        storyboard.scenes = updated_scenes
        self.log(f"All {len(storyboard.scenes)} scene visual assets collected successfully.")
        return storyboard
