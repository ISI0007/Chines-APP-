"""
Phase 3 models: UserAvatar, ListeningTest, ListeningQuestion, LessonProgress, UserBandProgress.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from db.database import Base
from models.user import HskLevel


# ─── Avatar ───────────────────────────────────────────────────────────────────

class UserAvatar(Base):
    __tablename__ = "user_avatars"

    id:        Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id:   Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    filename:  Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), default="image/jpeg")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─── Lesson progress ──────────────────────────────────────────────────────────

class LessonProgress(Base):
    """Tracks which course lessons a user has completed."""
    __tablename__ = "lesson_progress"

    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id:  Mapped[int] = mapped_column(Integer, ForeignKey("course_lessons.id", ondelete="CASCADE"))
    completed:  Mapped[bool] = mapped_column(Boolean, default=False)
    xp_earned:  Mapped[int]  = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress"),)


# ─── Listening test ───────────────────────────────────────────────────────────

class ListeningTest(Base):
    __tablename__ = "listening_tests"

    id:         Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    hsk_level:  Mapped[HskLevel] = mapped_column(SAEnum(HskLevel))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed:     Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    xp_gained:  Mapped[int] = mapped_column(Integer, default=0)

    answers: Mapped[list["ListeningAnswer"]] = relationship("ListeningAnswer", back_populates="test", cascade="all, delete-orphan")


class ListeningAnswer(Base):
    __tablename__ = "listening_answers"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    test_id:     Mapped[int] = mapped_column(Integer, ForeignKey("listening_tests.id", ondelete="CASCADE"))
    question_id: Mapped[str] = mapped_column(String(50))          # references static data key
    selected:    Mapped[str | None] = mapped_column(String(5), nullable=True)   # "A"|"B"|"C"|"D"
    correct:     Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    test: Mapped["ListeningTest"] = relationship("ListeningTest", back_populates="answers")


# ─── HSK band progression ─────────────────────────────────────────────────────

class BandStatus(str, enum.Enum):
    LOCKED      = "locked"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"


class UserBandProgress(Base):
    """One row per (user, hsk_band 1-9). Created on first access."""
    __tablename__ = "user_band_progress"

    id:              Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id:         Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    band:            Mapped[int] = mapped_column(Integer)   # 1-9
    status:          Mapped[BandStatus] = mapped_column(SAEnum(BandStatus), default=BandStatus.LOCKED)
    words_mastered:  Mapped[int] = mapped_column(Integer, default=0)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (UniqueConstraint("user_id", "band", name="uq_user_band"),)
