# Database migrations (Alembic)

Schema is defined by the SQLAlchemy models; Alembic tracks structured changes.

- **Fresh database:** `alembic upgrade head` (from `backend/`) creates the full schema. The app's
  `init_db()` also runs `create_all` on startup for dev convenience, so a fresh dev DB works either way.
- **A DB created by an earlier `create_all` (no `alembic_version` table):** adopt Alembic with
  `alembic stamp head`, then future migrations apply normally. Additive columns are also self-healed
  at startup by `init_db()` (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`), so this column change needs
  no manual step.
- **New change:** edit the models, then `alembic revision --autogenerate -m "..."`, review the file,
  and `alembic upgrade head`. Use a real migration (not the startup self-heal) for anything beyond
  adding a nullable column.

The DB URL comes from app settings (`DATABASE_URL`), not `alembic.ini`.
