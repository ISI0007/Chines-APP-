"""Reading module: graded passages with pinyin + translation."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from services.streak_service import record_activity
from models.reading import ReadingText, UserReadingProgress
from models.user import HskLevel, User
from schemas.content import (
    ReadingCompleteRequest, ReadingTextDetail, ReadingTextSummary, XpResponse,
)

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
