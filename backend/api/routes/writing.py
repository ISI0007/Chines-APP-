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


# ── Stroke-order scoring ──────────────────────────────────────────────────────

class StrokeScoreRequest(BaseModel):
    char: str                       # single Chinese character
    stroke_sequence: list[list[float]]   # list of [x, y] points per stroke
    expected_stroke_count: Optional[int] = None


class StrokeScoreResponse(BaseModel):
    char: str
    score: float                    # 0.0 – 1.0
    strokes_drawn: int
    strokes_expected: int
    feedback: str
    xp_gained: int
    total_xp: int


def _score_strokes(drawn: int, expected: int, points: list) -> float:
    """
    Heuristic stroke-order score.
    Penalises wrong stroke count and very short/empty strokes.
    Returns 0.0–1.0.
    """
    if expected == 0 or drawn == 0:
        return 0.0
    count_ratio = min(drawn, expected) / max(drawn, expected)
    # Penalise empty/trivial strokes
    valid = sum(1 for s in points if len(s) >= 2)
    quality = valid / drawn if drawn > 0 else 0
    return round(min(1.0, count_ratio * 0.7 + quality * 0.3), 3)


@router.post("/characters/{char}/score", response_model=StrokeScoreResponse)
async def score_stroke(
    char: str,
    body: StrokeScoreRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Score a user's stroke drawing for a single character.
    Clients send the captured stroke point arrays; the backend scores
    against expected stroke count and updates practice progress.

    Expected stroke counts come from the Character DB row when available;
    clients may also pass `expected_stroke_count` directly.
    """
    # Resolve expected stroke count
    char_row = (await db.execute(
        select(Character).where(Character.char == char)
    )).scalar_one_or_none()

    expected = body.expected_stroke_count or (char_row.stroke_count if char_row and hasattr(char_row, "stroke_count") else len(body.stroke_sequence))

    drawn = len(body.stroke_sequence)
    score = _score_strokes(drawn, expected, body.stroke_sequence)

    # Update practice record (reuse existing logic)
    xp_gained = 0
    mastered_threshold = 10
    if char_row:
        prog = (await db.execute(
            select(UserCharacterProgress)
            .where(UserCharacterProgress.user_id == user.id, UserCharacterProgress.char_id == char_row.id)
        )).scalar_one_or_none()
        if prog is None:
            prog = UserCharacterProgress(user_id=user.id, char_id=char_row.id, times_practiced=0, mastered=False)
            db.add(prog)
            xp_gained += FIRST_PRACTICE_XP
        prog.times_practiced += 1
        prog.last_practiced = datetime.now(timezone.utc)
        if not prog.mastered and prog.times_practiced >= mastered_threshold and score >= 0.7:
            prog.mastered = True
            xp_gained += MASTER_XP
        user.xp += xp_gained
        record_activity(user)
        await db.commit()

    pct = int(score * 100)
    if pct >= 85:
        feedback = "Excellent! Stroke order and form look great."
    elif pct >= 65:
        feedback = "Good attempt. Check the stroke count and direction."
    elif pct >= 40:
        feedback = "Keep practising — focus on stroke order."
    else:
        feedback = "Try again — make sure each stroke is drawn clearly."

    return StrokeScoreResponse(
        char=char,
        score=score,
        strokes_drawn=drawn,
        strokes_expected=expected,
        feedback=feedback,
        xp_gained=xp_gained,
        total_xp=user.xp,
    )
