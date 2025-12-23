"""Initial schema - users, generated_trainings, feedback

Revision ID: 001
Revises:
Create Date: 2024-12-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('goals', sa.Text(), nullable=True),
        sa.Column('contraindications', sa.JSON(), nullable=True),
        sa.Column('preferred_difficulty', sa.Enum('EASY', 'MEDIUM', 'HARD', name='difficultylevel'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create generated_trainings table
    op.create_table(
        'generated_trainings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('input_params', sa.JSON(), nullable=False),
        sa.Column('plan', sa.JSON(), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('prompt_version', sa.String(50), nullable=True),
        sa.Column('retrieved_exercises', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_generated_trainings_id'), 'generated_trainings', ['id'], unique=False)
    op.create_index(op.f('ix_generated_trainings_user_id'), 'generated_trainings', ['user_id'], unique=False)

    # Create feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('training_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('was_too_hard', sa.Integer(), nullable=True),
        sa.Column('was_too_easy', sa.Integer(), nullable=True),
        sa.Column('exercises_liked', sa.JSON(), nullable=True),
        sa.Column('exercises_disliked', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['training_id'], ['generated_trainings.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('training_id')
    )
    op.create_index(op.f('ix_feedback_id'), 'feedback', ['id'], unique=False)
    op.create_index(op.f('ix_feedback_training_id'), 'feedback', ['training_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_feedback_training_id'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_id'), table_name='feedback')
    op.drop_table('feedback')

    op.drop_index(op.f('ix_generated_trainings_user_id'), table_name='generated_trainings')
    op.drop_index(op.f('ix_generated_trainings_id'), table_name='generated_trainings')
    op.drop_table('generated_trainings')

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    op.execute("DROP TYPE IF EXISTS difficultylevel")
