"""Initial CloudGuard schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-02 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. recovery_tests
    op.create_table(
        'recovery_tests',
        sa.Column('test_id', sa.String(length=36), nullable=False),
        sa.Column('application_name', sa.String(length=120), nullable=False),
        sa.Column('environment', sa.String(length=64), nullable=False),
        sa.Column('backup_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('test_id')
    )
    op.create_index(op.f('ix_recovery_tests_application_name'), 'recovery_tests', ['application_name'], unique=False)
    op.create_index(op.f('ix_recovery_tests_backup_id'), 'recovery_tests', ['backup_id'], unique=False)
    op.create_index(op.f('ix_recovery_tests_status'), 'recovery_tests', ['status'], unique=False)

    # 2. backup_metadata
    op.create_table(
        'backup_metadata',
        sa.Column('backup_id', sa.String(length=64), nullable=False),
        sa.Column('application_name', sa.String(length=120), nullable=False),
        sa.Column('storage_path', sa.String(length=512), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
        sa.Column('records_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('backup_id')
    )
    op.create_index(op.f('ix_backup_metadata_application_name'), 'backup_metadata', ['application_name'], unique=False)

    # 3. validation_results
    op.create_table(
        'validation_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('test_id', sa.String(length=36), nullable=False),
        sa.Column('validation_type', sa.String(length=64), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('details_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['test_id'], ['recovery_tests.test_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_validation_results_test_id'), 'validation_results', ['test_id'], unique=False)

    # 4. recovery_reports
    op.create_table(
        'recovery_reports',
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('test_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('rto_seconds', sa.Float(), nullable=False),
        sa.Column('rpo_minutes', sa.Float(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['test_id'], ['recovery_tests.test_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('report_id')
    )
    op.create_index(op.f('ix_recovery_reports_test_id'), 'recovery_reports', ['test_id'], unique=True)


def downgrade() -> None:
    op.drop_table('recovery_reports')
    op.drop_table('validation_results')
    op.drop_table('backup_metadata')
    op.drop_table('recovery_tests')
