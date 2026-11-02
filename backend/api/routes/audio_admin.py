"""
Native audio mapping admin route.
POST /api/v1/audio-admin/words/{word_id}/audio  — upload or map a native audio file to a word.
GET  /api/v1/audio-admin/words/{word_id}/audio  — return the current mapping.
DELETE /api/v1/audio-admin/words/{word_id}/audio — remove the mapping.
"""
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.user import User
from models.vocabulary import Word
from services.audio_service import AUDIO_ROOT

router = APIRouter(prefix="/audio-admin", tags=["audio-admin"])

ALLOWED_AUDIO = {"audio/mpeg", "audio/mp3", "audio/ogg", "audio/wav", "audio/webm", "audio/mp4"}
MAX_AUDIO_MB = 10


class AudioMappingResponse(BaseModel):
    word_id: int
    simplified: str
    audio_path: Optional[str]
    audio_url: Optional[str]   # full API URL to stream it


async def _get_word(word_id: int, db: AsyncSession) -> Word:
    row = (await db.execute(select(Word).where(Word.id == word_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Word {word_id} not found")
    return row


@router.get("/words/{word_id}/audio", response_model=AudioMappingResponse)
async def get_audio_mapping(
    word_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(current_user),
):
    """Return the current native audio mapping for a word."""
    word = await _get_word(word_id, db)
    url = f"/api/v1/audio/{word.audio_path}" if word.audio_path else None
    return AudioMappingResponse(word_id=word.id, simplified=word.simplified,
                                audio_path=word.audio_path, audio_url=url)


@router.post("/words/{word_id}/audio", response_model=AudioMappingResponse)
async def upload_audio_mapping(
    word_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(current_user),
):
    """
    Upload a native audio file and map it to a vocabulary word.
    Accepted formats: MP3, OGG, WAV, WebM, MP4/AAC.
    Max size: 10 MB.
    Stored at: backend/data/audio/<hsk_level>/<simplified>.<ext>
    """
    # Validate content type
    ct = (file.content_type or "").lower()
    if not any(ct.startswith(a.split("/")[0]) or ct == a for a in ALLOWED_AUDIO):
        raise HTTPException(status_code=415, detail=f"Unsupported audio type: {ct}. Allowed: mp3, ogg, wav, webm, m4a")

    word = await _get_word(word_id, db)

    # Determine extension
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() or "mp3"
    if ext not in {"mp3", "ogg", "wav", "webm", "m4a", "mp4"}:
        ext = "mp3"

    # Level subfolder
    level = word.hsk_level.value if hasattr(word.hsk_level, "value") else str(word.hsk_level)
    level_dir = AUDIO_ROOT / level.lower()
    level_dir.mkdir(parents=True, exist_ok=True)

    # Remove old file(s) for this word
    for old in level_dir.glob(f"{word.simplified}.*"):
        try:
            old.unlink()
        except OSError:
            pass

    dest = level_dir / f"{word.simplified}.{ext}"

    # Stream-write file; enforce size limit
    read = 0
    max_bytes = MAX_AUDIO_MB * 1024 * 1024
    try:
        with dest.open("wb") as f:
            while chunk := await file.read(65536):
                read += len(chunk)
                if read > max_bytes:
                    dest.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail=f"File exceeds {MAX_AUDIO_MB} MB limit")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    # Store relative path (level/simplified.ext) in DB
    relative_path = f"{level.lower()}/{word.simplified}.{ext}"
    word.audio_path = relative_path
    await db.commit()
    await db.refresh(word)

    return AudioMappingResponse(
        word_id=word.id,
        simplified=word.simplified,
        audio_path=relative_path,
        audio_url=f"/api/v1/audio/{relative_path}",
    )


@router.delete("/words/{word_id}/audio", response_model=AudioMappingResponse)
async def delete_audio_mapping(
    word_id: int,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(current_user),
):
    """Remove the native audio file and DB mapping for a word."""
    word = await _get_word(word_id, db)

    if word.audio_path:
        path = (AUDIO_ROOT / word.audio_path).resolve()
        if path.is_relative_to(AUDIO_ROOT.resolve()) and path.is_file():
            path.unlink(missing_ok=True)
        word.audio_path = None
        await db.commit()

    return AudioMappingResponse(word_id=word.id, simplified=word.simplified,
                                audio_path=None, audio_url=None)
