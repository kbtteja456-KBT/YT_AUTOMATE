"""Local storage provider managing asset lifecycle on disk."""

import os
import shutil
import time
from pathlib import Path
from typing import Optional

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Local disk storage provider managing temporary and rendered media folders."""

    name = "local_storage"
    provider_type = ProviderType.STORAGE
    is_zero_cost = True
    is_paid = False

    def __init__(self, base_dir: Optional[str] = None):
        self.base_path = Path(base_dir or settings.media_storage_dir)
        self.temp_path = self.base_path / "temp"
        self.audio_path = self.base_path / "audio"
        self.rendered_path = self.base_path / "rendered"
        self.captions_path = self.base_path / "captions"
        self.thumbnails_path = self.base_path / "thumbnails"
        self.assets_path = self.base_path / "assets"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required folder hierarchy."""
        for p in [
            self.base_path, self.temp_path, self.audio_path,
            self.rendered_path, self.captions_path,
            self.thumbnails_path, self.assets_path
        ]:
            p.mkdir(parents=True, exist_ok=True)

    def get_path(self, category: str, filename: str) -> str:
        """Get absolute path for given category."""
        category_clean = category.lower().strip()
        dir_map = {
            "temp": self.temp_path,
            "audio": self.audio_path,
            "rendered": self.rendered_path,
            "captions": self.captions_path,
            "thumbnails": self.thumbnails_path,
            "assets": self.assets_path,
        }
        target_dir = dir_map.get(category_clean, self.temp_path)
        return str((target_dir / filename).resolve())

    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Remove orphaned temporary render files older than threshold."""
        deleted = 0
        cutoff = time.time() - (older_than_hours * 3600)

        for item in self.temp_path.iterdir():
            if item.is_file() and item.stat().st_mtime < cutoff:
                try:
                    item.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {item}: {e}")

        logger.info(f"Cleaned up {deleted} old temporary media files.")
        return deleted

    async def check_health(self) -> ProviderHealth:
        """Verify storage directory is writable and check free space."""
        try:
            test_file = self.temp_path / f"test_{int(time.time())}.tmp"
            test_file.write_text("ok")
            test_file.unlink()

            total, used, free = shutil.disk_usage(self.base_path)
            free_gb = round(free / (1024 ** 3), 1)

            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.CONNECTED,
                is_zero_cost=True,
                is_paid=False,
                details={"free_disk_gb": free_gb, "storage_dir": str(self.base_path)}
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
