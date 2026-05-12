"""
Server-side speech-to-text using faster-whisper.
Used as fallback when Web Speech API isn't available (iOS Safari).
Lazy-loads the model on first request to keep startup fast.
"""
import os
import tempfile
from pathlib import Path
from typing import Optional


_model = None
_model_load_attempted = False
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base.en")  # tiny.en, base.en, small.en, medium.en


def _try_load_model():
    """Lazy-load Whisper model; return None if unavailable."""
    global _model, _model_load_attempted
    if _model is not None or _model_load_attempted:
        return _model
    _model_load_attempted = True
    try:
        from faster_whisper import WhisperModel
        print(f"[STT] Loading Whisper model: {MODEL_SIZE} (first request only)...")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        print("[STT] Whisper ready.")
    except ImportError:
        print("[STT] faster-whisper not installed — iOS transcription disabled.")
        print("       Run: pip install faster-whisper")
    except Exception as e:
        print(f"[STT] Whisper failed to load: {e}")
    return _model


def transcribe_audio(audio_bytes: bytes, content_type: str = "audio/webm") -> Optional[str]:
    """Transcribe audio bytes to text. Returns None if unavailable."""
    model = _try_load_model()
    if model is None:
        return None

    suffix = _suffix_for_content_type(content_type)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            beam_size=1,
            language="en",
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text or None
    except Exception as e:
        print(f"[STT] Transcription error: {e}")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _suffix_for_content_type(ct: str) -> str:
    ct = ct.lower()
    if "mp4" in ct or "m4a" in ct or "aac" in ct:
        return ".m4a"
    if "ogg" in ct or "opus" in ct:
        return ".ogg"
    if "wav" in ct:
        return ".wav"
    if "mpeg" in ct or "mp3" in ct:
        return ".mp3"
    return ".webm"


def is_available() -> bool:
    return _try_load_model() is not None
