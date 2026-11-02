"""
Disaster Recovery Report Generator Orchestrator.
Builds comprehensive compliance reports containing the 15 required dimensions
and outputs them in JSON, PDF, and Human-Readable HTML formats.
Includes clear methodological distinctions for RTO and RPO.
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

from .models import ReportData, ConfiguredTargets, DetectedFailure
from .html_generator import HtmlReportGenerator
from .pdf_generator import PdfReportGenerator
from .storage import ReportStorageInterface, LocalReportStorage


class ReportGenerator:
    """
    Automated Disaster Recovery Report Generator.
    Coordinates creation, formatting (JSON/PDF/HTML), and storage of reports.
    """

    def __init__(self, storage: Optional[ReportStorageInterface] = None):
        self.storage = storage or LocalReportStorage()

    @staticmethod
    def _normalize_dt(dt: Optional[datetime | str]) -> datetime:
        if dt is None:
            return datetime.now(timezone.utc)
        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                return datetime.now(timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @classmethod
    def build_report_data(
        cls,
        application_name: str,
        test_id: str,
        backup_id: str,
        backup_created_at: Optional[datetime | str],
        test_started_at: Optional[datetime | str],
        test_completed_at: Optional[datetime | str],
        restore_job_status: str,
        validation_results: Dict[str, Any],
        restore_duration_seconds: float,
        target_rto_seconds: float = 300.0,
        target_rpo_minutes: float = 60.0,
        error_details: Optional[str] = None,
        logs: Optional[str] = None
    ) -> ReportData:
        """
        Assembles all 15 required report fields into a standardized ReportData model.
        """
        t_started = cls._normalize_dt(test_started_at)
        t_completed = cls._normalize_dt(test_completed_at)
        b_created = cls._normalize_dt(backup_created_at) if backup_created_at else t_started

        # Calculate drill duration & backup age
        drill_duration = max(round((t_completed - t_started).total_seconds(), 3), round(restore_duration_seconds, 3))
        backup_age_minutes = max(round((t_started - b_created).total_seconds() / 60.0, 2), 0.0)

        rto_met = drill_duration <= target_rto_seconds
        rpo_met = backup_age_minutes <= target_rpo_minutes

        # Extract validation breakdowns
        db_health = validation_results.get("database_validation", {"passed": True})
        app_health = validation_results.get("application_validation", {"passed": True})
        api_results = validation_results.get("api_validation", {"passed": True})
        data_integrity = validation_results.get("data_integrity", {"passed": True})

        # Determine failures
        detected_failures: List[DetectedFailure] = []
        errors_by_cat = validation_results.get("errors_by_category", {})
        for cat, err_list in errors_by_cat.items():
            for item in err_list:
                parts = item.split(": ", 1)
                chk_name = parts[0] if len(parts) > 1 else "check"
                msg = parts[1] if len(parts) > 1 else item
                detected_failures.append(DetectedFailure(
                    category=cat,
                    check_name=chk_name,
                    error_message=msg
                ))

        # Check records for failures if not already extracted
        if not detected_failures:
            for chk in validation_results.get("checks", []):
                if chk.get("status") in ["FAIL", "ERROR"]:
                    detected_failures.append(DetectedFailure(
                        category=chk.get("error_category") or "GENERAL_ERROR",
                        check_name=chk.get("check_name", "UNKNOWN"),
                        error_message=chk.get("error_message") or "Validation check failed",
                        observed_value=chk.get("observed_value"),
                        expected_value=chk.get("expected_value")
                    ))

        # Determine Final PASS/FAIL/INCOMPLETE status
        restore_succeeded = (restore_job_status.upper() == "SUCCESS")
        overall_passed = validation_results.get("overall_passed", len(detected_failures) == 0)

        if not restore_succeeded:
            final_status = "FAIL"
            summary = (
                f"RECOVERY TEST FAILED: Database restore operation failed for {application_name}. "
                f"Error: {error_details or 'Restore process error'}."
            )
        elif not overall_passed or len(detected_failures) > 0:
            final_status = "FAIL"
            summary = (
                f"RECOVERY TEST FAILED: Restored database or application failed integrity/readiness checks for {application_name}. "
                f"Detected issues: {len(detected_failures)}."
            )
        elif not rto_met or not rpo_met:
            final_status = "FAIL"  # SLA violation fails the drill
            summary = (
                f"RECOVERY TEST FAILED: Recovery SLAs breached for {application_name}. "
                f"Observed drill duration: {drill_duration}s (target: {target_rto_seconds}s), "
                f"Backup age: {backup_age_minutes}m (target: {target_rpo_minutes}m)."
            )
        else:
            final_status = "PASS"
            summary = (
                f"RECOVERY TEST PASSED: Full database parity, API readiness, and SLA compliance verified for {application_name}. "
                f"Observed drill duration: {drill_duration}s (within {target_rto_seconds}s target). "
                f"Backup freshness: {backup_age_minutes}m (within {target_rpo_minutes}m target)."
            )

        # Snippet of logs
        log_snippet = None
        if logs:
            lines = logs.strip().split("\n")
            log_snippet = "\n".join(lines[-25:]) if len(lines) > 25 else logs.strip()

        return ReportData(
            application_name=application_name,
            test_id=test_id,
            backup_id=backup_id,
            backup_timestamp=b_created.isoformat(),
            restore_job_status=restore_job_status,
            database_health=db_health,
            docker_application_health=app_health,
            api_validation_results=api_results,
            data_integrity_checks=data_integrity,
            recovery_drill_duration_seconds=drill_duration,
            backup_age_minutes=backup_age_minutes,
            configured_targets=ConfiguredTargets(
                target_rto_seconds=target_rto_seconds,
                target_rpo_minutes=target_rpo_minutes
            ),
            detected_failures=detected_failures,
            error_details=error_details,
            log_reference=f"logs/drills/{test_id}.log",
            execution_logs_snippet=log_snippet,
            final_status=final_status,
            started_at=t_started.isoformat(),
            completed_at=t_completed.isoformat(),
            generated_at=datetime.now(timezone.utc).isoformat(),
            rto_met=rto_met,
            rpo_met=rpo_met,
            summary=summary
        )

    def generate_all_formats(self, report_data: ReportData) -> Dict[str, Any]:
        """Generates JSON, HTML, and PDF representations of the report."""
        json_content = report_data.model_dump_json(indent=2)
        html_content = HtmlReportGenerator.generate(report_data)
        pdf_content = PdfReportGenerator.generate(report_data)

        # Persist across formats
        json_uri = self.storage.save_report(report_data.test_id, "json", json_content)
        html_uri = self.storage.save_report(report_data.test_id, "html", html_content)
        pdf_uri = self.storage.save_report(report_data.test_id, "pdf", pdf_content)

        return {
            "report_data": report_data,
            "json_content": json_content,
            "html_content": html_content,
            "pdf_bytes": pdf_content,
            "json_uri": json_uri,
            "html_uri": html_uri,
            "pdf_uri": pdf_uri
        }

    generate_all = generate_all_formats

    # Backward compatibility for Phase 1-4 callers
    @classmethod
    def generate_report(
        cls,
        test_id: str,
        application_name: str,
        backup_created_at: datetime,
        test_started_at: datetime,
        test_completed_at: datetime,
        validation_passed: bool,
        validation_findings: List[str],
        target_rto_seconds: float = 300.0,
        target_rpo_minutes: float = 60.0
    ) -> Dict[str, Any]:
        """Backward-compatible report dictionary generator."""
        t_started = cls._normalize_dt(test_started_at)
        t_completed = cls._normalize_dt(test_completed_at)
        b_created = cls._normalize_dt(backup_created_at)

        rto_seconds = max(round((t_completed - t_started).total_seconds(), 3), 0.0)
        rpo_minutes = max(round((t_started - b_created).total_seconds() / 60.0, 2), 0.0)

        rto_met = rto_seconds <= target_rto_seconds
        rpo_met = rpo_minutes <= target_rpo_minutes

        if not validation_passed:
            status = "FAILED"
            summary = (
                f"RECOVERY TEST FAILED: Verification detected integrity or health check errors for {application_name}. "
                f"Issues found: {len(validation_findings)}."
            )
        elif not rto_met or not rpo_met:
            status = "DEGRADED"
            summary = (
                f"RECOVERY TEST DEGRADED: Application {application_name} restored and verified with data parity, "
                f"but operational SLAs were breached (RTO: {rto_seconds}s / Target: {target_rto_seconds}s, "
                f"RPO: {rpo_minutes}m / Target: {target_rpo_minutes}m)."
            )
        else:
            status = "PASSED"
            summary = (
                f"RECOVERY TEST PASSED: Full database parity and API readiness verified for {application_name}. "
                f"RTO: {rto_seconds}s (within {target_rto_seconds}s SLA). "
                f"RPO: {rpo_minutes}m (within {target_rpo_minutes}m SLA)."
            )

        return {
            "test_id": test_id,
            "application_name": application_name,
            "status": status,
            "rto_seconds": rto_seconds,
            "target_rto_seconds": target_rto_seconds,
            "rto_met": rto_met,
            "rpo_minutes": rpo_minutes,
            "target_rpo_minutes": target_rpo_minutes,
            "rpo_met": rpo_met,
            "validation_passed": validation_passed,
            "summary": summary,
            "findings": validation_findings,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
