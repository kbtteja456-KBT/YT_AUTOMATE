"""Generate the educational narration for Python Variables trial."""

import asyncio
import edge_tts
from pathlib import Path

OUT_DIR = Path("media_storage/temp/educational_trial")
OUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_PATH = OUT_DIR / "narration.mp3"

SCRIPT = (
    "Imagine you are coding and need a place to store data. In Python, that is called a variable! "
    "Think of a variable as a labeled storage box in your computer's memory. "
    "When we write x equals 10, Python creates the value 10, and places it securely inside box x. "
    "Now, whenever your program mentions x, Python looks right inside that box. "
    "And when we run print x, it immediately displays the value stored inside: 10! "
    "Need to change it? Variables can vary! If we set x equals 25, the old value is replaced with 25. "
    "Run print x again, and the output is now 25. Simple, visual, and stored in memory. "
    "Follow for episode 2 where we explore Python Data Types!"
)


async def main():
    communicate = edge_tts.Communicate(
        text=SCRIPT,
        voice="en-US-AndrewMultilingualNeural",
        rate="+0%",
        pitch="+0Hz"
    )
    submaker = edge_tts.SubMaker()
    with open(AUDIO_PATH, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    print(f"Generated narration at: {AUDIO_PATH}")


if __name__ == "__main__":
    asyncio.run(main())

