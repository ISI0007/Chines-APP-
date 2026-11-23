"""add the combined HSK 7-9 vocabulary band

Revision ID: 5c91e8a247bf
Revises: 27ab5db60bf6
Create Date: 2026-11-22
"""
from alembic import op


revision = "5c91e8a247bf"
down_revision = "27ab5db60bf6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL enums are shared by HSK-level columns. Add the value without
    # rewriting existing learner data or rebuilding related tables.
    # SQLAlchemy persists Enum member names by default (HSK7_9); Pydantic emits
    # the user-facing member value (HSK7-9).
    op.execute("ALTER TYPE hsklevel ADD VALUE IF NOT EXISTS 'HSK7_9'")


def downgrade() -> None:
    # PostgreSQL cannot safely remove an enum label while rows may use it.
    pass
