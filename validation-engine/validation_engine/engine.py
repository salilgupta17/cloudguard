"""
Master Validation Engine Orchestrator.
Coordinates:
1. Database Parity & Schema Compatibility (manifest-driven)
2. Isolated Application & API Probing
3. Recovery Objectives & SLA Benchmark Verification
Classifies all detected issues into standardized error categories.
No self-healing or error repair is performed.
"""
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .models import (
    CheckStatus,
    ErrorCategory,
    ValidationCheck,
    ValidationReport
)
from .db_validator import DatabaseValidator
from .app_runner import IsolatedAppLauncher
from .app_validator import ApplicationValidator
from .recovery_validator import RecoveryValidator


class ValidationEngine:
    """
    CloudGuard Disaster Recovery Validation Engine.
    Executes comprehensive verification across Database, Application, and Recovery dimensions.
    """

    def __init__(
        self,
        restored_db_url: str,
        primary_db_url: Optional[str] = None,
        target_app_url: Optional[str] = None,
        backup_manifest: Optional[Dict[str, Any]] = None,
        container_name: Optional[str] = None,
        restore_duration_seconds: Optional[float] = None,
        backup_created_at: Optional[datetime | str] = None,
        drill_started_at: Optional[datetime | str] = None,
        target_rto_seconds: float = 300.0,
        target_rpo_minutes: float = 60.0,
        test_id: Optional[str] = None
    ):
        self.restored_db_url = restored_db_url
        self.primary_db_url = primary_db_url
        self.target_app_url = target_app_url
        self.backup_manifest = backup_manifest or {}
        self.container_name = container_name
        self.restore_duration_seconds = restore_duration_seconds
        self.backup_created_at = backup_created_at
        self.drill_started_at = drill_started_at
        self.target_rto_seconds = target_rto_seconds
        self.target_rpo_minutes = target_rpo_minutes
        self.test_id = test_id

        # Sub-validators
        self.db_validator = DatabaseValidator(
            restored_db_url=self.restored_db_url,
            backup_manifest=self.backup_manifest
        )
        self.app_launcher = IsolatedAppLauncher(
            restored_db_url=self.restored_db_url,
            target_app_url=self.target_app_url,
            container_name=self.container_name
        )
        self.app_validator = ApplicationValidator(launcher=self.app_launcher)
        self.recovery_validator = RecoveryValidator(
            restore_duration_seconds=self.restore_duration_seconds,
            backup_created_at=self.backup_created_at,
            drill_started_at=self.drill_started_at,
            target_rto_seconds=self.target_rto_seconds,
            target_rpo_minutes=self.target_rpo_minutes
        )

    def run_full_validation(self) -> Dict[str, Any]:
        """
        Executes the entire disaster recovery test validation suite.
        Returns a comprehensive report containing:
        - List of all checks (with check_name, status, duration, observed_value, expected_value, error_message, timestamp)
        - Summary counts for PASS, FAIL, SKIPPED, ERROR
        - Error groupings by classification category
        """
        validation_t0 = time.perf_counter()
        started_at = datetime.now(timezone.utc).isoformat()
        all_checks: List[ValidationCheck] = []

        # 1. Database Checks
        db_checks = self.db_validator.run_all_checks()
        all_checks.extend(db_checks)

        # 2. Application Checks
        # When a database is restored in an isolated environment, start a test application connected to that database.
        try:
            with self.app_launcher.run_context():
                app_checks = self.app_validator.run_all_checks()
                all_checks.extend(app_checks)
        except Exception as e:
            # If application launcher completely failed to initialize
            all_checks.append(ValidationCheck(
                check_name="application.startup",
                status=CheckStatus.FAIL,
                duration=0.0,
                observed_value="Startup exception",
                expected_value="Application initialized and listening",
                error_message=f"Application failed to start against isolated database: {str(e)}",
                error_category=ErrorCategory.APPLICATION_ERROR
            ))
            for skip_name in [
                "application.container_status",
                "application.health_endpoint",
                "application.ready_endpoint",
                "application.readonly_business_apis"
            ]:
                all_checks.append(ValidationCheck(
                    check_name=skip_name,
                    status=CheckStatus.SKIPPED,
                    duration=0.0,
                    observed_value="Not running",
                    expected_value="Application running",
                    error_message="Skipped because application startup encountered an unhandled exception",
                    error_category=ErrorCategory.APPLICATION_ERROR
                ))

        # 3. Recovery Checks
        recovery_checks = self.recovery_validator.run_all_checks(validation_start_time=validation_t0)
        all_checks.extend(recovery_checks)

        # 4. Summary & Error Classification
        completed_at = datetime.now(timezone.utc).isoformat()
        total_duration = time.perf_counter() - validation_t0

        summary_counts = {
            CheckStatus.PASS.value: 0,
            CheckStatus.FAIL.value: 0,
            CheckStatus.SKIPPED.value: 0,
            CheckStatus.ERROR.value: 0
        }

        errors_by_category: Dict[str, List[str]] = {
            ErrorCategory.DATABASE_ERROR.value: [],
            ErrorCategory.APPLICATION_ERROR.value: [],
            ErrorCategory.API_ERROR.value: [],
            ErrorCategory.DATA_INTEGRITY_ERROR.value: [],
            ErrorCategory.BACKUP_ERROR.value: [],
            ErrorCategory.RESTORE_ERROR.value: [],
            ErrorCategory.TIMEOUT_ERROR.value: []
        }

        overall_passed = True
        for c in all_checks:
            summary_counts[c.status.value] = summary_counts.get(c.status.value, 0) + 1
            if c.status in [CheckStatus.FAIL, CheckStatus.ERROR]:
                overall_passed = False
                if c.error_category:
                    cat_key = c.error_category.value
                    if cat_key in errors_by_category:
                        errors_by_category[cat_key].append(f"{c.check_name}: {c.error_message}")

        report = ValidationReport(
            test_id=self.test_id,
            overall_passed=overall_passed,
            checks=all_checks,
            summary_counts=summary_counts,
            errors_by_category=errors_by_category,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_seconds=total_duration
        )

        return report.to_dict()
