"""
    Mobile app records audio → sends to POST /transcribe → gets back English text
    → mobile app sends English text to POST /pipeline
"""

import tempfile
import os
from groq import Groq
from config import GROQ_API_KEY, setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Transcribe Nepali audio bytes and translate to English.

    Args:
        audio_bytes: Raw audio file bytes from the uploaded file
        filename:    Original filename (used to detect format)

    Returns:
        {"nepali": "...", "english": "..."}
    """
    client = Groq(api_key=GROQ_API_KEY)

    # Write to a temp file — Groq SDK needs a file object
    suffix = os.path.splitext(filename)[-1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        # Nepali transcription
        with open(tmp_path, "rb") as f:
            nepali_resp = client.audio.transcriptions.create(
                file=(filename, f),
                model="whisper-large-v3",
                language="ne",
                response_format="text",
            )

        # English translation
        with open(tmp_path, "rb") as f:
            english_resp = client.audio.translations.create(
                file=(filename, f),
                model="whisper-large-v3",
                response_format="text",
            )

        nepali  = nepali_resp.strip()  if isinstance(nepali_resp,  str) else str(nepali_resp)
        english = english_resp.strip() if isinstance(english_resp, str) else str(english_resp)

        logger.info(f"[TRANSCRIBE] Nepali:  {nepali}")
        logger.info(f"[TRANSCRIBE] English: {english}")

        return {"nepali": nepali, "english": english}

    finally:
        os.unlink(tmp_path)  # always clean up temp file
