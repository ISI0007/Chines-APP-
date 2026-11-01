"""
HSK Mock Test models — HSK 3.0 format (9 levels, 3 sections).
- HskTestQuestion: one MCQ question with optional audio / passage / image
- UserTestAttempt: a full test session with score
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base
from models.user import HskLevel


class QuestionType(str, enum.Enum):
    VOCABULARY = "vocabulary"   # Pick the right definition / translation
    PINYIN     = "pinyin"       # Pick the correct pinyin
    FILL_BLANK = "fill_blank"   # Complete a sentence (choose the missing word)
    LISTENING  = "listening"    # Audio clip → choose answer
    READING    = "reading"      # Passage or sentence → comprehension question
    WRITING    = "writing"      # Rearrange / identify characters / pinyin→hanzi


class TestSection(str, enum.Enum):
    """HSK 3.0 exam section.  Questions are always returned in section order."""
    LISTENING = "listening"
    READING   = "reading"
    WRITING   = "writing"


class HskTestQuestion(Base):
    """
    One MCQ question for an HSK 3.0 mock test.

    HSK 3.0-specific additions:
    - section          : which part of the exam this belongs to
    - passage_id       : groups questions that share the same reading / listening passage
    - passage_text     : the shared text shown above all questions in this group (null = standalone)
    - audio_path       : relative URL to an MP3/WAV clip for listening questions
    - image_url        : relative URL to an image for writing picture+word tasks
    - question_number  : ordering within the section (mirrors real exam numbering)
    """
    __tablename__ = "hsk_test_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel))

    # HSK 3.0 section
    section: Mapped[TestSection] = mapped_column(
        SAEnum(TestSection), nullable=False, default=TestSection.READING
    )
    question_number: Mapped[int] = mapped_column(Integer, default=0)  # order in exam

    question_type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType))
    question_text: Mapped[str] = mapped_column(Text)       # the question stem

    # Answer choices
    option_a: Mapped[str] = mapped_column(String(500))
    option_b: Mapped[str] = mapped_column(String(500))
    option_c: Mapped[str] = mapped_column(String(500))
    option_d: Mapped[str | None] = mapped_column(String(500), nullable=True)  # L1/L2 may use A-C only
    correct_option: Mapped[str] = mapped_column(String(1))   # "A" | "B" | "C" | "D"
    explanation: Mapped[str] = mapped_column(Text, default="")

    # Media / passage
    audio_path:   Mapped[str | None] = mapped_column(String(400), nullable=True)  # /audio/tests/hsk1/q01.mp3
    image_url:    Mapped[str | None] = mapped_column(String(400), nullable=True)  # picture+word writing
    passage_id:   Mapped[str | None] = mapped_column(String(80),  nullable=True)  # e.g. "hsk3-r1"
    passage_text: Mapped[str | None] = mapped_column(Text,        nullable=True)  # shared reading text

    # Optional link back to the vocabulary word this question is about
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
