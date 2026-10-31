"""
Grammar lesson models.
"""

from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.user import HskLevel


class GrammarLesson(Base):
    __tablename__ = "grammar_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel))
    pattern: Mapped[str] = mapped_column(String(300))      # e.g. "Subject + 是 + Object"
    explanation: Mapped[str] = mapped_column(Text)          # English explanation
    examples: Mapped[str] = mapped_column(Text)             # JSON array of {zh, pinyin, en}
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    progress: Mapped[list["UserGrammarProgress"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class UserGrammarProgress(Base):
    __tablename__ = "user_grammar_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("grammar_lessons.id", ondelete="CASCADE"))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lesson: Mapped["GrammarLesson"] = relationship(back_populates="progress")
