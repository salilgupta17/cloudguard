"""
Disaster Recovery Report Generator.
Computes RTO, RPO, SLA benchmarks, and compliance verdicts.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List


class ReportGenerator:
    @staticmethod
    def generate_report(
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
        """
        Calculates RTO, RPO and determines compliance status:
        - PASSED: Validation 100% passed AND SLAs met.
        - DEGRADED: Validation passed BUT RTO or RPO SLA breached.
        - FAILED: Validation failed or error encountered during drill.
        """
        rto_seconds = max(round((test_completed_at - test_started_at).total_seconds(), 3), 0.0)
        rpo_minutes = max(round((test_started_at - backup_created_at).total_seconds() / 60.0, 2), 0.0)

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
