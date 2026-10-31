"""
Audio mapping service.

Strategy:
1. Local MP3 files stored at  backend/data/audio/<hsk_level>/<simplified>.mp3
2. Falls back to a free TTS URL (browser-side, no server load)
3. Returns a path the frontend can call as  GET /api/v1/audio/{path}
"""

import os
from pathlib import Path

AUDIO_ROOT = Path(__file__).parent.parent / "data" / "audio"

# Free public TTS endpoint (Mandarin, no key needed, usage: educational)
# Google Translate TTS — only use as fallback; for production, use a proper TTS API
_GTTS_TEMPLATE = (
    "https://translate.google.com/translate_tts"
    "?ie=UTF-8&q={text}&tl=zh-CN&client=tw-ob"
)


def local_audio_path(simplified: str, hsk_level: str) -> str | None:
    """Return the relative path if a local MP3 exists, else None."""
    level_dir = AUDIO_ROOT / hsk_level.lower()
    mp3 = level_dir / f"{simplified}.mp3"
    if mp3.exists():
        return f"audio/{hsk_level.lower()}/{simplified}.mp3"
    return None


def audio_url(simplified: str, hsk_level: str) -> str:
    """
    Return the best available audio URL for a word.
    Priority: local file > free TTS fallback.

    Frontend accesses local files via:
      GET /api/v1/audio/{path}  →  StreamingResponse of the MP3

    TTS fallback is a direct browser-callable URL (no server proxy needed).
    """
    local = local_audio_path(simplified, hsk_level)
    if local:
        return f"/api/v1/{local}"
    # Fallback: let the frontend call Google TTS directly
    return _GTTS_TEMPLATE.format(text=simplified)


def ensure_audio_dirs() -> None:
    """Create audio directories for all HSK levels."""
    for level in ["hsk1", "hsk2", "hsk3", "hsk4", "hsk5", "hsk6"]:
        (AUDIO_ROOT / level).mkdir(parents=True, exist_ok=True)
