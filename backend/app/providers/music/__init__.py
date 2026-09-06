"""Music provider package — royalty-free background music for YouTube Shorts."""

from backend.app.providers.music.music_archive import FreeMusicArchiveProvider, build_attribution_credit

__all__ = ["FreeMusicArchiveProvider", "build_attribution_credit"]
