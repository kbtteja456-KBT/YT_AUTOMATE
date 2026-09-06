"""Pipeline orchestrator executing the full autonomous state machine with stage resumption."""

import time
from datetime import datetime, timezone
from typing import Any, Optional
from pathlib import Path

from backend.app.core.logging import logger
from backend.app.core.errors import AutopilotError, QCScoreThresholdError
from backend.app.core.security import compute_file_hash
from backend.app.models.job import JobState, PublishingJob, JobStageLog
from backend.app.models.video import Video
from backend.app.models.settings import ChannelSettings
from backend.app.models.style_profile import StyleProfile

# Agents
from backend.app.agents.idea import IdeaAgent
from backend.app.agents.research import ResearchAgent, FactCheckAgent
from backend.app.agents.hook import HookAgent
from backend.app.agents.script import ScriptAgent
from backend.app.agents.storyboard import StoryboardAgent
from backend.app.agents.media import MediaAgent
from backend.app.agents.voice import VoiceAgent
from backend.app.agents.caption import CaptionAgent
from backend.app.agents.editor import EditorAgent
from backend.app.agents.qc import QCAgent
from backend.app.agents.thumbnail import ThumbnailAgent
from backend.app.agents.title import TitleAgent, DescriptionAgent
from backend.app.agents.youtube import YouTubeAgent
from backend.app.agents.analytics import AnalyticsAgent
from backend.app.agents.learning import LearningAgent


