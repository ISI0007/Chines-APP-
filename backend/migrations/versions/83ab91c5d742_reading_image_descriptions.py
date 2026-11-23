"""add image descriptions to graded reading texts"""
from alembic import op
import sqlalchemy as sa


revision = "83ab91c5d742"
down_revision = "6f2b11d8a4c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reading_texts", sa.Column("image_description", sa.Text(), nullable=False, server_default=""))
    op.add_column("reading_texts", sa.Column("image_path", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("reading_texts", "image_path")
    op.drop_column("reading_texts", "image_description")
