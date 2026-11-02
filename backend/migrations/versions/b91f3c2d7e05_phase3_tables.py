"""phase3 tables: user_avatars, lesson_progress, listening_tests, listening_answers, user_band_progress

Revision ID: b91f3c2d7e05
Revises: 27ab5db60bf6
Create Date: 2026-11-03
"""
from alembic import op
import sqlalchemy as sa

revision = 'b91f3c2d7e05'
down_revision = '27ab5db60bf6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_avatars',
        sa.Column('id',         sa.Integer(),     nullable=False),
        sa.Column('user_id',    sa.Integer(),     nullable=False),
        sa.Column('filename',   sa.String(255),   nullable=False),
        sa.Column('mime_type',  sa.String(50),    nullable=False, server_default='image/jpeg'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    op.create_table(
        'lesson_progress',
        sa.Column('id',           sa.Integer(),  nullable=False),
        sa.Column('user_id',      sa.Integer(),  nullable=False),
        sa.Column('lesson_id',    sa.Integer(),  nullable=False),
        sa.Column('completed',    sa.Boolean(),  nullable=False, server_default='false'),
        sa.Column('xp_earned',    sa.Integer(),  nullable=False, server_default='0'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'],   ['users.id'],          ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['course_lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'lesson_id', name='uq_lesson_progress'),
    )

    op.create_table(
        'listening_tests',
        sa.Column('id',            sa.Integer(),  nullable=False),
        sa.Column('user_id',       sa.Integer(),  nullable=False),
        sa.Column('hsk_level',     sa.Enum('HSK1','HSK2','HSK3','HSK4','HSK5','HSK6', name='hsklevel'), nullable=False),
        sa.Column('started_at',    sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at',   sa.DateTime(timezone=True), nullable=True),
        sa.Column('score_percent', sa.Float(),    nullable=True),
        sa.Column('passed',        sa.Boolean(),  nullable=True),
        sa.Column('xp_gained',     sa.Integer(),  nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'listening_answers',
        sa.Column('id',          sa.Integer(),    nullable=False),
        sa.Column('test_id',     sa.Integer(),    nullable=False),
        sa.Column('question_id', sa.String(50),   nullable=False),
        sa.Column('selected',    sa.String(5),    nullable=True),
        sa.Column('correct',     sa.Boolean(),    nullable=True),
        sa.ForeignKeyConstraint(['test_id'], ['listening_tests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'user_band_progress',
        sa.Column('id',             sa.Integer(), nullable=False),
        sa.Column('user_id',        sa.Integer(), nullable=False),
        sa.Column('band',           sa.Integer(), nullable=False),
        sa.Column('status',         sa.Enum('locked','in_progress','completed', name='bandstatus'), nullable=False, server_default='locked'),
        sa.Column('words_mastered', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'band', name='uq_user_band'),
    )


def downgrade() -> None:
    op.drop_table('user_band_progress')
    op.drop_table('listening_answers')
    op.drop_table('listening_tests')
    op.drop_table('lesson_progress')
    op.drop_table('user_avatars')
    op.execute("DROP TYPE IF EXISTS bandstatus")
