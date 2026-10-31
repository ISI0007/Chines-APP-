"""
Vocabulary routes — HSK word listing, lookup, search, and SRS review.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.user import HskLevel, User
from models.vocabulary import Word, UserWordProgress
from schemas.vocabulary import (
    WordResponse,
    WordListResponse,
    UserWordProgressResponse,
    ReviewRequest,
    ReviewResponse,
)
from services.srs_service import sm2_update

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


# ──────────────────────────────────────────────
# GET /words  — paginated word list with optional HSK level filter
# ──────────────────────────────────────────────
@router.get("/words", response_model=WordListResponse)
async def list_words(
    hsk_level: Optional[HskLevel] = None,
    search: Optional[str] = Query(None, max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    List vocabulary words with optional filters.

    Query params:
    - hsk_level: HSK1 | HSK2 | HSK3 | HSK4 | HSK5 | HSK6
    - search: full-text search across simplified, pinyin, definitions
    - skip / limit: pagination
    """
    q = select(Word)

    if hsk_level:
        q = q.where(Word.hsk_level == hsk_level)

    if search:
        pattern = f"%{search}%"
        q = q.where(
            or_(
                Word.simplified.ilike(pattern),
                Word.pinyin.ilike(pattern),
                Word.definitions.ilike(pattern),
            )
        )

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar_one()

    q = q.order_by(Word.hsk_level.asc(), Word.frequency_rank.asc().nulls_last(), Word.id.asc()).offset(skip).limit(limit)
    words = (await db.execute(q)).scalars().all()

    return WordListResponse(total=total, skip=skip, limit=limit, words=words)


# ──────────────────────────────────────────────
# GET /words/{word_id}  — single word detail
# ──────────────────────────────────────────────
@router.get("/words/{word_id}", response_model=WordResponse)
async def get_word(
    word_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    word = await db.get(Word, word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")
    return word


# ──────────────────────────────────────────────
# GET /review  — words due for SRS review (SM-2)
# ──────────────────────────────────────────────
@router.get("/review", response_model=list[WordResponse])
async def get_due_reviews(
    hsk_level: Optional[HskLevel] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Return words whose next_review is <= now (due for SRS review).
    New words (no progress entry yet) are included up to the limit.
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    # Words with existing progress that are due
    due_q = (
        select(Word)
        .join(UserWordProgress, and_(
            UserWordProgress.word_id == Word.id,
            UserWordProgress.user_id == user.id,
            UserWordProgress.next_review <= now,
        ))
    )
    if hsk_level:
        due_q = due_q.where(Word.hsk_level == hsk_level)
    due_q = due_q.limit(limit)
    due_words = list((await db.execute(due_q)).scalars().all())

    # Fill remaining slots with brand-new words
    remaining = limit - len(due_words)
    if remaining > 0:
        seen_ids = [w.id for w in due_words]
        # Subquery: words this user already has progress for
        has_progress = select(UserWordProgress.word_id).where(
            UserWordProgress.user_id == user.id
        )
        new_q = select(Word).where(Word.id.not_in(has_progress))
        if seen_ids:
            new_q = new_q.where(Word.id.not_in(seen_ids))
        if hsk_level:
            new_q = new_q.where(Word.hsk_level == hsk_level)
        new_q = new_q.order_by(Word.hsk_level.asc(), Word.frequency_rank.asc().nulls_last(), Word.id.asc()).limit(remaining)
        new_words = list((await db.execute(new_q)).scalars().all())
        due_words.extend(new_words)

    return due_words


# ──────────────────────────────────────────────
# POST /review  — submit an SRS review answer
# ──────────────────────────────────────────────
@router.post("/review", response_model=ReviewResponse)
async def submit_review(
    body: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Submit a flashcard review result.
    quality: 0-5 (SM-2 scale: 0=blackout, 3=correct w/ difficulty, 5=perfect)
    """
    word = await db.get(Word, body.word_id)
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    # Get or create progress record
    result = await db.execute(
        select(UserWordProgress).where(
            UserWordProgress.user_id == user.id,
            UserWordProgress.word_id == body.word_id,
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # Column defaults only apply at flush, so set SM-2 start values explicitly.
        progress = UserWordProgress(
            user_id=user.id, word_id=body.word_id,
            ease_factor=2.5, interval_days=1, repetitions=0, is_learned=False,
        )
        db.add(progress)

    # Apply SM-2 algorithm
    progress = sm2_update(progress, body.quality)
    await db.commit()
    await db.refresh(progress)

    # Award XP
    xp_gained = 5 if body.quality >= 3 else 1
    user.xp += xp_gained
    await db.commit()

    return ReviewResponse(
        word_id=body.word_id,
        next_review=progress.next_review,
        interval_days=progress.interval_days,
        ease_factor=progress.ease_factor,
        is_learned=progress.is_learned,
        xp_gained=xp_gained,
    )


# ──────────────────────────────────────────────
# GET /progress  — user's learning progress summary
# ──────────────────────────────────────────────
@router.get("/progress")
async def get_progress(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Return aggregate SRS progress per HSK level."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    levels = {}
    for level in HskLevel:
        total_q = select(func.count(Word.id)).where(Word.hsk_level == level)
        total = (await db.execute(total_q)).scalar_one()

        learned_q = (
            select(func.count(UserWordProgress.id))
            .where(
                UserWordProgress.user_id == user.id,
                UserWordProgress.is_learned == True,
            )
            .join(Word, and_(Word.id == UserWordProgress.word_id, Word.hsk_level == level))
        )
        learned = (await db.execute(learned_q)).scalar_one()

        due_q = (
            select(func.count(UserWordProgress.id))
            .where(
                UserWordProgress.user_id == user.id,
                UserWordProgress.next_review <= now,
            )
            .join(Word, and_(Word.id == UserWordProgress.word_id, Word.hsk_level == level))
        )
        due = (await db.execute(due_q)).scalar_one()

        levels[level.value] = {"total": total, "learned": learned, "due_for_review": due}

    return {
        "user_xp": user.xp,
        "streak_days": user.streak_days,
        "levels": levels,
    }
