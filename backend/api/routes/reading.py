"""Reading module: graded passages with pinyin + translation."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from services.streak_service import record_activity
from models.reading import ReadingText, UserReadingProgress
from models.user import HskLevel, User
from schemas.content import (
    ReadingCompleteRequest, ReadingTextDetail, ReadingTextSummary, XpResponse,
)


class ReadingLevelStat(BaseModel):
    hsk_level: str
    total: int
    completed: int
    pct: float          # 0.0 – 100.0


class ReadingStatsResponse(BaseModel):
    levels: list[ReadingLevelStat]
    total_completed: int
    total_texts: int

router = APIRouter(prefix="/reading", tags=["reading"])
FIRST_COMPLETION_XP = 10


async def _completed_ids(db: AsyncSession, user_id: int) -> set[int]:
    rows = await db.execute(
        select(UserReadingProgress.text_id).where(
            UserReadingProgress.user_id == user_id, UserReadingProgress.completed.is_(True)
        )
    )
    return set(rows.scalars())


@router.get("/texts", response_model=list[ReadingTextSummary])
async def list_texts(
    hsk_level: Optional[HskLevel] = None,
    topic: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    q = select(ReadingText).order_by(ReadingText.hsk_level, ReadingText.id)
    if hsk_level:
        q = q.where(ReadingText.hsk_level == hsk_level)
    if topic:
        q = q.where(ReadingText.topic == topic)
    texts = (await db.execute(q)).scalars().all()
    done = await _completed_ids(db, user.id)
    return [
        ReadingTextSummary.model_validate(t).model_copy(update={"completed": t.id in done})
        for t in texts
    ]


@router.get("/texts/{text_id}", response_model=ReadingTextDetail)
async def get_text(
    text_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    t = await db.get(ReadingText, text_id)
    if not t:
        raise HTTPException(404, "Text not found")
    done = await _completed_ids(db, user.id)
    return ReadingTextDetail.model_validate(t).model_copy(update={"completed": t.id in done})


@router.post("/texts/{text_id}/complete", response_model=XpResponse)
async def complete_text(
    text_id: int,
    body: ReadingCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Mark a text as read. XP is awarded only on the first completion."""
    if not await db.get(ReadingText, text_id):
        raise HTTPException(404, "Text not found")
    prog = (await db.execute(
        select(UserReadingProgress).where(
            UserReadingProgress.user_id == user.id, UserReadingProgress.text_id == text_id
        )
    )).scalar_one_or_none()

    gained = 0
    if prog is None:
        prog = UserReadingProgress(user_id=user.id, text_id=text_id, completed=False)
        db.add(prog)
    if not prog.completed:
        gained = FIRST_COMPLETION_XP
        user.xp += gained
    record_activity(user)
    prog.completed = True
    prog.read_at = datetime.now(timezone.utc)
    if body.comprehension_score is not None:
        prog.comprehension_score = body.comprehension_score
    await db.commit()
    return XpResponse(xp_gained=gained, total_xp=user.xp)


@router.get("/stats", response_model=ReadingStatsResponse)
async def reading_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Return per-level reading completion statistics for the current user."""
    # All texts grouped by level
    rows = (await db.execute(
        select(ReadingText.hsk_level, func.count(ReadingText.id).label("total"))
        .group_by(ReadingText.hsk_level)
    )).all()

    # Completed ids for this user
    done_ids = await _completed_ids(db, user.id)

    # Count completed per level
    completed_rows = (await db.execute(
        select(ReadingText.hsk_level, func.count(ReadingText.id).label("done"))
        .join(
            UserReadingProgress,
            (UserReadingProgress.text_id == ReadingText.id)
            & (UserReadingProgress.user_id == user.id)
            & (UserReadingProgress.completed.is_(True)),
            isouter=True,
        )
        .where(UserReadingProgress.user_id == user.id, UserReadingProgress.completed.is_(True))
        .group_by(ReadingText.hsk_level)
    )).all()
    done_map: dict[str, int] = {r.hsk_level.value: r.done for r in completed_rows}

    level_order = [l.value for l in HskLevel]
    stats: list[ReadingLevelStat] = []
    total_texts = 0
    total_completed = 0
    for row in sorted(rows, key=lambda r: level_order.index(r.hsk_level.value) if r.hsk_level.value in level_order else 99):
        lv = row.hsk_level.value
        tot = row.total
        done = done_map.get(lv, 0)
        total_texts += tot
        total_completed += done
        stats.append(ReadingLevelStat(
            hsk_level=lv,
            total=tot,
            completed=done,
            pct=round(done / tot * 100, 1) if tot else 0.0,
        ))
    return ReadingStatsResponse(levels=stats, total_completed=total_completed, total_texts=total_texts)
