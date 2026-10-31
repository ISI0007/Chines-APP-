"""
Audio serving route.
Serves local MP3 files from backend/data/audio/<level>/<simplified>.mp3
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/audio", tags=["audio"])

AUDIO_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "audio"


@router.get("/{hsk_level}/{filename}")
async def serve_audio(hsk_level: str, filename: str):
    """
    Stream a local MP3 audio file.
    Example: GET /api/v1/audio/hsk1/你好.mp3

    If the file doesn't exist, return 404.
    The frontend should fall back to browser-side Google TTS for missing files.
    """
    # Sanitize: prevent directory traversal
    safe_level = hsk_level.lower().replace("..", "").replace("/", "")
    safe_name = filename.replace("..", "").replace("/", "")

    path = AUDIO_ROOT / safe_level / safe_name
    if not path.exists() or path.suffix.lower() != ".mp3":
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(path, media_type="audio/mpeg")
