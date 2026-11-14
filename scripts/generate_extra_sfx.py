"""Synthesize extra high-impact cartoon & Foley sound effects using NumPy."""

import os
import wave
import numpy as np
from pathlib import Path

SFX_DIR = Path("media_storage/assets/sfx")
SFX_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_RATE = 44100


def save_wav(filename: str, audio: np.ndarray):
    filepath = SFX_DIR / filename
    # Normalize and clip to 16-bit PCM
    audio = np.clip(audio, -1.0, 1.0)
    int_data = (audio * 32767).astype(np.int16)
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_data.tobytes())
    print(f"Generated: {filepath} ({len(int_data)/SAMPLE_RATE:.2f}s)")


# 1. Harsh Error Buzzer (Sawtooth / Dual Square wave buzzer: 150Hz + 225Hz)
def make_buzzer():
    dur = 0.55
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
    wave1 = np.sign(np.sin(2 * np.pi * 140 * t))
    wave2 = np.sign(np.sin(2 * np.pi * 210 * t))
    buzzer = 0.5 * (wave1 + wave2)
    # Fast attack, harsh sustain, quick decay
    env = np.ones_like(t)
    decay_len = int(SAMPLE_RATE * 0.08)
    env[-decay_len:] = np.linspace(1, 0, decay_len)
    save_wav("buzzer.wav", buzzer * env * 0.8)


# 2. Cinematic 808 Sub-Bass Impact (Pitch drops from 120Hz to 35Hz with saturation)
def make_sub_bass():
    dur = 1.2
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
    freq = 130 * np.exp(-t * 3.5) + 38
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    bass = np.sin(phase)
    # Add warm harmonic saturation
    bass = np.tanh(bass * 1.8)
    env = np.exp(-t * 2.8)
    save_wav("sub_bass.wav", bass * env * 0.95)


# 3. Cartoon Boxing Glove Punch (Meaty punch thud + high snap)
def make_boxing_punch():
    dur = 0.35
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
    # Noise burst for the crack
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 50)
    # Deep thud pitch drop
    freq = 240 * np.exp(-t * 30) + 50
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    thud = np.sin(phase) * np.exp(-t * 12)
    punch = 0.6 * noise + 0.8 * thud
    save_wav("boxing_punch.wav", punch * 0.9)


# 4. Slide Chute Whoosh (Ascending/Descending cartoon glide)
def make_slide_swoosh():
    dur = 0.8
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
    freq = 300 + 400 * np.sin(np.pi * t / dur)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    glide = np.sin(phase)
    # White noise hiss filter
    noise = np.random.uniform(-1, 1, len(t))
    env = np.sin(np.pi * t / dur) ** 1.5
    sfx = (0.5 * glide + 0.5 * noise) * env
    save_wav("slide_swoosh.wav", sfx * 0.85)


# 5. Warning Siren Alarm (Beep-boop pulsing alert)
def make_siren():
    dur = 0.9
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), False)
    mod = np.sin(2 * np.pi * 5 * t)
    carrier_freq = 600 + 250 * mod
    phase = 2 * np.pi * np.cumsum(carrier_freq) / SAMPLE_RATE
    siren = np.sin(phase)
    env = np.minimum(t * 10, 1.0) * np.exp(-t * 0.5)
    save_wav("siren.wav", siren * env * 0.75)


if __name__ == "__main__":
    make_buzzer()
    make_sub_bass()
    make_boxing_punch()
    make_slide_swoosh()
    make_siren()

