"""
Writing / stroke-order module.

Character curriculum = the official 书写字 (characters a learner must be able to write), by level.
Stroke graphics are rendered on the frontend (hanzi-writer) from the character itself; the backend
owns the curriculum (which characters, in which order, at which level) and the user's practice state.
"""
from datetime import datetime, timezone

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base
from models.user import HskLevel


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    char: Mapped[str] = mapped_column(String(4), unique=True, index=True)   # one hanzi
    pinyin: Mapped[str] = mapped_column(String(30), default="")
    meaning: Mapped[str] = mapped_column(Text, default="[]")                # JSON array of glosses
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel), index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)            # order within the syllabus

    progress: Mapped[list["UserCharacterProgress"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class UserCharacterProgress(Base):
    __tablename__ = "user_character_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    char_id: Mapped[int] = mapped_column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), index=True)
    times_practiced: Mapped[int] = mapped_column(Integer, default=0)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    last_practiced: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    character: Mapped["Character"] = relationship(back_populates="progress")
