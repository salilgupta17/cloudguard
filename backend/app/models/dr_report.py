"""
CloudGuard Disaster Recovery Audit, Backup, and Test Execution Models.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TimestampMixin


class DRBackupRecord(Base, TimestampMixin):
    __tablename__ = "cg_backup_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_mode: Mapped[str] = mapped_column(String(16), default="LOCAL", nullable=False) # LOCAL or AWS
    backup_type: Mapped[str] = mapped_column(String(32), default="FULL_SNAPSHOT", nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(16), default="LOCAL", nullable=False) # LOCAL or S3
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tables_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="AVAILABLE", nullable=False) # AVAILABLE, CORRUPTED, EXPIRED
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)


class DRRestoreTestRun(Base, TimestampMixin):
    __tablename__ = "cg_restore_test_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    backup_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(16), default="LOCAL", nullable=False)
    isolated_target_db: Mapped[str] = mapped_column(String(255), nullable=False)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rto_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_rpo_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sla_rto_met: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sla_rpo_met: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    status: Mapped[str] = mapped_column(String(32), default="PASSED", nullable=False) # PASSED, FAILED, DEGRADED
    verification_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)


class DRVerificationDetail(Base, TimestampMixin):
    __tablename__ = "cg_verification_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    test_run_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    table_name: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    restored_row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count_matched: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    checksum_matched: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    schema_matched: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    foreign_keys_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
