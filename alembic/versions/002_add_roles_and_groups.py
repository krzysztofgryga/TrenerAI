"""Add role system - trainers, clients, groups

Revision ID: 002
Revises: 001
Create Date: 2024-12-26

Changes:
- Add password_hash, role, is_active to users
- Remove physical data from users (moved to client_profiles)
- Create client_profiles table
- Create trainer_clients table
- Create groups table
- Create group_members table
- Add created_by_id, group_id to generated_trainings
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create UserRole enum
    op.execute("CREATE TYPE userrole AS ENUM ('trainer', 'client')")

    # Add new columns to users table
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('role', sa.Enum('trainer', 'client', name='userrole'), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))

    # Set default values for existing users
    op.execute("UPDATE users SET role = 'client' WHERE role IS NULL")
    op.execute("UPDATE users SET password_hash = 'CHANGE_ME' WHERE password_hash IS NULL")
    op.execute("UPDATE users SET name = email WHERE name IS NULL")

    # Make columns non-nullable
    op.alter_column('users', 'password_hash', nullable=False)
    op.alter_column('users', 'role', nullable=False)
    op.alter_column('users', 'name', nullable=False)

    # Create client_profiles table
    op.create_table(
        'client_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('goals', sa.Text(), nullable=True),
        sa.Column('contraindications', sa.JSON(), nullable=True),
        sa.Column('preferred_difficulty', sa.Enum('EASY', 'MEDIUM', 'HARD', name='difficultylevel'), nullable=True),
        sa.Column('trainer_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_client_profiles_id'), 'client_profiles', ['id'], unique=False)

    # Migrate existing user data to client_profiles
    op.execute("""
        INSERT INTO client_profiles (user_id, age, weight, height, goals, contraindications, preferred_difficulty, created_at, updated_at)
        SELECT id, age, weight, height, goals, contraindications, preferred_difficulty, created_at, updated_at
        FROM users
        WHERE age IS NOT NULL OR weight IS NOT NULL OR height IS NOT NULL OR goals IS NOT NULL
    """)

    # Create trainer_clients table
    op.create_table(
        'trainer_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('can_generate_training', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('can_view_history', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trainer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['client_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trainer_clients_id'), 'trainer_clients', ['id'], unique=False)
    op.create_index(op.f('ix_trainer_clients_trainer_id'), 'trainer_clients', ['trainer_id'], unique=False)
    op.create_index(op.f('ix_trainer_clients_client_id'), 'trainer_clients', ['client_id'], unique=False)

    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['trainer_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groups_id'), 'groups', ['id'], unique=False)
    op.create_index(op.f('ix_groups_trainer_id'), 'groups', ['trainer_id'], unique=False)

    # Create group_members table
    op.create_table(
        'group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
        sa.ForeignKeyConstraint(['client_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_members_id'), 'group_members', ['id'], unique=False)
    op.create_index(op.f('ix_group_members_group_id'), 'group_members', ['group_id'], unique=False)
    op.create_index(op.f('ix_group_members_client_id'), 'group_members', ['client_id'], unique=False)

    # Add new columns to generated_trainings
    op.add_column('generated_trainings', sa.Column('created_by_id', sa.Integer(), nullable=True))
    op.add_column('generated_trainings', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_training_created_by', 'generated_trainings', 'users', ['created_by_id'], ['id'])
    op.create_foreign_key('fk_training_group', 'generated_trainings', 'groups', ['group_id'], ['id'])
    op.create_index(op.f('ix_generated_trainings_created_by_id'), 'generated_trainings', ['created_by_id'], unique=False)
    op.create_index(op.f('ix_generated_trainings_group_id'), 'generated_trainings', ['group_id'], unique=False)

    # Drop old columns from users (data already migrated to client_profiles)
    op.drop_column('users', 'age')
    op.drop_column('users', 'weight')
    op.drop_column('users', 'height')
    op.drop_column('users', 'goals')
    op.drop_column('users', 'contraindications')
    op.drop_column('users', 'preferred_difficulty')


def downgrade() -> None:
    # Add back old columns to users
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('weight', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('height', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('goals', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('contraindications', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('preferred_difficulty', sa.Enum('EASY', 'MEDIUM', 'HARD', name='difficultylevel'), nullable=True))

    # Migrate data back from client_profiles
    op.execute("""
        UPDATE users u
        SET age = cp.age, weight = cp.weight, height = cp.height,
            goals = cp.goals, contraindications = cp.contraindications,
            preferred_difficulty = cp.preferred_difficulty
        FROM client_profiles cp
        WHERE u.id = cp.user_id
    """)

    # Drop new columns from generated_trainings
    op.drop_index(op.f('ix_generated_trainings_group_id'), table_name='generated_trainings')
    op.drop_index(op.f('ix_generated_trainings_created_by_id'), table_name='generated_trainings')
    op.drop_constraint('fk_training_group', 'generated_trainings', type_='foreignkey')
    op.drop_constraint('fk_training_created_by', 'generated_trainings', type_='foreignkey')
    op.drop_column('generated_trainings', 'group_id')
    op.drop_column('generated_trainings', 'created_by_id')

    # Drop group_members table
    op.drop_index(op.f('ix_group_members_client_id'), table_name='group_members')
    op.drop_index(op.f('ix_group_members_group_id'), table_name='group_members')
    op.drop_index(op.f('ix_group_members_id'), table_name='group_members')
    op.drop_table('group_members')

    # Drop groups table
    op.drop_index(op.f('ix_groups_trainer_id'), table_name='groups')
    op.drop_index(op.f('ix_groups_id'), table_name='groups')
    op.drop_table('groups')

    # Drop trainer_clients table
    op.drop_index(op.f('ix_trainer_clients_client_id'), table_name='trainer_clients')
    op.drop_index(op.f('ix_trainer_clients_trainer_id'), table_name='trainer_clients')
    op.drop_index(op.f('ix_trainer_clients_id'), table_name='trainer_clients')
    op.drop_table('trainer_clients')

    # Drop client_profiles table
    op.drop_index(op.f('ix_client_profiles_id'), table_name='client_profiles')
    op.drop_table('client_profiles')

    # Remove new columns from users
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'role')
    op.drop_column('users', 'password_hash')

    # Make name nullable again
    op.alter_column('users', 'name', nullable=True)

    # Drop UserRole enum
    op.execute("DROP TYPE IF EXISTS userrole")
