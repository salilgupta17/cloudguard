"""
ValidationResult Model - CloudGuard Validation Drill Results.
Stores per-check outcomes (schema drift, row count parity, checksum matching, API readiness).
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
try:
    from app.database import Base
except ImportError:
    from ..database import Base


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True)
    test_id = Column(String(36), ForeignKey("recovery_tests.test_id", ondelete="CASCADE"), nullable=False, index=True)
    validation_type = Column(String(64), nullable=False) # DATABASE_SCHEMA, DATA_PARITY, CHECKSUM, API_HEALTH
    passed = Column(Boolean, default=False, nullable=False)
    details_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    recovery_test = relationship("RecoveryTest", back_populates="validation_results")
