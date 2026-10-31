"""Grammar lessons."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from services.streak_service import record_activity
from models.grammar import GrammarLesson, UserGrammarProgress
from models.user import HskLevel, User
from schemas.content import GrammarLessonDetail, GrammarLessonSummary, XpResponse

router = APIRouter(prefix="/grammar", tags=["grammar"])
FIRST_COMPLETION_XP = 10


async def _completed_ids(db: AsyncSession, user_id: int) -> set[int]:
    rows = await db.execute(
        select(UserGrammarProgress.lesson_id).where(
            UserGrammarProgress.user_id == user_id, UserGrammarProgress.completed.is_(True)
        )
    )
    return set(rows.scalars())


@router.get("/lessons", response_model=list[GrammarLessonSummary])
async def list_lessons(
    hsk_level: Optional[HskLevel] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    q = select(GrammarLesson).order_by(GrammarLesson.hsk_level, GrammarLesson.order_index)
    if hsk_level:
        q = q.where(GrammarLesson.hsk_level == hsk_level)
    lessons = (await db.execute(q)).scalars().all()
    done = await _completed_ids(db, user.id)
    return [
        GrammarLessonSummary.model_validate(l).model_copy(update={"completed": l.id in done})
        for l in lessons
    ]


@router.get("/lessons/{lesson_id}", response_model=GrammarLessonDetail)
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    l = await db.get(GrammarLesson, lesson_id)
    if not l:
        raise HTTPException(404, "Lesson not found")
    done = await _completed_ids(db, user.id)
    return GrammarLessonDetail.model_validate(l).model_copy(update={"completed": l.id in done})


@router.post("/lessons/{lesson_id}/complete", response_model=XpResponse)
async def complete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Mark a lesson complete. XP is awarded only the first time."""
    if not await db.get(GrammarLesson, lesson_id):
        raise HTTPException(404, "Lesson not found")
    prog = (await db.execute(
        select(UserGrammarProgress).where(
            UserGrammarProgress.user_id == user.id, UserGrammarProgress.lesson_id == lesson_id
        )
    )).scalar_one_or_none()

    gained = 0
    if prog is None:
        prog = UserGrammarProgress(user_id=user.id, lesson_id=lesson_id, completed=False)
        db.add(prog)
    if not prog.completed:
        gained = FIRST_COMPLETION_XP
        user.xp += gained
    record_activity(user)
    prog.completed = True
    prog.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return XpResponse(xp_gained=gained, total_xp=user.xp)
