"""One-time setup script to populate royalty-free music pool tracks for quiz Shorts."""

import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings
from backend.app.providers.music.music_archive import FreeMusicArchiveProvider


async def main():
    print("=" * 60)
    print("Setting up Royalty-Free Background Music Pool (Zero-Cost)")
    print("=" * 60)
    provider = FreeMusicArchiveProvider()
    pool_dir = Path(settings.media_storage_dir) / "audio" / "music_pool"
    
    health = await provider.check_health()
    print(f"Music Provider Status: {health.status.value}")
    if health.error_message:
        print(f"Notice: {health.error_message}")
        return

    tracks = await provider.populate_pool(pool_dir)
    print(f"\nSuccessfully populated {len(tracks)} tracks at: {pool_dir.resolve()}")
    for t in tracks:
        print(f"  - {t['filename']} ({t['mood']}) | {t['license']}")
    print("\nMusic pool setup complete!")


if __name__ == "__main__":
    asyncio.run(main())
