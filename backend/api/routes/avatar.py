"""
Avatar upload / delete endpoint.

POST   /api/v1/users/me/avatar   — upload a new avatar image
DELETE /api/v1/users/me/avatar   — remove avatar

Files are stored under backend/static/avatars/<user_id>.<ext>
and served at /static/avatars/<filename> via FastAPI StaticFiles.

Supported formats: jpeg, png, webp  (max 5 MB).
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.phase3 import UserAvatar
from models.user import User

router = APIRouter(prefix="/users/me", tags=["avatar"])

AVATAR_DIR  = Path(__file__).resolve().parents[2] / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

MAX_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB
ALLOWED_MIME   = {"image/jpeg", "image/png", "image/webp"}
EXT_MAP        = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class AvatarResponse(BaseModel):
    avatar_url: str


def _avatar_url(filename: str) -> str:
    return f"/static/avatars/{filename}"


@router.post("/avatar", response_model=AvatarResponse, status_code=201)
async def upload_avatar(
    file: UploadFile = File(...),
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Upload a profile photo.

    - Max 5 MB
    - Accepted content types: image/jpeg, image/png, image/webp
    - The old avatar is deleted automatically.

    Returns the URL of the newly stored image.
    """
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="Unsupported image type. Use JPEG, PNG, or WebP.")

    data = await file.read()
    if len(data) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit.")

    ext      = EXT_MAP[content_type]
    filename = f"{user.id}.{ext}"
    dest     = AVATAR_DIR / filename

    # Remove old avatar files for this user (any extension)
    for old in AVATAR_DIR.glob(f"{user.id}.*"):
        old.unlink(missing_ok=True)

    dest.write_bytes(data)

    # Upsert DB record
    result = await db.execute(select(UserAvatar).where(UserAvatar.user_id == user.id))
    record = result.scalar_one_or_none()
    if record:
        record.filename  = filename
        record.mime_type = content_type
    else:
        db.add(UserAvatar(user_id=user.id, filename=filename, mime_type=content_type))
    await db.commit()

    return AvatarResponse(avatar_url=_avatar_url(filename))


@router.delete("/avatar", status_code=204)
async def delete_avatar(
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Remove the user's profile photo."""
    result = await db.execute(select(UserAvatar).where(UserAvatar.user_id == user.id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="No avatar found.")

    for f in AVATAR_DIR.glob(f"{user.id}.*"):
        f.unlink(missing_ok=True)

    await db.delete(record)
    await db.commit()
    return JSONResponse(status_code=204, content=None)
