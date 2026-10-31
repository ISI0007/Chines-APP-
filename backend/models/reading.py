"""
Reading module models.
- ReadingText: a graded Chinese passage
- UserReadingProgress: tracks which texts a user has read + comprehension score
"""

from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.user import HskLevel


class ReadingText(Base):
    __tablename__ = "reading_texts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    title_pinyin: Mapped[str] = mapped_column(String(300), default="")
    content: Mapped[str] = mapped_column(Text)           # Chinese text
    content_pinyin: Mapped[str] = mapped_column(Text, default="")  # pinyin per char
    translation: Mapped[str] = mapped_column(Text, default="")     # English translation
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel))
    topic: Mapped[str] = mapped_column(String(100), default="")    # e.g. "Daily Life"
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    audio_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    progress: Mapped[list["UserReadingProgress"]] = relationship(
        back_populates="text", cascade="all, delete-orphan"
    )


class UserReadingProgress(Base):
    __tablename__ = "user_reading_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    text_id: Mapped[int] = mapped_column(Integer, ForeignKey("reading_texts.id", ondelete="CASCADE"))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    comprehension_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    text: Mapped["ReadingText"] = relationship(back_populates="progress")
