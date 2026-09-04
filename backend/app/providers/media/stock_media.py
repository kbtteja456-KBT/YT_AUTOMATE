"""Free licensed stock media (Pexels, Pixabay) and procedural motion graphic asset generator."""

import os
import hashlib
import httpx
from pathlib import Path
from typing import Optional, Any
from PIL import Image, ImageDraw

from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import ProviderError
from backend.app.models.provider import ProviderHealth, ProviderStatus, ProviderType
from backend.app.models.video import Scene, VisualType
from backend.app.providers.base import StockMediaProvider

# Color gradients for procedural typography motion graphics (1080x1920)
CARD_GRADIENTS = [
    ((18, 24, 38), (30, 42, 68), (0, 242, 254)),       # Cyan/Deep Blue
    ((15, 23, 42), (88, 28, 135), (244, 63, 94)),      # Purple/Rose
    ((10, 15, 29), (6, 78, 59), (0, 255, 163)),        # Mint/Emerald
    ((24, 24, 27), (63, 63, 70), (245, 158, 11)),      # Amber/Dark Gray
]


class StockMediaEngine(StockMediaProvider):
    """Acquires free licensed stock media from Pexels & Pixabay or generates procedural motion graphics."""

    name = "stock_media_engine"
    provider_type = ProviderType.STOCK_MEDIA
    is_zero_cost = True
    is_paid = False

    def __init__(self, media_dir: Optional[str] = None):
        self.media_dir = Path(media_dir or "./media_storage/assets").resolve()
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self._download_cache: dict[str, str] = {}

    def _generate_procedural_card(
        self,
        text: str,
        output_path: str,
        scene_id: int = 1,
        width: int = 1080,
        height: int = 1920
    ) -> str:
        """Create high-retention 1080x1920 visual card with gradients and clean typography."""
        bg_dark, bg_mid, accent = CARD_GRADIENTS[scene_id % len(CARD_GRADIENTS)]

        img = Image.new("RGB", (width, height), bg_dark)
        draw = ImageDraw.Draw(img)

        # Gradient interpolation
        for y in range(height):
            ratio = y / height
            r = int(bg_dark[0] * (1 - ratio) + bg_mid[0] * ratio)
            g = int(bg_dark[1] * (1 - ratio) + bg_mid[1] * ratio)
            b = int(bg_dark[2] * (1 - ratio) + bg_mid[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Accent border frame
        draw.rectangle([40, 60, width - 40, height - 60], outline=accent, width=4)

        # Card container
        draw.rounded_rectangle([80, 500, width - 80, 1420], radius=32, fill=(10, 14, 23, 200), outline=(255, 255, 255, 40), width=2)

        # Draw scene badge
        badge_text = f"KEY INSIGHT #{scene_id}"
        draw.rounded_rectangle([120, 540, 440, 610], radius=16, fill=accent)
        draw.text((140, 558), badge_text, fill=(0, 0, 0))

        # Split text into readable chunks
        words = text.split()
        lines = []
        current_line = []
        for w in words:
            current_line.append(w)
            if len(" ".join(current_line)) > 24:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))

        y_offset = 680
        for line in lines[:5]:
            draw.text((120, y_offset), line, fill=(255, 255, 255))
            y_offset += 80

        img.save(output_path, "PNG")
        return output_path

    async def _search_pexels_media(self, query: str, target_dir: Path) -> Optional[dict[str, Any]]:
        """Search and download portrait media from Pexels API."""
        api_key = settings.pexels_api_key.strip()
        if not api_key:
            return None

        headers = {"Authorization": api_key}
        # Try Pexels Photos API (portrait orientation)
        url = "https://api.pexels.com/v1/search"
        params = {"query": query, "orientation": "portrait", "per_page": 3}

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    photos = data.get("photos", [])
                    if photos:
                        photo = photos[0]
                        img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
                        if img_url:
                            # Download image
                            file_hash = hashlib.sha256(img_url.encode("utf-8")).hexdigest()[:12]
                            local_file = target_dir / f"pexels_{file_hash}.jpg"

                            if not local_file.exists():
                                dl_resp = await client.get(img_url)
                                if dl_resp.status_code == 200:
                                    local_file.write_bytes(dl_resp.content)

                            if local_file.exists() and local_file.stat().st_size > 5000:
                                return {
                                    "local_path": str(local_file),
                                    "source_url": photo.get("url", img_url),
                                    "license": "Pexels Free to Use License",
                                    "attribution": f"Photo by {photo.get('photographer', 'Pexels Creator')} on Pexels"
                                }
        except Exception as e:
            logger.warning(f"Pexels media search note: {e}")

        return None

    async def _search_pixabay_media(self, query: str, target_dir: Path) -> Optional[dict[str, Any]]:
        """Search and download vertical media from Pixabay API."""
        api_key = settings.pixabay_api_key.strip()
        if not api_key:
            return None

        url = "https://pixabay.com/api/"
        params = {
            "key": api_key,
            "q": query,
            "image_type": "photo",
            "orientation": "vertical",
            "per_page": 3
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", [])
                    if hits:
                        hit = hits[0]
                        img_url = hit.get("largeImageURL") or hit.get("webformatURL")
                        if img_url:
                            file_hash = hashlib.sha256(img_url.encode("utf-8")).hexdigest()[:12]
                            local_file = target_dir / f"pixabay_{file_hash}.jpg"

                            if not local_file.exists():
                                dl_resp = await client.get(img_url)
                                if dl_resp.status_code == 200:
                                    local_file.write_bytes(dl_resp.content)

                            if local_file.exists() and local_file.stat().st_size > 5000:
                                return {
                                    "local_path": str(local_file),
                                    "source_url": hit.get("pageURL", img_url),
                                    "license": "Pixabay Content License (Free to use)",
                                    "attribution": f"Image by {hit.get('user', 'Pixabay Creator')} from Pixabay"
                                }
        except Exception as e:
            logger.warning(f"Pixabay media search note: {e}")

        return None

    async def search_and_acquire(
        self,
        query: str,
        duration_sec: float,
        target_dir: str,
        visual_type: str = "motion_graphic"
    ) -> Scene:
        """Acquire visual asset for a storyboard scene: Pexels -> Pixabay -> Procedural Card."""
        self.verify_zero_cost_compliance()

        target_path = Path(target_dir).resolve()
        target_path.mkdir(parents=True, exist_ok=True)

        content_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]

        # 1. Try Pexels if visual_type requests stock footage or image
        if visual_type in ["stock_footage", "generated_image"]:
            pexels_res = await self._search_pexels_media(query, target_path)
            if pexels_res:
                logger.info(f"Acquired Pexels stock media for '{query[:30]}...' -> {pexels_res['local_path']}")
                return Scene(
                    scene_id=1,
                    start=0.0,
                    end=duration_sec,
                    narration="",
                    visual_type=VisualType.STOCK_FOOTAGE,
                    visual_prompt=query,
                    asset_local_path=pexels_res["local_path"],
                    asset_url=pexels_res["source_url"],
                    license_info=pexels_res["license"],
                    attribution=pexels_res["attribution"]
                )

            # 2. Try Pixabay
            pixabay_res = await self._search_pixabay_media(query, target_path)
            if pixabay_res:
                logger.info(f"Acquired Pixabay stock media for '{query[:30]}...' -> {pixabay_res['local_path']}")
                return Scene(
                    scene_id=1,
                    start=0.0,
                    end=duration_sec,
                    narration="",
                    visual_type=VisualType.STOCK_FOOTAGE,
                    visual_prompt=query,
                    asset_local_path=pixabay_res["local_path"],
                    asset_url=pixabay_res["source_url"],
                    license_info=pixabay_res["license"],
                    attribution=pixabay_res["attribution"]
                )

        # 3. Procedural high-retention 1080x1920 graphic card
        output_file = str(target_path / f"scene_{content_hash}.png")
        self._generate_procedural_card(
            text=query,
            output_path=output_file,
            scene_id=int(content_hash[:2], 16) % 10 + 1
        )

        return Scene(
            scene_id=1,
            start=0.0,
            end=duration_sec,
            narration="",
            visual_type=VisualType.MOTION_GRAPHIC,
            visual_prompt=query,
            asset_local_path=output_file,
            license_info="Procedural Open Asset (Autopilot Engine Generated)",
            attribution="AI YouTube Shorts Autopilot Engine"
        )

    async def check_health(self) -> ProviderHealth:
        """Verify stock media capabilities (Pexels, Pixabay, Pillow engine)."""
        has_pexels = bool(settings.pexels_api_key.strip())
        has_pixabay = bool(settings.pixabay_api_key.strip())

        try:
            test_file = self.media_dir / "health_check.png"
            self._generate_procedural_card("Health Check", str(test_file), scene_id=1)
            test_file.unlink(missing_ok=True)

            return ProviderHealth(
                provider_name=self.name,
                provider_type=self.provider_type,
                status=ProviderStatus.CONNECTED,
                is_zero_cost=True,
                is_paid=False,
                details={
                    "procedural_engine": True,
                    "pexels_api_configured": has_pexels,
                    "pixabay_api_configured": has_pixabay
                }
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
