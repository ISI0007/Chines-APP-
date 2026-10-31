from sqlalchemy import String, Integer, Text, Float, Enum as SAEnum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from db.database import Base
from models.user import HskLevel


class Word(Base):
    """Core vocabulary entry from CC-CEDICT + HSK lists."""
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    simplified: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    traditional: Mapped[str] = mapped_column(String(20), nullable=True)
    pinyin: Mapped[str] = mapped_column(String(100), nullable=False)       # e.g. "nǐ hǎo"
    pinyin_numeric: Mapped[str] = mapped_column(String(100), nullable=True) # e.g. "ni3 hao3"
    definitions: Mapped[str] = mapped_column(Text, nullable=False)          # JSON array of defs
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel), nullable=True, index=True)
    frequency_rank: Mapped[int] = mapped_column(Integer, nullable=True)
    audio_path: Mapped[str] = mapped_column(String(255), nullable=True)    # relative path
    stroke_order_data: Mapped[str] = mapped_column(Text, nullable=True)    # JSON

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserWordProgress(Base):
    """SRS (Spaced Repetition) state per user per word."""
    __tablename__ = "user_word_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id", ondelete="CASCADE"), index=True)

    # SRS fields (SM-2 algorithm)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_reviewed: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_learned: Mapped[bool] = mapped_column(Boolean, default=False)