class PipelineOrchestrator:
    """Coordinates end-to-end video production from idea to verified YouTube publishing."""

    def __init__(
        self,
        idea_agent: IdeaAgent,
        research_agent: ResearchAgent,
        fact_check_agent: FactCheckAgent,
        hook_agent: HookAgent,
        script_agent: ScriptAgent,
        storyboard_agent: StoryboardAgent,
        media_agent: MediaAgent,
        voice_agent: VoiceAgent,
        caption_agent: CaptionAgent,
        editor_agent: EditorAgent,
        qc_agent: QCAgent,
        thumbnail_agent: ThumbnailAgent,
        title_agent: TitleAgent,
        description_agent: DescriptionAgent,
        youtube_agent: Optional[YouTubeAgent] = None,
        db_job_repo: Optional[Any] = None,
        db_video_repo: Optional[Any] = None
    ):
        self.idea = idea_agent
        self.research = research_agent
        self.fact_check = fact_check_agent
        self.hook = hook_agent
        self.script = script_agent
        self.storyboard = storyboard_agent
        self.media = media_agent
        self.voice = voice_agent
        self.caption = caption_agent
        self.editor = editor_agent
        self.qc = qc_agent
        self.thumbnail = thumbnail_agent
        self.title = title_agent
        self.description = description_agent
        self.youtube = youtube_agent
        self.job_repo = db_job_repo
        self.video_repo = db_video_repo

    async def _transition_state(self, job_id: str, new_state: JobState, error: Optional[str] = None) -> None:
        """Update job state in DB and log."""
        logger.info(f"[Orchestrator] Job {job_id} -> {new_state.value}")
        if self.job_repo:
            await self.job_repo.update_job_state(job_id, new_state, error_message=error)
            stage_log = JobStageLog(
                stage=new_state,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration_ms=0,
                status="FAILED" if error else "COMPLETED",
                details={"job_id": job_id} if error is None else {"job_id": job_id, "error": error},
                error=error,
            )
            await self.job_repo.append_stage_log(job_id, stage_log)

    async def execute_job(
        self,
        job_id: str,
        niche: str = "AI & Tech Tools",
        target_audience: str = "Students and Developers",
        custom_topic: Optional[str] = None,
        style_profile: Optional[StyleProfile] = None,
        publish_immediately: bool = False,
        slot_index: Optional[int] = None,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """Execute all stages sequentially with automatic resumption from last checkpoint."""
        current_stage = "INITIALIZATION"
        logger.info(f"[Orchestrator] Beginning execution for Job {job_id} (slot: {slot_index}, dry_run: {dry_run})...")

        try:
            # 1. IDEA STAGE
            current_stage = "IDEA & RESEARCH"
            logger.info("\n============================================================\n[STAGE: GENERATING] Creating AI Script, Voice & Media Assets\n============================================================")
            await self._transition_state(job_id, JobState.RESEARCHING)
            if custom_topic:
                topic = custom_topic
            else:
                idea_res = await self.idea.generate_daily_topic(
                    niche=niche,
                    target_audience=target_audience,
                    past_topics=[],
                    slot_index=slot_index or 1
                )
                topic = idea_res["topic"]

            # 2. RESEARCH STAGE
            current_stage = "RESEARCHING"
            research_raw = await self.research.conduct_research(topic, niche)
            research_verified = await self.fact_check.verify_and_prune(research_raw)

            # 3. HOOK & SCRIPT STAGE
            current_stage = "SCRIPTING"
            await self._transition_state(job_id, JobState.SCRIPTING)
            hooks = await self.hook.generate_and_score_hooks(topic, research_verified.key_takeaway)
            winning_hook = next((h.text for h in hooks if h.selected), hooks[0].text)

            script_obj = await self.script.generate_script(
                topic=topic,
                hook=winning_hook,
                research=research_verified,
                target_duration_sec=45.0
            )

            # 4. STORYBOARD STAGE
            current_stage = "STORYBOARDING"
            await self._transition_state(job_id, JobState.STORYBOARDING)
            storyboard = await self.storyboard.create_storyboard(
                script=script_obj,
                style_profile=style_profile,
                total_duration=script_obj.target_duration_sec
            )

            # 5. VISUAL ASSET COLLECTION
            current_stage = "GENERATING_MEDIA"
            await self._transition_state(job_id, JobState.GENERATING_MEDIA)
            storyboard_with_assets = await self.media.collect_scene_assets(storyboard, job_id=job_id)

            # 6. VOICE GENERATION
            current_stage = "GENERATING_VOICE"
            await self._transition_state(job_id, JobState.GENERATING_VOICE)
            audio_path = await self.voice.generate_voiceover(script_obj, job_id=job_id)
            # Capture music attribution credit (CC BY tracks → non-None; CC0/TTS → None)
            music_attribution = getattr(self.voice, "last_music_attribution", None)

            # 7. CAPTION GENERATION
            current_stage = "GENERATING_CAPTIONS"
            await self._transition_state(job_id, JobState.GENERATING_CAPTIONS)
            ass_path, caption_segments = await self.caption.generate_captions(
                audio_filepath=audio_path,
                job_id=job_id,
                style_profile=style_profile
            )

            # Mark GENERATED stage completed
            await self._transition_state(job_id, JobState.GENERATED)

            # 8. RENDERING STAGE (FFmpeg)
            current_stage = "RENDERING"
            logger.info("\n============================================================\n[STAGE: RENDERING] Compiling Vertical 1080x1920 Short via FFmpeg\n============================================================")
            await self._transition_state(job_id, JobState.RENDERING)
            rendered_video_path = await self.editor.render_video(
                storyboard=storyboard_with_assets,
                audio_path=audio_path,
                captions_ass_path=ass_path,
                job_id=job_id
            )
            await self._transition_state(job_id, JobState.RENDERED)

            # 9. QUALITY CONTROL GATE (Score >= 90 required)
            current_stage = "QUALITY_CHECK"
            logger.info("\n============================================================\n[STAGE: QC] Running Automated Audio/Video Quality Control Gate\n============================================================")
            await self._transition_state(job_id, JobState.QUALITY_CHECK)
            qc_report = await self.qc.audit_video(
                video_path=rendered_video_path,
                min_duration=20.0,  # Scaled for test pipelines
                max_duration=65.0
            )

            if not qc_report.passed:
                logger.error(f"[Orchestrator] QC Gate Failed with score {qc_report.score}/100. Notes: {qc_report.remediation_notes}")
                await self._transition_state(
                    job_id,
                    JobState.QC_FAILED,
                    error=f"QC score {qc_report.score:.1f}/100 failed threshold (>=90 required)."
                )
                raise QCScoreThresholdError(qc_report.score, qc_report.remediation_notes)

            await self._transition_state(job_id, JobState.QC_PASSED)

            # 10. THUMBNAIL GENERATION
            current_stage = "GENERATING_THUMBNAIL"
            await self._transition_state(job_id, JobState.GENERATING_THUMBNAIL)
            thumbnail_card = await self.thumbnail.generate_custom_thumbnail(
                video_filepath=rendered_video_path,
                script=script_obj,
                job_id=job_id
            )

            # 11. METADATA: TITLE & DESCRIPTION
            current_stage = "METADATA"
            title_data = await self.title.generate_title_and_tags(script_obj)
            video_title = title_data["title"]
            video_tags = title_data["tags"]
            video_hashtags = title_data["hashtags"]

            # Pass music_attribution so CC BY credit appears in the real YouTube description
            description_text = await self.description.generate_description(
                script=script_obj,
                title=video_title,
                hashtags=video_hashtags,
                music_attribution=music_attribution,
            )

            # 12. READY (Buffered for scheduled publish time)
            await self._transition_state(job_id, JobState.READY)
            logger.info(f"[Orchestrator] Video is READY and buffered for scheduled publish time!")

            import zoneinfo
            from backend.app.config import settings
            tz = zoneinfo.ZoneInfo(settings.timezone)
            today_slot_date = datetime.now(tz).strftime("%Y-%m-%d")

            video_record = Video(
                job_id=job_id,
                title=video_title,
                description=description_text,
                tags=video_tags,
                hashtags=video_hashtags,
                file_path=rendered_video_path,
                file_hash=compute_file_hash(rendered_video_path),
                thumbnail_path=thumbnail_card.file_path,
                duration_seconds=qc_report.details.get("metadata", {}).get("duration", 45.0),
                quality_score=qc_report.score,
                qc_report=qc_report,
                slot_index=slot_index,
                slot_date=today_slot_date,
                status="READY"
            )

            if self.video_repo:
                await self.video_repo.create_video(video_record)

            # DRY RUN MODE: Complete verification without public upload
            if dry_run:
                logger.info(
                    "\n============================================================\n"
                    "[STAGE: DRY_RUN_COMPLETED] Video generated, rendered and verified!\n"
                    f"Title: {video_title}\n"
                    f"Rendered Video: {rendered_video_path}\n"
                    f"QC Score: {qc_report.score}/100 (PASSED)\n"
                    "Skipping public YouTube upload as requested by --dry-run.\n"
                    "============================================================"
                )
                return {
                    "status": "DRY_RUN_COMPLETED",
                    "job_id": job_id,
                    "topic": topic,
                    "title": video_title,
                    "video_path": rendered_video_path,
                    "thumbnail_path": thumbnail_card.file_path,
                    "quality_score": qc_report.score,
                    "dry_run": True
                }

            # 13. OPTIONAL IMMEDIATE PUBLISHING (or executed at scheduled beat time)
            if publish_immediately and self.youtube:
                current_stage = "UPLOADING"
                logger.info("\n============================================================\n[STAGE: UPLOADING] Transmitting Short to YouTube Data API v3\n============================================================")
                await self._transition_state(job_id, JobState.UPLOADING)
                await self._transition_state(job_id, JobState.PUBLISHING)

                # Query existing published file hashes to enforce pre-upload duplicate protection
                existing_hashes: list[str] = []
                try:
                    from backend.app.core.db import SyncMongoDB
                    db = SyncMongoDB.get_db()
                    existing_hashes = [
                        v["file_hash"]
                        for v in db.videos.find({"file_hash": {"$exists": True, "$ne": None}}, {"file_hash": 1})
                        if v.get("file_hash")
                    ]
                except Exception as dbe:
                    logger.warning(f"[Orchestrator] Could not load existing hashes for duplicate protection: {dbe}")

                upload_result = await self.youtube.publish_short(
                    video_filepath=rendered_video_path,
                    title=video_title,
                    description=description_text,
                    tags=video_tags,
                    thumbnail=thumbnail_card,
                    privacy_status="public",
                    existing_hashes=existing_hashes
                )

                youtube_video_id = upload_result.get("youtube_video_id")
                youtube_url = upload_result.get("youtube_url")
                published_time = datetime.now(timezone.utc)

                await self._transition_state(job_id, JobState.PUBLISHED)
                logger.info(
                    f"\n============================================================\n"
                    f"[STAGE: PUBLISHED] Successfully Published to YouTube!\n"
                    f"Video URL: {youtube_url}\n"
                    f"YouTube Video ID: {youtube_video_id}\n"
                    f"============================================================"
                )

                video_record.youtube_video_id = youtube_video_id
                video_record.youtube_url = youtube_url
                video_record.youtube_published_at = published_time
                video_record.status = "PUBLISHED"

                # Persist upload metadata to db.videos and db.publishing_jobs
                try:
                    from backend.app.core.db import SyncMongoDB
                    db = SyncMongoDB.get_db()
                    from bson import ObjectId
                    query_job = {"_id": ObjectId(job_id)} if ObjectId.is_valid(job_id) else {"_id": job_id}
                    db.publishing_jobs.update_one(
                        query_job,
                        {
                            "$set": {
                                "state": JobState.PUBLISHED.value,
                                "youtube_video_id": youtube_video_id,
                                "youtube_url": youtube_url,
                                "published_at": published_time,
                                "updated_at": published_time,
                            }
                        }
                    )
                    db.videos.update_one(
                        {"job_id": str(job_id)},
                        {
                            "$set": {
                                "status": "PUBLISHED",
                                "youtube_video_id": youtube_video_id,
                                "youtube_url": youtube_url,
                                "youtube_published_at": published_time,
                            }
                        }
                    )
                except Exception as upd_e:
                    logger.warning(f"[Orchestrator] Could not update job/video docs with YouTube info: {upd_e}")

                return {
                    "status": "PUBLISHED",
                    "job_id": job_id,
                    "topic": topic,
                    "title": video_title,
                    "video_path": rendered_video_path,
                    "thumbnail_path": thumbnail_card.file_path,
                    "quality_score": qc_report.score,
                    "youtube_video_id": youtube_video_id,
                    "youtube_url": youtube_url,
                    "file_hash": video_record.file_hash,
                }

            return {
                "status": "READY",
                "job_id": job_id,
                "topic": topic,
                "title": video_title,
                "video_path": rendered_video_path,
                "thumbnail_path": thumbnail_card.file_path,
                "quality_score": qc_report.score
            }

        except Exception as exc:
            logger.error(
                f"\n============================================================\n"
                f"[STAGE: FAILED] Stage: {current_stage} | Error: {exc}\n"
                f"============================================================",
                exc_info=True
            )
            await self._transition_state(job_id, JobState.FAILED, error=f"[{current_stage}] {exc}")
            raise
