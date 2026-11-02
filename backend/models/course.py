"""
Course lesson model for HSK Standard Course (标准教程).

Each row represents one lesson in one book (textbook or workbook) at one level.
Audio track metadata is stored as a JSON array in `audio_tracks`.
Answer key references are page-level pointers into the answer PDFs.

Audio tracks JSON shape (per element):
  {
    "section":    "new_words" | "dialogue_1" | "dialogue_2" | "listening" | "exercise",
    "track":      "01.mp3",           # filename relative to audio_extracted/
    "label":      "New Words",        # display label
    "duration_s": 45                  # seconds (filled by manifest builder)
  }
"""
import enum
from sqlalchemy import String, Text, Integer, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base
from models.user import HskLevel


class CourseBook(str, enum.Enum):
    TEXTBOOK = "textbook"
    WORKBOOK = "workbook"


class CourseLesson(Base):
    __tablename__ = "course_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    hsk_level: Mapped[HskLevel] = mapped_column(SAEnum(HskLevel))
    book:       Mapped[CourseBook] = mapped_column(SAEnum(CourseBook), default=CourseBook.TEXTBOOK)

    # e.g. "HSK1" has lessons 1–15; "HSK4A" / "HSK4B" have lessons 1–10 each
    volume:        Mapped[str] = mapped_column(String(10), default="")  # "A" | "B" | ""
    lesson_number: Mapped[int] = mapped_column(Integer)

    title_zh: Mapped[str] = mapped_column(String(200), default="")   # 第1课 你好
    title_en: Mapped[str] = mapped_column(String(200), default="")   # Hello
    topic:    Mapped[str] = mapped_column(String(100), default="")   # greetings | family | …

    # JSON array of audio track metadata (see module docstring)
    audio_tracks: Mapped[str] = mapped_column(Text, default="[]")

    # Answer key reference for workbook/exercise answers
    # Points to a page in answer_keys/hsk{level}{volume}_answers.pdf
    answer_key_pdf:   Mapped[str | None] = mapped_column(String(200), nullable=True)
    answer_key_pages: Mapped[str] = mapped_column(String(50), default="")  # "12-13"

    has_audio: Mapped[bool] = mapped_column(Boolean, default=False)
