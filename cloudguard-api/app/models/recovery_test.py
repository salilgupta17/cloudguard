"""
RecoveryTest Model - CloudGuard Core DR Drill Tracker.
Tracks: test_id, application_name, environment, backup_id, status, started_at, completed_at,
restore duration, execution logs, error details, and cleanup state.
"""
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship

try:
    from app.database import Base
except ImportError:
    from ..database import Base

if TYPE_CHECKING:
    from .validation_result import ValidationResult
    from .recovery_report import RecoveryReport


class RecoveryTest(Base):
    __tablename__ = "recovery_tests"

    test_id = Column(String(36), primary_key=True)
    application_name = Column(String(120), nullable=False, index=True)
    environment = Column(String(64), default="production", nullable=False)
    backup_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), default="PENDING", nullable=False, index=True) # PENDING, RUNNING, SUCCESS, FAILED
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # DR Execution Tracking
    isolated_target_db = Column(String(255), nullable=True)
    restore_duration_seconds = Column(Float, nullable=True)
    logs = Column(Text, default="", nullable=True)
    error_details = Column(Text, nullable=True)
    cleaned_up = Column(Boolean, default=False, nullable=False)

    validation_results = relationship("ValidationResult", back_populates="recovery_test", cascade="all, delete-orphan")
    recovery_report = relationship("RecoveryReport", back_populates="recovery_test", uselist=False, cascade="all, delete-orphan")
