"""
RecoveryReport Model - CloudGuard Disaster Recovery Executive Report.
Captures RTO (seconds), RPO (minutes), status, and executive summary.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
try:
    from app.database import Base
except ImportError:
    from ..database import Base


class RecoveryReport(Base):
    __tablename__ = "recovery_reports"

    report_id = Column(String(36), primary_key=True)
    test_id = Column(String(36), ForeignKey("recovery_tests.test_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status = Column(String(32), default="PASSED", nullable=False) # PASSED, DEGRADED, FAILED
    rto_seconds = Column(Float, default=0.0, nullable=False)
    rpo_minutes = Column(Float, default=0.0, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    recovery_test = relationship("RecoveryTest", back_populates="recovery_report")
