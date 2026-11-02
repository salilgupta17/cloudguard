"""
Validation Engine Models and Check Data Structures.
Defines CheckStatus, ErrorCategory, and the standardized ValidationCheck record.
"""
from enum import Enum
from typing import Optional, Any, Dict, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class ErrorCategory(str, Enum):
    DATABASE_ERROR = "DATABASE_ERROR"
    APPLICATION_ERROR = "APPLICATION_ERROR"
    API_ERROR = "API_ERROR"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"
    BACKUP_ERROR = "BACKUP_ERROR"
    RESTORE_ERROR = "RESTORE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class ValidationCheck(BaseModel):
    check_name: str
    status: CheckStatus
    duration: float  # execution time in seconds
    observed_value: Any
    expected_value: Any
    error_message: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __getitem__(self, item: str) -> Any:
        val = getattr(self, item)
        if isinstance(val, Enum):
            return val.value
        return val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status.value if isinstance(self.status, CheckStatus) else str(self.status),
            "duration": round(self.duration, 4),
            "observed_value": self.observed_value,
            "expected_value": self.expected_value,
            "error_message": self.error_message,
            "error_category": self.error_category.value if self.error_category else None,
            "timestamp": self.timestamp
        }


class ValidationReport(BaseModel):
    test_id: Optional[str] = None
    overall_passed: bool = False
    checks: List[ValidationCheck] = Field(default_factory=list)
    summary_counts: Dict[str, int] = Field(default_factory=dict)
    errors_by_category: Dict[str, List[str]] = Field(default_factory=dict)
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "overall_passed": self.overall_passed,
            "checks": [c.to_dict() for c in self.checks],
            "summary_counts": self.summary_counts,
            "errors_by_category": self.errors_by_category,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_seconds": round(self.total_duration_seconds, 4),
            "database_validation": {
                "passed": all(c.status == CheckStatus.PASS for c in self.checks if c.check_name.startswith("database.")),
                "checks": [c.to_dict() for c in self.checks if c.check_name.startswith("database.")]
            },
            "application_validation": {
                "passed": all(c.status == CheckStatus.PASS for c in self.checks if c.check_name.startswith("application.")),
                "checks": [c.to_dict() for c in self.checks if c.check_name.startswith("application.")]
            },
            "recovery_validation": {
                "passed": all(c.status == CheckStatus.PASS for c in self.checks if c.check_name.startswith("recovery.")),
                "checks": [c.to_dict() for c in self.checks if c.check_name.startswith("recovery.")]
            },
            "findings": [
                f"[{c.error_category.value if c.error_category else 'VALIDATION'}] {c.check_name}: {c.error_message}"
                for c in self.checks if c.status in [CheckStatus.FAIL, CheckStatus.ERROR] and c.error_message
            ]
        }
