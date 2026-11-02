from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

# Convert postgresql:// → postgresql+asyncpg://
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=settings.APP_ENV == "development")
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Idempotent, additive-only DDL so databases created by an earlier create_all pick up new columns
# on startup. For anything beyond adding a nullable column, use a real Alembic migration (see
# backend/migrations/). create_all never alters an existing table, which is why this exists.
_ADDITIVE_DDL = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active_on DATE",
    # HSK 3.0 test question columns (added 2026-11)
    "ALTER TABLE hsk_test_questions ADD COLUMN IF NOT EXISTS section VARCHAR(20) DEFAULT 'reading'",
    "ALTER TABLE hsk_test_questions ADD COLUMN IF NOT EXISTS question_number INTEGER DEFAULT 0",
    "ALTER TABLE hsk_test_questions ADD COLUMN IF NOT EXISTS image_url VARCHAR(400)",
    "ALTER TABLE hsk_test_questions ADD COLUMN IF NOT EXISTS passage_id VARCHAR(80)",
    "ALTER TABLE hsk_test_questions ADD COLUMN IF NOT EXISTS passage_text TEXT",
    # option_d may be null for 3-choice questions (L1)
    "ALTER TABLE hsk_test_questions ALTER COLUMN option_d DROP NOT NULL",
    # CourseLesson table columns (added 2026-11) — table created by create_all, extras here
    "ALTER TABLE course_lessons ADD COLUMN IF NOT EXISTS volume VARCHAR(10) DEFAULT ''",
    "ALTER TABLE course_lessons ADD COLUMN IF NOT EXISTS topic VARCHAR(100) DEFAULT ''",
    "ALTER TABLE course_lessons ADD COLUMN IF NOT EXISTS answer_key_pdf VARCHAR(200)",
    "ALTER TABLE course_lessons ADD COLUMN IF NOT EXISTS answer_key_pages VARCHAR(50) DEFAULT ''",
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _ADDITIVE_DDL:
            await conn.execute(text(stmt))
