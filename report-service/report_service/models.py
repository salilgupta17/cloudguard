"""
Disaster Recovery Report Data Models.
Defines the comprehensive 15-field Disaster Recovery Report structure.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ConfiguredTargets(BaseModel):
    target_rto_seconds: float = 300.0
    target_rpo_minutes: float = 60.0


class DetectedFailure(BaseModel):
    category: str
    check_name: str
    error_message: str
    observed_value: Optional[Any] = None
    expected_value: Optional[Any] = None


class ReportData(BaseModel):
    # 1. Application name
    application_name: str = Field(..., description="Name of the protected application")

    # 2. Recovery test ID
    test_id: str = Field(..., description="Unique ID of the recovery verification drill")

    # 3. Backup identifier and timestamp
    backup_id: str = Field(..., description="Backup snapshot identifier")
    backup_timestamp: Optional[str] = Field(None, description="Timestamp when the backup was created")

    # 4. Restore job status
    restore_job_status: str = Field(..., description="Status of the restore job (e.g. SUCCESS, FAILED)")

    # 5. Database health
    database_health: Dict[str, Any] = Field(default_factory=dict, description="Database connectivity, tables, and schema status")

    # 6. Docker application health
    docker_application_health: Dict[str, Any] = Field(default_factory=dict, description="Docker container and application startup status")

    # 7. API validation results
    api_validation_results: Dict[str, Any] = Field(default_factory=dict, description="Liveness, readiness, and read-only business API probes")

    # 8. Data integrity checks
    data_integrity_checks: Dict[str, Any] = Field(default_factory=dict, description="Manifest record parity, foreign keys, and ledger math")

    # 9. Recovery drill duration
    recovery_drill_duration_seconds: float = Field(0.0, description="Observed duration of the recovery drill in seconds")

    # 10. Backup age / recovery point freshness
    backup_age_minutes: float = Field(0.0, description="Calculated age of backup snapshot in minutes")

    # 11. Configured RTO and RPO targets
    configured_targets: ConfiguredTargets = Field(default_factory=ConfiguredTargets)

    # 12. Detected failures
    detected_failures: List[DetectedFailure] = Field(default_factory=list, description="Categorized list of failures")

    # 13. Error details and log references
    error_details: Optional[str] = Field(None, description="Detailed error trace or failure message")
    log_reference: Optional[str] = Field(None, description="Reference pointer or path to full execution logs")
    execution_logs_snippet: Optional[str] = Field(None, description="Key snippet of execution logs")

    # 14. Final PASS/FAIL/INCOMPLETE status
    final_status: str = Field("INCOMPLETE", description="PASS, FAIL, or INCOMPLETE")

    # 15. Test start and completion timestamps
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Methodological Nuances / Disclaimers
    rto_met: bool = True
    rpo_met: bool = True
    rto_methodological_note: str = (
        "Observed recovery drill duration reflects isolated database restoration and local verification "
        "within a segregated test sandbox. Actual production RTO additionally includes disaster declaration latency, "
        "DNS cutover, traffic routing, edge cache invalidation, and production infrastructure capacity allocation."
    )
    rpo_methodological_note: str = (
        "Backup snapshot age indicates the elapsed time since the scheduled backup archive was produced. "
        "Backup age alone does not prove actual RPO; true data loss window depends on database write velocity, "
        "transaction log (WAL) archiving continuity, and replication synchronization state at the moment of failure."
    )
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
