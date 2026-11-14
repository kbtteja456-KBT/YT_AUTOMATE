import sys
import os
sys.path.insert(0, os.getcwd())

try:
    import whisper
    model = whisper.load_model("base")
    res = model.transcribe("media_storage/temp/ref_analysis/ref_audio.wav")
    print("TRANSCRIPTION:\n", res["text"])
    print("\nSEGMENTS:")
    for s in res.get("segments", []):
        print(f"{s['start']:.1f}s - {s['end']:.1f}s: {s['text']}")
except Exception as e:
    print("Error with whisper:", e)

