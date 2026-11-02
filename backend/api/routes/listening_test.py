"""
HSK Listening test endpoints.

GET  /api/v1/listening-test/{hsk_level}          — start / retrieve a test session
POST /api/v1/listening-test/{test_id}/submit     — submit answers + get results
GET  /api/v1/listening-test/history              — past attempts for current user

Questions are loaded from backend/data/listening/hsk{N}_listening.json.
Each question has an optional audio_url (null = text-only until native audio is added).
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.phase3 import ListeningAnswer, ListeningTest
from models.user import HskLevel, User

router = APIRouter(prefix="/listening-test", tags=["listening-test"])

DATA_DIR  = Path(__file__).resolve().parents[2] / "data" / "listening"
XP_PASS   = 30
XP_FAIL   = 5
PASS_PCT  = 60.0   # 60 % or above = pass


# ── Load question bank ────────────────────────────────────────────────────────

def _load_questions(hsk_level: str) -> list[dict]:
    path = DATA_DIR / f"{hsk_level.lower()}_listening.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class QuestionOption(BaseModel):
    key:  str
    text: str


class ListeningQuestion(BaseModel):
    id:                  str
    audio_url:           Optional[str]
    question_text:       str
    question_text_pinyin: str
    options:             list[QuestionOption]


class ListeningTestSession(BaseModel):
    test_id:   int
    hsk_level: str
    questions: list[ListeningQuestion]


class AnswerSubmit(BaseModel):
    question_id:     str
    selected_option: str   # "A" | "B" | "C" | "D"


class SubmitRequest(BaseModel):
    answers: list[AnswerSubmit]


class QuestionResult(BaseModel):
    question_id:    str
    selected:       Optional[str]
    correct_option: str
    is_correct:     bool
    explanation:    str


class ListeningResult(BaseModel):
    test_id:         int
    total_questions: int
    correct_answers: int
    score_percent:   float
    passed:          bool
    xp_gained:       int
    results:         list[QuestionResult]


class TestHistoryItem(BaseModel):
    id:            int
    hsk_level:     str
    score_percent: Optional[float]
    passed:        Optional[bool]
    started_at:    str
    finished_at:   Optional[str]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/{hsk_level}", response_model=ListeningTestSession)
async def start_listening_test(
    hsk_level: str,
    num_questions: int = Query(5, ge=1, le=20),
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Create a new listening test session for the given HSK level.

    Returns the test ID and a (shuffled) sample of questions.
    Audio URLs are null until native audio files are loaded.
    """
    try:
        lvl = HskLevel(hsk_level.upper())
    except ValueError:
        raise HTTPException(400, f"Unknown hsk_level '{hsk_level}'")

    bank = _load_questions(lvl.value)
    if not bank:
        raise HTTPException(404, f"No listening questions found for {lvl.value}. Add them to data/listening/{lvl.value.lower()}_listening.json")

    sample = random.sample(bank, min(num_questions, len(bank)))

    # Persist test record
    test = ListeningTest(user_id=user.id, hsk_level=lvl)
    db.add(test)
    await db.flush()   # get test.id

    questions = [
        ListeningQuestion(
            id=q["id"],
            audio_url=q.get("audio_url"),
            question_text=q["question_text"],
            question_text_pinyin=q.get("question_text_pinyin", ""),
            options=[QuestionOption(**opt) for opt in q["options"]],
        )
        for q in sample
    ]

    await db.commit()
    return ListeningTestSession(test_id=test.id, hsk_level=lvl.value, questions=questions)


@router.post("/{test_id}/submit", response_model=ListeningResult)
async def submit_listening_test(
    test_id: int = PathParam(..., description="test_id from the session response"),
    body: SubmitRequest = ...,
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """
    Submit answers for a listening test.

    - Scores each answer against the question bank.
    - Awards XP (30 on pass, 5 on fail).
    - Returns per-question results and overall score.
    """
    result = await db.execute(
        select(ListeningTest).where(
            ListeningTest.id == test_id,
            ListeningTest.user_id == user.id,
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(404, "Test not found")
    if test.finished_at is not None:
        raise HTTPException(409, "Test already submitted")

    # Load full question bank for this level to get correct answers + explanations
    bank = {q["id"]: q for q in _load_questions(test.hsk_level.value)}

    results: list[QuestionResult] = []
    correct_count = 0

    for ans in body.answers:
        q_data = bank.get(ans.question_id)
        if not q_data:
            continue   # unknown question id — skip gracefully
        is_correct = (ans.selected_option.upper() == q_data["correct_option"].upper())
        if is_correct:
            correct_count += 1
        results.append(QuestionResult(
            question_id=ans.question_id,
            selected=ans.selected_option,
            correct_option=q_data["correct_option"],
            is_correct=is_correct,
            explanation=q_data.get("explanation", ""),
        ))
        # Persist individual answer
        db.add(ListeningAnswer(
            test_id=test.id,
            question_id=ans.question_id,
            selected=ans.selected_option,
            correct=is_correct,
        ))

    total    = len(results)
    pct      = round((correct_count / total) * 100, 1) if total else 0.0
    passed   = pct >= PASS_PCT
    xp       = XP_PASS if passed else XP_FAIL

    test.finished_at   = datetime.now(timezone.utc)
    test.score_percent = pct
    test.passed        = passed
    test.xp_gained     = xp
    user.xp = (user.xp or 0) + xp

    await db.commit()

    return ListeningResult(
        test_id=test.id,
        total_questions=total,
        correct_answers=correct_count,
        score_percent=pct,
        passed=passed,
        xp_gained=xp,
        results=results,
    )


@router.get("/history", response_model=list[TestHistoryItem])
async def listening_test_history(
    limit: int = Query(20, ge=1, le=100),
    db:    AsyncSession = Depends(get_db),
    user:  User = Depends(current_user),
):
    """Return the current user's listening test history, newest first."""
    result = await db.execute(
        select(ListeningTest)
        .where(ListeningTest.user_id == user.id)
        .order_by(ListeningTest.started_at.desc())
        .limit(limit)
    )
    tests = result.scalars().all()
    return [
        TestHistoryItem(
            id=t.id,
            hsk_level=t.hsk_level.value,
            score_percent=t.score_percent,
            passed=t.passed,
            started_at=t.started_at.isoformat(),
            finished_at=t.finished_at.isoformat() if t.finished_at else None,
        )
        for t in tests
    ]
