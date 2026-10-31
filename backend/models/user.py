from sqlalchemy import String, Boolean, Integer, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from db.database import Base
import enum


class HskLevel(str, enum.Enum):
    HSK1 = "HSK1"
    HSK2 = "HSK2"
    HSK3 = "HSK3"
    HSK4 = "HSK4"
    HSK5 = "HSK5"
    HSK6 = "HSK6"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Learning profile
    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel), default=HskLevel.HSK1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships (added in later phases)
    # progress = relationship("UserProgress", back_populates="user")
    # flashcard_sessions = relationship("FlashcardSession", back_populates="user")
