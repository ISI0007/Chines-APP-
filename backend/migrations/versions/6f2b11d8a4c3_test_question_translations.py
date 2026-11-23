"""store per-locale test prompts and Chinese sentence text"""
from alembic import op
import sqlalchemy as sa

revision = "6f2b11d8a4c3"
down_revision = "5c91e8a247bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_language", sa.String(length=16), nullable=False, server_default="en"))
    op.add_column("hsk_test_questions", sa.Column("translations", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("hsk_test_questions", sa.Column("sentence_zh", sa.Text(), nullable=True))
    op.add_column("hsk_test_questions", sa.Column("sentence_pinyin", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("hsk_test_questions", "sentence_pinyin")
    op.drop_column("hsk_test_questions", "sentence_zh")
    op.drop_column("hsk_test_questions", "translations")
    op.drop_column("users", "preferred_language")
