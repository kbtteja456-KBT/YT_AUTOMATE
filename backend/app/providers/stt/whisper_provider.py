"""Local Faster-Whisper STT provider producing word-level timestamps."""

import time
from typing import Optional
from pathlib import Path
from faster_whisper import WhisperModel

from backend.app.core.logging import logger
from backend.app.core.errors import ProviderError
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.models.video import CaptionSegment, CaptionWord
from backend.app.providers.base import STTProvider


class WhisperProvider(STTProvider):
    """Local, open-source transcription engine running on CPU/CUDA with word timestamps."""

    name = "faster_whisper"
    provider_type = ProviderType.STT
    is_zero_cost = True
    is_paid = False

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    def _get_model(self) -> WhisperModel:
        """Lazy load model to save memory until transcription is needed."""
        if self._model is None:
            logger.info(f"Loading local Faster-Whisper model ({self.model_size}) on {self.device}...")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model

    async def transcribe_audio(self, audio_filepath: str) -> list[CaptionSegment]:
        """Transcribe narration audio and extract word-level and phrase timestamps."""
        self.verify_zero_cost_compliance()

        audio_path = Path(audio_filepath).resolve()
        if not audio_path.exists():
            raise ProviderError(f"Audio file not found for transcription: {audio_filepath}")

        try:
            model = self._get_model()
            segments_generator, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                word_timestamps=True,
                vad_filter=True  # Filter out silence
            )

            results: list[CaptionSegment] = []

            for segment in segments_generator:
                words_list: list[CaptionWord] = []
                if segment.words:
                    for w in segment.words:
                        words_list.append(CaptionWord(
                            word=w.word.strip(),
                            start=round(w.start, 2),
                            end=round(w.end, 2),
                            confidence=round(w.probability, 2)
                        ))

                results.append(CaptionSegment(
                    text=segment.text.strip(),
                    start=round(segment.start, 2),
                    end=round(segment.end, 2),
                    words=words_list
                ))

            logger.info(f"Whisper transcribed {len(results)} segments from {audio_path.name} (language: {info.language})")
            return results

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise ProviderError(f"Whisper transcription failed: {e}")

    async def check_health(self) -> ProviderHealth:
        """Verify Faster-Whisper runtime availability."""
        try:
            # Check library import and device initialization
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.CONNECTED,
                is_zero_cost=True,
                is_paid=False,
                details={"model_size": self.model_size, "device": self.device}
            )
        except Exception as e:
            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.OFFLINE,
                is_zero_cost=True,
                is_paid=False,
                error_message=str(e)
            )
