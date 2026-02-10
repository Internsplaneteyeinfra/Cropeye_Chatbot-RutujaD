"""
CropEye VoiceBot: Speech-to-Text (STT) and Text-to-Speech (TTS).
Treats transcribed text exactly as typed input; no modification of intent or meaning.
"""

import base64
import io
import os
import tempfile
import subprocess
from gtts import gTTS
from typing import Optional, Tuple
from faster_whisper import WhisperModel

# Language code mapping: chatbot user_language -> gTTS lang code ..
USER_LANG_TO_GTTS = {
    "en": "en",
    "english": "en",
    "hi": "hi",
    "hindi": "hi",
    "mr": "mr",
    "marathi": "mr",
}

def debug(msg: str):
    print(f"[VOICE DEBUG] {msg}")


def get_tts_lang(user_language: Optional[str]) -> str:
    """Resolve gTTS language code from chatbot user_language. Default to English."""
    if not user_language:
        return "en"
    key = (user_language or "").strip().lower()
    return USER_LANG_TO_GTTS.get(key, "en")


# -----------------------------
# FFmpeg audio conversion
# -----------------------------
def convert_to_wav(input_path: str, output_path: str):
    """
    Convert any audio format to Whisper-safe WAV
    """
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            output_path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# Speech → Text (Whisper)
def transcribe_audio(audio_bytes: bytes, content_type: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Transcribe audio to text using faster-whisper.
    Returns (transcribed_text, detected_language_code or None).
    Empty or whitespace-only text is treated as unclear input.
    """

    debug("STT started")

    if not audio_bytes or len(audio_bytes) < 500:
        debug("❌ STT failed: audio too small")
        return "", None

    # try:
    #     from faster_whisper import WhisperModel
    # except ImportError:
    #     print("❌ faster-whisper not installed")
    #     return "", None


    suffix = ".bin"
    if content_type:
        if "webm" in content_type:
            suffix = ".webm"
        elif "ogg" in content_type:
            suffix = ".ogg"
        elif "wav" in content_type:
            suffix = ".wav"
        elif "mpeg" in content_type:
            suffix = ".mp3"

    with open(f"debug_audio{suffix}", "wb") as f:
        f.write(audio_bytes)
    debug(f"Audio saved for debug: debug_audio{suffix}")


    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as raw_tmp:
        raw_tmp.write(audio_bytes)
        raw_tmp.flush()
        raw_path = raw_tmp.name

    wav_path = raw_path.replace(suffix, ".wav")

    try:
        debug("Converting audio to Whisper-safe WAV")
        # Convert to Whisper-safe WAV
        convert_to_wav(raw_path, wav_path)

        model = WhisperModel(
            os.getenv("WHISPER_MODEL", "base"),
            device=os.getenv("WHISPER_DEVICE", "cpu"),
            compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        )

        segments, info = model.transcribe(wav_path, beam_size=5)

        text = " ".join(seg.text for seg in segments).strip()
        detected_lang = getattr(info, "language", None)

        if text:
            debug("✅ STT successful")
            debug(f"Transcribed text: {text}")
            debug(f"Detected language: {detected_lang}")
        else:
            debug("❌ STT completed but no speech detected")

        return text, detected_lang

    finally:
        for p in (raw_path, wav_path):
            try:
                os.unlink(p)
            except Exception:
                pass


def transcribe_audio_base64(audio_base64: str, content_type: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """Decode base64 audio and transcribe. Returns (text, detected_lang)."""
    debug("Received base64 audio for STT")

    try:
        # Remove data URI prefix if present
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",")[1]

        audio_bytes = base64.b64decode(audio_base64)
        debug("Base64 decoded successfully")

        return transcribe_audio(audio_bytes, content_type)

    except Exception as e:
        print("❌ Base64 decode error:", e)
        return "", None

# -----------------------------
# Text → Speech (gTTS)
# -----------------------------
def text_to_speech(text: str, lang: str = "en") -> Optional[bytes]:
    """
    Convert text to speech using gTTS.
    Returns audio bytes (MP3) or None on failure.
    """

    debug("TTS started")

    if not text or not text.strip():
        debug("❌ TTS skipped: empty text")
        return None
    try:
        debug(f"Generating speech (lang={lang})")
        buf = io.BytesIO()
        tts = gTTS(text=text.strip(), lang=lang, slow=False)
        tts.write_to_fp(buf)

        debug("✅ TTS successful")
        return buf.getvalue()

    except Exception:
        debug(f"❌ TTS failed: {e}")
        return None
