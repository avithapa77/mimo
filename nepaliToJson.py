#!/usr/bin/env python3
"""
INSTALL:  pip install faster-whisper sounddevice soundfile numpy
"""

import json
import time
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

SECONDS     = 3
SAMPLE_RATE = 16_000

def returnText():
    # Record
    print(f"Recording {SECONDS}s — speak Nepali now...")
    audio = sd.rec(int(SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()
    sf.write("_temp.wav", audio, SAMPLE_RATE)
    print("Done Recording.\n")
    print("Loading Whisper...")

    start = time.perf_counter()

    model = WhisperModel("base", device="cpu", compute_type="int8")

    # Nepali text
    segments, _ = model.transcribe("_temp.wav", language="ne", task="transcribe")
    nepali = " ".join([s.text.strip() for s in segments])

    # English text
    segments, _ = model.transcribe("_temp.wav", language="ne", task="translate")

    end = time.perf_counter()
    print(f"Whisper took {end - start:.6f} seconds")

    english = " ".join([s.text.strip() for s in segments])

    # Save JSON
    json.dump({"nepali": nepali, "english": english},
              open("output.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"  {nepali}")
    print(f" {english}")

    return english
if __name__ == "__main__":
   returnText()