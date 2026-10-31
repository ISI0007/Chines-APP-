"""Alembic async environment. Reads the DB URL from app settings and all models' metadata."""
import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # import the app package

from core.config import settings  # noqa: E402
from db.database import Base  # noqa: E402
import models.user, models.vocabulary, models.reading, models.grammar, models.hsk_test  # noqa: E401,E402,F401

target_metadata = Base.metadata
URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


def _run(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def _async_run():
    engine = create_async_engine(URL)
    async with engine.connect() as conn:
        await conn.run_sync(_run)
    await engine.dispose()


def run_migrations_offline():
    context.configure(url=URL, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(_async_run())
