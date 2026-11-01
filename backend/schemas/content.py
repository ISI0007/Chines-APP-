"""Schemas for reading, grammar and HSK test endpoints."""
import json
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from models.user import HskLevel


# ── Reading ──────────────────────────────────────────────
class ReadingTextSummary(BaseModel):
    id: int
    title: str
    title_pinyin: str
    topic: str
    hsk_level: HskLevel
    word_count: int
    completed: bool = False
    model_config = {"from_attributes": True}


class ReadingTextDetail(ReadingTextSummary):
    content: str
    content_pinyin: str
    translation: str
    audio_path: Optional[str] = None


class ReadingCompleteRequest(BaseModel):
    comprehension_score: Optional[float] = None  # 0-100

    @field_validator("comprehension_score")
    @classmethod
    def _range(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError("comprehension_score must be 0-100")
        return v


class XpResponse(BaseModel):
    xp_gained: int
    total_xp: int


# ── Grammar ──────────────────────────────────────────────
class GrammarExample(BaseModel):
    zh: str
    pinyin: str
    en: str


class GrammarLessonSummary(BaseModel):
    id: int
    title: str
    hsk_level: HskLevel
    pattern: str
    order_index: int
    completed: bool = False
    model_config = {"from_attributes": True}


class GrammarLessonDetail(GrammarLessonSummary):
    explanation: str
    examples: list[GrammarExample]

    @field_validator("examples", mode="before")
    @classmethod
    def _parse(cls, v):
        return json.loads(v) if isinstance(v, str) else v


# ── HSK tests ────────────────────────────────────────────
class TestQuestion(BaseModel):
    """Question shown to the user — correct answer is NOT included."""
    id: int
    section: str = "reading"           # "listening" | "reading" | "writing"
    question_number: int = 0
    question_type: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: Optional[str] = None     # may be absent for 3-choice HSK 1 questions
    audio_path:   Optional[str] = None  # URL for listening questions
    image_url:    Optional[str] = None  # URL for picture+word writing questions
    passage_id:   Optional[str] = None  # groups questions sharing a passage
    passage_text: Optional[str] = None  # the shared passage text (only on first q of group)
    model_config = {"from_attributes": True}


class TestStartResponse(BaseModel):
    attempt_id: int
    hsk_level: HskLevel
    total_questions: int
    questions: list[TestQuestion]
    # HSK 3.0: questions already ordered section → question_number
    # Frontend can group by `section` for a tabbed / sectioned view


class TestSubmitRequest(BaseModel):
    answers: dict[int, str]  # {question_id: "A"|"B"|"C"|"D"}

    @field_validator("answers")
    @classmethod
    def _valid(cls, v):
        for opt in v.values():
            if opt.upper() not in ("A", "B", "C", "D"):
                raise ValueError("each answer must be A, B, C or D")
        return {k: o.upper() for k, o in v.items()}


class QuestionResult(BaseModel):
    question_id: int
    chosen: Optional[str]
    correct: str
    is_correct: bool
    explanation: str


class TestResultResponse(BaseModel):
    attempt_id: int
    total_questions: int
    correct_answers: int
    score_percent: float
    passed: bool
    xp_gained: int
    results: list[QuestionResult]


class TestHistoryItem(BaseModel):
    id: int
    hsk_level: HskLevel
    score_percent: float
    passed: bool
    finished_at: Optional[datetime]
    model_config = {"from_attributes": True}
