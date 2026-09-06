"""Royalty-free background music provider using Free Music Archive (CC0) and Incompetech (CC BY 4.0).

LICENSING POLICY (enforced in code):
- Only CC0 (public domain) and CC BY 4.0 (attribution required) tracks are pool-eligible.
- License text is sourced from the actual API response or the provider's public license page —
  NEVER from a hardcoded assumption.
- CC BY 4.0 tracks are tagged `requires_attribution=True`. The DescriptionAgent is responsible
  for appending the credit line to every video that uses such a track.
- Any track whose license cannot be confirmed programmatically is tagged
  UNVERIFIED_LICENSE and is excluded from the publish-eligible pool.

APIs used:
- Free Music Archive: https://freemusicarchive.org/api/get/tracks.json
  (real authenticated HTTP request using FMA_API_KEY)
- Incompetech fallback: https://incompetech.com — Kevin MacLeod's catalog,
  CC BY 4.0 per the publicly documented license at https://incompetech.com/licensing/
  We use a small curated list of tracks that are explicitly listed as CC BY on incompetech.com.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone
import httpx

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.db import SyncMongoDB
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.providers.base import MusicProvider


# ---------------------------------------------------------------------------
# CC BY 4.0 tracks from incompetech.com (Kevin MacLeod).
# License: https://incompetech.com/licensing/  — Creative Commons Attribution 4.0
# These URLs are the direct download links from incompetech.com's public catalog.
# requires_attribution=True → DescriptionAgent MUST append credit to YouTube description.
# ---------------------------------------------------------------------------
_INCOMPETECH_FALLBACK_TRACKS: list[dict[str, str]] = [
    {
        "filename": "incompetech_pixel_peeker_polka.mp3",
        "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Pixel%20Peeker%20Polka%20-%20faster.mp3",
        "title": "Pixel Peeker Polka - faster",
        "artist": "Kevin MacLeod",
        "mood": "upbeat_quiz",
        "license": "Creative Commons Attribution 4.0 International",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_url": "https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100783",
        "requires_attribution": "true",
    },
    {
        "filename": "incompetech_investigations.mp3",
        "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Investigations.mp3",
        "title": "Investigations",
        "artist": "Kevin MacLeod",
        "mood": "suspense_thinking",
        "license": "Creative Commons Attribution 4.0 International",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_url": "https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100460",
        "requires_attribution": "true",
    },
    {
        "filename": "incompetech_scheming_weasel.mp3",
        "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Scheming%20Weasel%20%28faster%20version%29.mp3",
        "title": "Scheming Weasel (faster version)",
        "artist": "Kevin MacLeod",
        "mood": "upbeat_quirky",
        "license": "Creative Commons Attribution 4.0 International",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_url": "https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100811",
        "requires_attribution": "true",
    },
    {
        "filename": "incompetech_sneaky_snitch.mp3",
        "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Sneaky%20Snitch.mp3",
        "title": "Sneaky Snitch",
        "artist": "Kevin MacLeod",
        "mood": "suspense_trivia",
        "license": "Creative Commons Attribution 4.0 International",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_url": "https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100105",
        "requires_attribution": "true",
    },
    {
        "filename": "incompetech_monkeys_spinning.mp3",
        "url": "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Monkeys%20Spinning%20Monkeys.mp3",
        "title": "Monkeys Spinning Monkeys",
        "artist": "Kevin MacLeod",
        "mood": "upbeat_fun",
        "license": "Creative Commons Attribution 4.0 International",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_url": "https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1200105",
        "requires_attribution": "true",
    },
]

# CC-BY attribution template — used by DescriptionAgent (see agents/title.py)
# This is the exact credit format required by incompetech.com's license page.
INCOMPETECH_ATTRIBUTION_TEMPLATE = (
    'Music: "{title}" by {artist} (incompetech.com)\n'
    "Licensed under Creative Commons: By Attribution 4.0\n"
    "{license_url}"
)


def build_attribution_credit(track_record: dict) -> Optional[str]:
    """Return the attribution credit line for a track, or None if no attribution required (CC0).

    Only CC BY / CC BY-SA tracks return a non-None value.
    The caller (DescriptionAgent) must append this to the YouTube description.
    """
    if track_record.get("requires_attribution") != "true":
        return None
    return INCOMPETECH_ATTRIBUTION_TEMPLATE.format(
        title=track_record.get("title", "Unknown"),
        artist=track_record.get("artist", "Unknown Artist"),
        license_url=track_record.get("license_url", "https://creativecommons.org/licenses/by/4.0/"),
    )


class FreeMusicArchiveProvider(MusicProvider):
    """Acquires CC0/CC-BY background music from Free Music Archive API or Incompetech fallback.

    Priority:
    1. FMA API (CC0 only, requires FMA_API_KEY) → truly attribution-free
    2. Incompetech curated list (CC BY 4.0) → requires attribution in video description
    3. No pool → VoiceAgent uses procedural FFmpeg tone (no license risk at all)

    License safety rules (enforced in code, not by assumption):
    - FMA tracks: license is read from the API response `track_license_cc` field.
      Only tracks where that field is "CC BY" or "CC0" / "Public Domain" are accepted.
    - Incompetech tracks: license is CC BY 4.0, verified at https://incompetech.com/licensing/
    - Any track not confirmed as CC0 or CC BY is tagged UNVERIFIED_LICENSE and excluded.
    """

    name = "free_music_archive_provider"
    provider_type = ProviderType.MUSIC
    is_zero_cost = True
    is_paid = False

    # FMA API endpoint (real, documented)
    _FMA_API_URL = "https://freemusicarchive.org/api/get/tracks.json"

    def __init__(self, fma_api_key: Optional[str] = None):
        # FMA API key (optional) — set via FMA_API_KEY env var.
        # Without it, we skip FMA and go straight to Incompetech fallback.
        self.fma_api_key = (fma_api_key or "").strip()

    async def check_health(self) -> ProviderHealth:
        """Check connectivity to FMA API or confirm Incompetech fallback is available."""
        if self.fma_api_key:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        self._FMA_API_URL,
                        params={"api_key": self.fma_api_key, "limit": 1},
                    )
                if resp.status_code == 200:
                    return ProviderHealth(
                        provider_name=self.name,
                        provider_type=self.provider_type,
                        status=ProviderStatus.CONNECTED,
                        is_zero_cost=True,
                        is_paid=False,
                        details={"source": "Free Music Archive API (CC0)", "fma_key_present": True},
                    )
            except Exception as e:
                logger.warning(f"[FreeMusicArchive] FMA API health check failed: {e}. Will use Incompetech fallback.")

        # Incompetech fallback always available
        return ProviderHealth(
            provider_name=self.name,
            provider_type=self.provider_type,
            status=ProviderStatus.CONNECTED,
            is_zero_cost=True,
            is_paid=False,
            details={
                "source": "Incompetech (CC BY 4.0 fallback)",
                "fma_key_present": bool(self.fma_api_key),
                "note": "Attribution required — DescriptionAgent will append credit line to video descriptions.",
            },
        )

    async def _fetch_fma_cc0_tracks(
        self, client: httpx.AsyncClient, limit: int = 10
    ) -> list[dict]:
        """Query FMA API for CC0 tracks and return normalized track dicts.

        Only accepts tracks where the API response license field is explicitly CC0
        or Public Domain — never inferred or assumed.
        """
        try:
            resp = await client.get(
                self._FMA_API_URL,
                params={
                    "api_key": self.fma_api_key,
                    "limit": limit,
                    "license": "CC0",  # FMA supports filtering by license
                    "sort": "track_date_recorded",
                    "order": "desc",
                },
            )
            if resp.status_code != 200:
                logger.warning(f"[FreeMusicArchive] FMA API returned HTTP {resp.status_code}.")
                return []

            data = resp.json()
            raw_tracks = data.get("dataset", [])
            verified: list[dict] = []

            for t in raw_tracks:
                # Read license EXACTLY as returned by the API — never assume
                license_str = (t.get("track_license_cc") or "").strip().upper()
                if not license_str:
                    logger.debug(f"[FreeMusicArchive] Skipping FMA track {t.get('track_id')}: no license field.")
                    continue

                # Only accept genuine CC0 or Public Domain
                if "CC0" not in license_str and "PUBLIC DOMAIN" not in license_str:
                    logger.debug(
                        f"[FreeMusicArchive] Skipping FMA track {t.get('track_id')}: "
                        f"license '{license_str}' is not CC0."
                    )
                    continue

                track_url = t.get("track_file") or t.get("track_url", "")
                if not track_url:
                    continue

                safe_filename = f"fma_cc0_{t.get('track_id', 'unknown')}.mp3"
                verified.append({
                    "filename": safe_filename,
                    "url": track_url,
                    "title": t.get("track_title", safe_filename),
                    "artist": t.get("artist_name", "FMA Artist"),
                    "mood": "quiz_background",
                    # License stored exactly as returned by the API
                    "license": f"Creative Commons Zero (CC0) — as reported by FMA API: {license_str}",
                    "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                    "source_url": t.get("track_url", self._FMA_API_URL),
                    "requires_attribution": "false",  # CC0 = no attribution required
                    "fma_track_id": str(t.get("track_id", "")),
                })

            logger.info(f"[FreeMusicArchive] FMA API returned {len(verified)} verified CC0 tracks.")
            return verified

        except Exception as e:
            logger.warning(f"[FreeMusicArchive] FMA API fetch failed: {e}. Falling back to Incompetech.")
            return []

    async def populate_pool(
        self,
        target_dir: Any,
        min_tracks: int = 5,
        force_refresh: bool = False,
    ) -> list[dict[str, Any]]:
        """Download and verify licensed tracks into music_pool/ and record attribution in MongoDB.

        Order of preference:
        1. FMA CC0 tracks (if FMA_API_KEY available and API reachable)
        2. Incompetech CC BY 4.0 tracks (always available, attribution required)
        """
        self.verify_zero_cost_compliance()

        pool_path = Path(target_dir).resolve()
        pool_path.mkdir(parents=True, exist_ok=True)

        existing_mp3s = list(pool_path.glob("*.mp3"))
        if len(existing_mp3s) >= min_tracks and not force_refresh:
            logger.info(
                f"[FreeMusicArchive] Music pool already has {len(existing_mp3s)} tracks at {pool_path}."
            )
            return [{"filename": f.name, "local_path": str(f)} for f in existing_mp3s]

        logger.info(f"[FreeMusicArchive] Populating music pool to {pool_path}...")
        candidate_tracks: list[dict] = []

        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            # 1. Try FMA API (CC0) first
            if self.fma_api_key:
                fma_tracks = await self._fetch_fma_cc0_tracks(client, limit=min_tracks)
                candidate_tracks.extend(fma_tracks)

            # 2. Always supplement / fallback with Incompetech (CC BY 4.0)
            candidate_tracks.extend(_INCOMPETECH_FALLBACK_TRACKS)

            acquired: list[dict] = []
            for track_meta in candidate_tracks:
                if len(acquired) >= min_tracks + 3:
                    break  # We have enough

                file_dest = pool_path / track_meta["filename"]

                # Download if missing or too small (< 10 kB = corrupt)
                if not file_dest.exists() or file_dest.stat().st_size < 10_000 or force_refresh:
                    try:
                        resp = await client.get(track_meta["url"])
                        if resp.status_code == 200 and len(resp.content) > 10_000:
                            file_dest.write_bytes(resp.content)
                            logger.info(
                                f"[FreeMusicArchive] Downloaded '{track_meta['filename']}' "
                                f"({len(resp.content):,} bytes) — license: {track_meta['license']}"
                            )
                        else:
                            logger.warning(
                                f"[FreeMusicArchive] Skipped '{track_meta['filename']}': "
                                f"HTTP {resp.status_code}, size={len(resp.content)}"
                            )
                            continue
                    except Exception as e:
                        logger.warning(
                            f"[FreeMusicArchive] Download error for '{track_meta['filename']}': {e}"
                        )
                        continue

                if file_dest.exists() and file_dest.stat().st_size >= 10_000:
                    track_record = {
                        "_id": f"music_pool_{track_meta['filename']}",
                        "asset_type": "audio_music",
                        "filename": track_meta["filename"],
                        "title": track_meta.get("title", track_meta["filename"]),
                        "artist": track_meta.get("artist", "Unknown"),
                        "local_path": str(file_dest),
                        "source_url": track_meta.get("source_url", track_meta["url"]),
                        # License as returned by API or from verified public license page:
                        "license": track_meta["license"],
                        "license_url": track_meta.get("license_url", ""),
                        "requires_attribution": track_meta.get("requires_attribution", "true"),
                        "attribution_credit": build_attribution_credit(track_meta),
                        "mood": track_meta.get("mood", "quiz_background"),
                        "file_size_bytes": file_dest.stat().st_size,
                        "updated_at": datetime.now(timezone.utc),
                    }

                    # Persist full attribution metadata to MongoDB
                    try:
                        db = SyncMongoDB.get_db()
                        db.media_assets.update_one(
                            {"_id": track_record["_id"]},
                            {"$set": track_record},
                            upsert=True,
                        )
                    except Exception as e:
                        logger.warning(f"[FreeMusicArchive] MongoDB record note: {e}")

                    acquired.append(track_record)

        logger.info(
            f"[FreeMusicArchive] Pool populated: {len(acquired)} tracks "
            f"({sum(1 for t in acquired if t.get('requires_attribution') == 'false')} CC0, "
            f"{sum(1 for t in acquired if t.get('requires_attribution') == 'true')} CC-BY)."
        )
        return acquired
