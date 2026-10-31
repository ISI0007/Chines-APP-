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
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _ADDITIVE_DDL:
            await conn.execute(text(stmt))
