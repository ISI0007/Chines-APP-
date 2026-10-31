"""Writing / stroke-order module: character curriculum + practice tracking."""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.user import HskLevel, User
from models.writing import Character, UserCharacterProgress
from services.streak_service import record_activity

router = APIRouter(prefix="/writing", tags=["writing"])
FIRST_PRACTICE_XP = 3
MASTER_XP = 5


class CharacterResponse(BaseModel):
    id: int
    char: str
    pinyin: str
    meaning: list[str]
    hsk_level: HskLevel
    times_practiced: int = 0
    mastered: bool = False

    model_config = {"from_attributes": True}

    @field_validator("meaning", mode="before")
    @classmethod
    def _parse(cls, v):
        return json.loads(v) if isinstance(v, str) else v


class PracticeRequest(BaseModel):
    mastered: bool = False


class PracticeResponse(BaseModel):
    char_id: int
    times_practiced: int
    mastered: bool
    xp_gained: int
    total_xp: int


@router.get("/characters", response_model=list[CharacterResponse])
async def list_characters(
    hsk_level: Optional[HskLevel] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Writing-character curriculum for a level (official 书写字), in syllabus order, with the
    user's practice state. Render strokes on the client with hanzi-writer using `char`."""
    q = select(Character).order_by(Character.hsk_level, Character.order_index)
    if hsk_level:
        q = q.where(Character.hsk_level == hsk_level)
    chars = (await db.execute(q)).scalars().all()

    prog = {
        p.char_id: p for p in (await db.execute(
            select(UserCharacterProgress).where(UserCharacterProgress.user_id == user.id)
        )).scalars()
    }
    out = []
    for c in chars:
        r = CharacterResponse.model_validate(c)
        p = prog.get(c.id)
        if p:
            r = r.model_copy(update={"times_practiced": p.times_practiced, "mastered": p.mastered})
        out.append(r)
    return out


@router.post("/characters/{char_id}/practice", response_model=PracticeResponse)
async def practice(
    char_id: int,
    body: PracticeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Record one practice of a character. XP on first practice and on first mastery."""
    if not await db.get(Character, char_id):
        raise HTTPException(404, "Character not found")
    p = (await db.execute(
        select(UserCharacterProgress).where(
            UserCharacterProgress.user_id == user.id, UserCharacterProgress.char_id == char_id
        )
    )).scalar_one_or_none()

    gained = 0
    if p is None:
        p = UserCharacterProgress(user_id=user.id, char_id=char_id, times_practiced=0, mastered=False)
        db.add(p)
        gained += FIRST_PRACTICE_XP
    if body.mastered and not p.mastered:
        gained += MASTER_XP
        p.mastered = True
    p.times_practiced += 1
    p.last_practiced = datetime.now(timezone.utc)
    if gained:
        user.xp += gained
    record_activity(user)
    await db.commit()
    await db.refresh(p)
    return PracticeResponse(char_id=char_id, times_practiced=p.times_practiced,
                            mastered=p.mastered, xp_gained=gained, total_xp=user.xp)


@router.get("/progress")
async def writing_progress(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Per-level writing progress: total characters, how many practiced, how many mastered."""
    levels = {}
    for lv in HskLevel:
        total = (await db.execute(
            select(func.count(Character.id)).where(Character.hsk_level == lv)
        )).scalar_one()
        practiced = (await db.execute(
            select(func.count(UserCharacterProgress.id))
            .where(UserCharacterProgress.user_id == user.id)
            .join(Character, (Character.id == UserCharacterProgress.char_id) & (Character.hsk_level == lv))
        )).scalar_one()
        mastered = (await db.execute(
            select(func.count(UserCharacterProgress.id))
            .where(UserCharacterProgress.user_id == user.id, UserCharacterProgress.mastered == True)
            .join(Character, (Character.id == UserCharacterProgress.char_id) & (Character.hsk_level == lv))
        )).scalar_one()
        levels[lv.value] = {"total": total, "practiced": practiced, "mastered": mastered}
    return {"levels": levels}
