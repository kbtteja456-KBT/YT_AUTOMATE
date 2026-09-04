"""System resource monitoring and rendering safety guard."""

import shutil
import psutil
from typing import Any


class ResourceGuard:
    """Monitors CPU, RAM, and disk space to prevent rendering from freezing the host."""

    def __init__(
        self,
        min_ram_mb: int = 1500,
        min_disk_gb: int = 5,
        max_cpu_percent: float = 90.0
    ):
        self.min_ram_mb = min_ram_mb
        self.min_disk_gb = min_disk_gb
        self.max_cpu_percent = max_cpu_percent

    def get_system_metrics(self) -> dict[str, Any]:
        """Query host memory, CPU, and disk availability."""
        mem = psutil.virtual_memory()
        disk = shutil.disk_usage(".")
        cpu = psutil.cpu_percent(interval=None)

        ram_available_mb = mem.available / (1024 * 1024)
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        return {
            "ram_available_mb": round(ram_available_mb, 1),
            "ram_total_mb": round(mem.total / (1024 * 1024), 1),
            "ram_percent": mem.percent,
            "disk_free_gb": round(disk_free_gb, 1),
            "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 1),
            "cpu_percent": cpu,
            "is_safe_for_rendering": (
                ram_available_mb >= self.min_ram_mb
                and disk_free_gb >= self.min_disk_gb
            )
        }

    def verify_safe_to_render(self) -> tuple[bool, list[str]]:
        """Verify if current host load permits heavy FFmpeg / Whisper jobs."""
        metrics = self.get_system_metrics()
        warnings = []

        if metrics["ram_available_mb"] < self.min_ram_mb:
            warnings.append(
                f"Low RAM: {metrics['ram_available_mb']}MB available, minimum required is {self.min_ram_mb}MB"
            )

        if metrics["disk_free_gb"] < self.min_disk_gb:
            warnings.append(
                f"Low Disk: {metrics['disk_free_gb']}GB free, minimum required is {self.min_disk_gb}GB"
            )

        return (len(warnings) == 0, warnings)


resource_guard = ResourceGuard()
