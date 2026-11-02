"""
Disaster Recovery Objectives and SLA Validator.
Validates:
1. Restore duration against Target RTO
2. Backup freshness against Target RPO
3. Configurable recovery objectives integrity
4. Validation execution duration against timeout limits
"""
import time
from typing import List, Optional
from datetime import datetime, timezone

from .models import ValidationCheck, CheckStatus, ErrorCategory


class RecoveryValidator:
    """
    Evaluates disaster recovery SLAs and operational readiness:
    - Restore duration (RTO)
    - Backup freshness (RPO)
    - Configurable recovery objectives
    - Validation execution time
    """

    def __init__(
        self,
        restore_duration_seconds: Optional[float] = None,
        backup_created_at: Optional[datetime | str] = None,
        drill_started_at: Optional[datetime | str] = None,
        target_rto_seconds: float = 300.0,
        target_rpo_minutes: float = 60.0,
        max_validation_seconds: float = 60.0
    ):
        self.restore_duration_seconds = restore_duration_seconds
        self.backup_created_at = self._parse_dt(backup_created_at)
        self.drill_started_at = self._parse_dt(drill_started_at) or datetime.now(timezone.utc)
        self.target_rto_seconds = target_rto_seconds
        self.target_rpo_minutes = target_rpo_minutes
        self.max_validation_seconds = max_validation_seconds

    def run_all_checks(self, validation_start_time: float) -> List[ValidationCheck]:
        """Runs all 4 recovery objective checks."""
        checks: List[ValidationCheck] = []

        checks.append(self.check_restore_duration())
        checks.append(self.check_backup_freshness())
        checks.append(self.check_recovery_objectives())
        checks.append(self.check_validation_execution_time(validation_start_time))

        return checks

    def check_restore_duration(self) -> ValidationCheck:
        """Verifies observed database restore duration is within Target RTO SLA."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        dur = time.perf_counter() - t0

        if self.restore_duration_seconds is None:
            return ValidationCheck(
                check_name="recovery.restore_duration",
                status=CheckStatus.SKIPPED,
                duration=dur,
                observed_value="Not recorded",
                expected_value=f"<= {self.target_rto_seconds:.1f}s",
                error_message="Restore duration was not provided to validator",
                error_category=ErrorCategory.RESTORE_ERROR,
                timestamp=now
            )

        observed = round(self.restore_duration_seconds, 3)
        if observed <= self.target_rto_seconds:
            return ValidationCheck(
                check_name="recovery.restore_duration",
                status=CheckStatus.PASS,
                duration=dur,
                observed_value=f"{observed:.3f}s",
                expected_value=f"<= {self.target_rto_seconds:.1f}s",
                error_message=None,
                error_category=None,
                timestamp=now
            )
        else:
            return ValidationCheck(
                check_name="recovery.restore_duration",
                status=CheckStatus.FAIL,
                duration=dur,
                observed_value=f"{observed:.3f}s",
                expected_value=f"<= {self.target_rto_seconds:.1f}s",
                error_message=f"Restore duration of {observed:.2f}s breached target RTO SLA ({self.target_rto_seconds:.1f}s)",
                error_category=ErrorCategory.TIMEOUT_ERROR,
                timestamp=now
            )

    def check_backup_freshness(self) -> ValidationCheck:
        """Verifies backup timestamp is within Target RPO SLA window."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        dur = time.perf_counter() - t0

        if not self.backup_created_at:
            return ValidationCheck(
                check_name="recovery.backup_freshness",
                status=CheckStatus.SKIPPED,
                duration=dur,
                observed_value="Timestamp unavailable",
                expected_value=f"<= {self.target_rpo_minutes:.1f}m",
                error_message="Backup creation timestamp was not provided to validator",
                error_category=ErrorCategory.BACKUP_ERROR,
                timestamp=now
            )

        # Calculate age in minutes
        delta_seconds = max((self.drill_started_at - self.backup_created_at).total_seconds(), 0.0)
        age_minutes = round(delta_seconds / 60.0, 2)

        if age_minutes <= self.target_rpo_minutes:
            return ValidationCheck(
                check_name="recovery.backup_freshness",
                status=CheckStatus.PASS,
                duration=dur,
                observed_value=f"{age_minutes:.2f}m",
                expected_value=f"<= {self.target_rpo_minutes:.1f}m",
                error_message=None,
                error_category=None,
                timestamp=now
            )
        else:
            return ValidationCheck(
                check_name="recovery.backup_freshness",
                status=CheckStatus.FAIL,
                duration=dur,
                observed_value=f"{age_minutes:.2f}m",
                expected_value=f"<= {self.target_rpo_minutes:.1f}m",
                error_message=f"Backup age of {age_minutes:.1f}m breached target RPO SLA ({self.target_rpo_minutes:.1f}m)",
                error_category=ErrorCategory.BACKUP_ERROR,
                timestamp=now
            )

    def check_recovery_objectives(self) -> ValidationCheck:
        """Verifies configurable recovery objectives (RTO and RPO) are defined and valid."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        dur = time.perf_counter() - t0

        valid_rto = isinstance(self.target_rto_seconds, (int, float)) and self.target_rto_seconds > 0
        valid_rpo = isinstance(self.target_rpo_minutes, (int, float)) and self.target_rpo_minutes > 0

        if valid_rto and valid_rpo:
            return ValidationCheck(
                check_name="recovery.recovery_objectives",
                status=CheckStatus.PASS,
                duration=dur,
                observed_value={"target_rto_seconds": self.target_rto_seconds, "target_rpo_minutes": self.target_rpo_minutes},
                expected_value={"target_rto_seconds": "> 0", "target_rpo_minutes": "> 0"},
                error_message=None,
                error_category=None,
                timestamp=now
            )
        else:
            return ValidationCheck(
                check_name="recovery.recovery_objectives",
                status=CheckStatus.FAIL,
                duration=dur,
                observed_value={"target_rto_seconds": self.target_rto_seconds, "target_rpo_minutes": self.target_rpo_minutes},
                expected_value={"target_rto_seconds": "> 0", "target_rpo_minutes": "> 0"},
                error_message="Configured recovery objectives are invalid (must be positive numbers)",
                error_category=ErrorCategory.BACKUP_ERROR,
                timestamp=now
            )

    def check_validation_execution_time(self, validation_start_time: float) -> ValidationCheck:
        """Verifies the total validation execution time does not exceed timeout threshold."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        elapsed = time.perf_counter() - validation_start_time
        dur = time.perf_counter() - t0

        if elapsed <= self.max_validation_seconds:
            return ValidationCheck(
                check_name="recovery.validation_execution_time",
                status=CheckStatus.PASS,
                duration=dur,
                observed_value=f"{elapsed:.3f}s",
                expected_value=f"<= {self.max_validation_seconds:.1f}s",
                error_message=None,
                error_category=None,
                timestamp=now
            )
        else:
            return ValidationCheck(
                check_name="recovery.validation_execution_time",
                status=CheckStatus.FAIL,
                duration=dur,
                observed_value=f"{elapsed:.3f}s",
                expected_value=f"<= {self.max_validation_seconds:.1f}s",
                error_message=f"Validation execution time of {elapsed:.2f}s exceeded threshold ({self.max_validation_seconds:.1f}s)",
                error_category=ErrorCategory.TIMEOUT_ERROR,
                timestamp=now
            )

    @staticmethod
    def _parse_dt(dt: Optional[datetime | str]) -> Optional[datetime]:
        if dt is None:
            return None
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                return None
        return None
