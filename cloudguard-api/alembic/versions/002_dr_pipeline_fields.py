"""Add DR pipeline tracking fields

Revision ID: 002_dr_pipeline_fields
Revises: 001_initial_schema
Create Date: 2026-11-02 19:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_dr_pipeline_fields'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to recovery_tests
    op.add_column('recovery_tests', sa.Column('isolated_target_db', sa.String(length=255), nullable=True))
    op.add_column('recovery_tests', sa.Column('restore_duration_seconds', sa.Float(), nullable=True))
    op.add_column('recovery_tests', sa.Column('logs', sa.Text(), nullable=True))
    op.add_column('recovery_tests', sa.Column('error_details', sa.Text(), nullable=True))
    op.add_column('recovery_tests', sa.Column('cleaned_up', sa.Boolean(), server_default='0', nullable=False))

    # Add columns to backup_metadata
    op.add_column('backup_metadata', sa.Column('source_database', sa.String(length=120), server_default='cloudguard_primary', nullable=False))
    op.add_column('backup_metadata', sa.Column('schema_version', sa.String(length=32), server_default='1.0.0', nullable=False))
    op.add_column('backup_metadata', sa.Column('manifest_json', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('backup_metadata', 'manifest_json')
    op.drop_column('backup_metadata', 'schema_version')
    op.drop_column('backup_metadata', 'source_database')

    op.drop_column('recovery_tests', 'cleaned_up')
    op.drop_column('recovery_tests', 'error_details')
    op.drop_column('recovery_tests', 'logs')
    op.drop_column('recovery_tests', 'restore_duration_seconds')
    op.drop_column('recovery_tests', 'isolated_target_db')
