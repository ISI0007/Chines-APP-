"""HSK mock tests: start -> submit -> history. Correct answers are never sent before submit."""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from db.database import get_db
from models.hsk_test import HskTestQuestion, UserTestAttempt
from models.user import HskLevel, User
from schemas.content import (
    QuestionResult, TestHistoryItem, TestQuestion, TestResultResponse,
    TestStartResponse, TestSubmitRequest,
)

router = APIRouter(prefix="/tests", tags=["tests"])
PASS_PERCENT = 60.0
XP_PER_CORRECT = 2
PASS_BONUS_XP = 20


@router.post("/start", response_model=TestStartResponse)
async def start_test(
    hsk_level: HskLevel,
    num_questions: int = Query(20, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    questions = (await db.execute(
        select(HskTestQuestion)
        .where(HskTestQuestion.hsk_level == hsk_level)
        .order_by(func.random())
        .limit(num_questions)
    )).scalars().all()
    if not questions:
        raise HTTPException(404, f"No questions available for {hsk_level.value}")

    attempt = UserTestAttempt(
        user_id=user.id, hsk_level=hsk_level, total_questions=len(questions),
        correct_answers=0, score_percent=0.0, passed=False, xp_gained=0,
        answers=json.dumps({"question_ids": [q.id for q in questions]}),
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return TestStartResponse(
        attempt_id=attempt.id, hsk_level=hsk_level, total_questions=len(questions),
        questions=[TestQuestion.model_validate(q) for q in questions],
    )


@router.post("/{attempt_id}/submit", response_model=TestResultResponse)
async def submit_test(
    attempt_id: int,
    body: TestSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    attempt = await db.get(UserTestAttempt, attempt_id)
    if not attempt or attempt.user_id != user.id:
        raise HTTPException(404, "Attempt not found")
    if attempt.finished_at is not None:
        raise HTTPException(409, "This attempt was already submitted")

    stored = json.loads(attempt.answers)
    qids: list[int] = stored["question_ids"]
    questions = {
        q.id: q for q in (await db.execute(
            select(HskTestQuestion).where(HskTestQuestion.id.in_(qids))
        )).scalars()
    }

    results, correct = [], 0
    for qid in qids:
        q = questions.get(qid)
        if q is None:
            continue
        chosen = body.answers.get(qid)
        ok = chosen == q.correct_option
        correct += ok
        results.append(QuestionResult(
            question_id=qid, chosen=chosen, correct=q.correct_option,
            is_correct=ok, explanation=q.explanation,
        ))

    total = attempt.total_questions
    score = round(correct / total * 100, 1) if total else 0.0
    passed = score >= PASS_PERCENT
    xp = correct * XP_PER_CORRECT + (PASS_BONUS_XP if passed else 0)

    attempt.correct_answers = correct
    attempt.score_percent = score
    attempt.passed = passed
    attempt.xp_gained = xp
    attempt.finished_at = datetime.now(timezone.utc)
    attempt.answers = json.dumps({"question_ids": qids, "answers": {str(k): v for k, v in body.answers.items()}})
    user.xp += xp
    await db.commit()

    return TestResultResponse(
        attempt_id=attempt.id, total_questions=total, correct_answers=correct,
        score_percent=score, passed=passed, xp_gained=xp, results=results,
    )


@router.get("/history", response_model=list[TestHistoryItem])
async def history(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    rows = await db.execute(
        select(UserTestAttempt)
        .where(UserTestAttempt.user_id == user.id, UserTestAttempt.finished_at.is_not(None))
        .order_by(UserTestAttempt.finished_at.desc())
        .limit(limit)
    )
    return rows.scalars().all()
