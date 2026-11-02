"""
Course lesson progress endpoints (Phase 3).

GET  /api/v1/course/levels               — HSK levels with user completion %
GET  /api/v1/course/units?hsk_level=HSK1 — lessons grouped as 'units' per level
GET  /api/v1/course/lessons/{id}         — existing route in course.py (kept); this adds:
POST /api/v1/course/lessons/{id}/complete — mark lesson done, award XP

Note: lesson detail (GET /course/lessons/{id}) already exists in course.py.
This file adds the /levels, /units, and /complete routes only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.course import CourseBook, CourseLesson
from models.phase3 import LessonProgress
from models.user import HskLevel, User

router = APIRouter(prefix="/course", tags=["course"])

XP_PER_LESSON = 20

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class LevelSummary(BaseModel):
    level: str
    lesson_count: int
    completed_count: int
    completion_pct: float


class LevelsResponse(BaseModel):
    levels: list[LevelSummary]


class LessonItem(BaseModel):
    id: int
    lesson_number: int
    title_zh: str
    title_en: str
    topic: str
    has_audio: bool
    completed: bool


class UnitsResponse(BaseModel):
    hsk_level: str
    lessons: list[LessonItem]


class LessonCompleteResult(BaseModel):
    lesson_id: int
    xp_earned: int
    total_xp: int
    streak_updated: bool
    already_completed: bool


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/levels", response_model=LevelsResponse)
async def get_course_levels(
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Return all HSK levels (1-6) with textbook lesson counts and the current
    user's completion percentage.
    """
    all_levels: list[LevelSummary] = []

    for lvl in HskLevel:
        # Total textbook lessons at this level
        total_result = await db.execute(
            select(func.count()).where(
                CourseLesson.hsk_level == lvl,
                CourseLesson.book == CourseBook.TEXTBOOK,
            )
        )
        total = total_result.scalar() or 0

        if total == 0:
            all_levels.append(LevelSummary(
                level=lvl.value, lesson_count=0, completed_count=0, completion_pct=0.0
            ))
            continue

        # User's completed lessons at this level
        lesson_ids_result = await db.execute(
            select(CourseLesson.id).where(
                CourseLesson.hsk_level == lvl,
                CourseLesson.book == CourseBook.TEXTBOOK,
            )
        )
        lesson_ids = [row[0] for row in lesson_ids_result.all()]

        completed_result = await db.execute(
            select(func.count()).where(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id.in_(lesson_ids),
                LessonProgress.completed == True,
            )
        )
        completed = completed_result.scalar() or 0

        pct = round((completed / total) * 100, 1) if total else 0.0
        all_levels.append(LevelSummary(
            level=lvl.value,
            lesson_count=total,
            completed_count=completed,
            completion_pct=pct,
        ))

    return LevelsResponse(levels=all_levels)


@router.get("/units", response_model=UnitsResponse)
async def get_course_units(
    hsk_level: str = Query(..., description="e.g. HSK1"),
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Return all textbook lessons for a given HSK level, annotated with the
    current user's completion status.
    """
    try:
        lvl = HskLevel(hsk_level.upper())
    except ValueError:
        raise HTTPException(400, f"Unknown hsk_level '{hsk_level}'")

    lessons_result = await db.execute(
        select(CourseLesson)
        .where(CourseLesson.hsk_level == lvl, CourseLesson.book == CourseBook.TEXTBOOK)
        .order_by(CourseLesson.lesson_number)
    )
    lessons = lessons_result.scalars().all()

    if not lessons:
        return UnitsResponse(hsk_level=lvl.value, lessons=[])

    lesson_ids = [l.id for l in lessons]

    # Fetch completed set for this user
    prog_result = await db.execute(
        select(LessonProgress.lesson_id).where(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id.in_(lesson_ids),
            LessonProgress.completed == True,
        )
    )
    completed_ids = {row[0] for row in prog_result.all()}

    items = [
        LessonItem(
            id=l.id,
            lesson_number=l.lesson_number,
            title_zh=l.title_zh,
            title_en=l.title_en,
            topic=l.topic,
            has_audio=l.has_audio,
            completed=(l.id in completed_ids),
        )
        for l in lessons
    ]

    return UnitsResponse(hsk_level=lvl.value, lessons=items)


@router.post("/lessons/{lesson_id}/complete", response_model=LessonCompleteResult)
async def complete_lesson(
    lesson_id: int,
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Mark a course lesson as completed and award XP (idempotent — safe to call
    multiple times; XP is only awarded on the first completion).
    """
    # Validate lesson exists
    lesson_result = await db.execute(
        select(CourseLesson).where(CourseLesson.id == lesson_id)
    )
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(404, "Lesson not found")

    # Find or create progress record
    prog_result = await db.execute(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id == lesson_id,
        )
    )
    prog = prog_result.scalar_one_or_none()

    already_completed = bool(prog and prog.completed)
    xp_earned = 0

    if not already_completed:
        xp_earned = XP_PER_LESSON
        if prog:
            prog.completed    = True
            prog.xp_earned    = xp_earned
            prog.completed_at = datetime.now(timezone.utc)
        else:
            prog = LessonProgress(
                user_id=user.id,
                lesson_id=lesson_id,
                completed=True,
                xp_earned=xp_earned,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(prog)

        user.xp = (user.xp or 0) + xp_earned

    await db.commit()

    return LessonCompleteResult(
        lesson_id=lesson_id,
        xp_earned=xp_earned,
        total_xp=user.xp,
        streak_updated=False,   # streak logic lives in streak_service; hook in later
        already_completed=already_completed,
    )
