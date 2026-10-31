"""
HSK Mock Test models.
- HskTestQuestion: a single MCQ question
- UserTestAttempt: a full test session with score
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.user import HskLevel


class QuestionType(str, enum.Enum):
    VOCABULARY = "vocabulary"       # Pick the right definition
    PINYIN     = "pinyin"           # Pick the correct pinyin
    FILL_BLANK = "fill_blank"       # Complete a sentence
    LISTENING  = "listening"        # Hear audio, choose answer
    READING    = "reading"          # Read passage, answer question


class HskTestQuestion(Base):
    __tablename__ = "hsk_test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel))
    question_type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType))
    question_text: Mapped[str] = mapped_column(Text)       # The question (Chinese or English)
    option_a: Mapped[str] = mapped_column(String(500))
    option_b: Mapped[str] = mapped_column(String(500))
    option_c: Mapped[str] = mapped_column(String(500))
    option_d: Mapped[str] = mapped_column(String(500))
    correct_option: Mapped[str] = mapped_column(String(1))  # "A" | "B" | "C" | "D"
    explanation: Mapped[str] = mapped_column(Text, default="")
    audio_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    word_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("words.id", ondelete="SET NULL"), nullable=True
    )


class UserTestAttempt(Base):
    __tablename__ = "user_test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel))
    total_questions: Mapped[int] = mapped_column(Integer)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    score_percent: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)  # >= 60% to pass
    answers: Mapped[str] = mapped_column(Text, default="{}")     # JSON {question_id: chosen_option}
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    xp_gained: Mapped[int] = mapped_column(Integer, default=0)
