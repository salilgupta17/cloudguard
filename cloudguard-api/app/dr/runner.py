"""
Disaster Recovery Drill Runner Orchestrator.
Coordinates backup validation, isolated restore execution, parity audits, error tracking, and cleanup.
A recovery drill is a TEST, not production failover.
"""
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.recovery_test import RecoveryTest
from app.models.backup_metadata import BackupMetadata
from app.models.validation_result import ValidationResult
from app.models.recovery_report import RecoveryReport
from app.core.logging import logger
from .local_provider import LocalPostgresDisasterRecoveryProvider
from validation_engine import ValidationEngine
from report_service import ReportGenerator, LocalReportStorage


class DisasterRecoveryDrillRunner:
    def __init__(self, db: Session, provider=None):
        self.db = db
        self.provider = provider or LocalPostgresDisasterRecoveryProvider()

    def run_drill(
        self,
        backup_id: str,
        application_name: str = "demo-banking-application",
        environment: str = "production",
        source_db_url: str | None = None,
        target_db_url: str | None = None,
        auto_cleanup: bool = False
    ) -> RecoveryTest:
        """
        Executes a complete, isolated disaster recovery drill.
        Tracks job status, duration, execution logs, error details, and handles safe cleanup.
        """
        test_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        dst_url = target_db_url or settings.RESTORE_TEST_DATABASE_URL

        logger.info(f"Initiating Recovery Drill [{test_id}] for backup [{backup_id}]...")

        # 1. Fetch Backup Metadata
        backup_meta = self.db.query(BackupMetadata).filter(BackupMetadata.backup_id == backup_id).first()
        if not backup_meta:
            # If not in DB, check on disk
            manifest_file = settings.BACKUP_DIR / f"{backup_id}.manifest.json"
            if manifest_file.exists():
                m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                backup_meta = BackupMetadata(
                    backup_id=backup_id,
                    application_name=application_name,
                    storage_path=str(settings.BACKUP_DIR / f"{backup_id}.sql"),
                    size_bytes=m_data.get("size_bytes", 0),
                    checksum_sha256=m_data.get("checksum_sha256", "UNKNOWN"),
                    records_count=m_data.get("total_records", 0),
                    source_database=m_data.get("source_database", "cloudguard_primary"),
                    schema_version=m_data.get("schema_version", "2.0.0")
                )
                self.db.add(backup_meta)
                self.db.commit()

        # Determine valid SQLAlchemy primary source URL for verification
        src_url = None
        if source_db_url:
            src_url = source_db_url
        elif backup_meta:
            if backup_meta.manifest_json:
                try:
                    m = json.loads(backup_meta.manifest_json)
                    src_url = m.get("source_db_url")
                except Exception:
                    pass
            if not src_url and backup_meta.source_database:
                s_db = backup_meta.source_database
                if "://" in s_db:
                    src_url = s_db
                elif s_db.endswith(".db") or s_db.endswith(".sqlite") or ":" in s_db or "/" in s_db or "\\" in s_db:
                    src_url = f"sqlite:///{Path(s_db).as_posix()}"
        if not src_url:
            src_url = settings.PRIMARY_DATABASE_URL

        # 2. Initialize RecoveryTest Record
        test_record = RecoveryTest(
            test_id=test_id,
            application_name=application_name,
            environment=environment,
            backup_id=backup_id,
            status="RUNNING",
            started_at=started_at,
            isolated_target_db=dst_url.split("@")[-1] if "@" in dst_url else dst_url,
            logs="[START] Initializing isolated disaster recovery drill...\n",
            cleaned_up=False
        )
        self.db.add(test_record)
        self.db.commit()

        try:
            storage_path = backup_meta.storage_path if backup_meta else str(settings.BACKUP_DIR / f"{backup_id}.sql")
            
            # 3. Execute Isolated Restore
            restore_res = self.provider.restore_backup(
                backup_path=storage_path,
                source_db_url=src_url,
                target_db_url=dst_url
            )

            test_record.restore_duration_seconds = restore_res["duration_seconds"]
            test_record.logs = (test_record.logs or "") + restore_res["logs"]

            if not restore_res["success"]:
                # Record Restore Failure Details
                test_record.status = "FAILED"
                test_record.completed_at = datetime.now(timezone.utc)
                test_record.error_details = restore_res.get("error", "Restore execution failed")
                
                # Create failure validation record
                self.db.add(ValidationResult(
                    id=str(uuid.uuid4()),
                    test_id=test_id,
                    validation_type="ISOLATED_RESTORE",
                    passed=False,
                    details_json=str({"error": restore_res.get("error")})
                ))
                self.db.commit()
                return test_record

            # 4. Execute Verification Suite
            manifest_dict = {}
            if backup_meta and backup_meta.manifest_json:
                try:
                    manifest_dict = json.loads(backup_meta.manifest_json)
                except Exception:
                    pass

            val_engine = ValidationEngine(
                restored_db_url=dst_url,
                primary_db_url=src_url,
                backup_manifest=manifest_dict,
                restore_duration_seconds=restore_res.get("duration_seconds"),
                backup_created_at=backup_meta.created_at if backup_meta else None,
                drill_started_at=started_at,
                target_rto_seconds=settings.TARGET_RTO_SECONDS,
                target_rpo_minutes=settings.TARGET_RPO_MINUTES,
                test_id=test_id
            )
            val_result = val_engine.run_full_validation()

            # Record Granular Validation Check Results
            db_val_passed = val_result.get("database_validation", {}).get("passed", True)
            for chk in val_result.get("checks", []):
                chk_name = chk.get("check_name", "UNKNOWN")
                self.db.add(ValidationResult(
                    id=str(uuid.uuid4()),
                    test_id=test_id,
                    validation_type=chk_name,
                    passed=(chk.get("status") == "PASS"),
                    details_json=json.dumps(chk)
                ))

            # 5. Generate Automated Disaster Recovery Reports (JSON, HTML, PDF)
            backup_created_at = backup_meta.created_at if backup_meta else started_at
            completed_at = datetime.now(timezone.utc)

            rep_gen = ReportGenerator(storage=LocalReportStorage(settings.REPORTS_DIR))
            report_data = rep_gen.build_report_data(
                application_name=application_name,
                test_id=test_id,
                backup_id=backup_id,
                backup_created_at=backup_created_at,
                test_started_at=started_at,
                test_completed_at=completed_at,
                restore_job_status="SUCCESS" if restore_res.get("success") else "FAILED",
                validation_results=val_result,
                restore_duration_seconds=restore_res.get("duration_seconds", 0.0),
                target_rto_seconds=settings.TARGET_RTO_SECONDS,
                target_rpo_minutes=settings.TARGET_RPO_MINUTES,
                error_details=test_record.error_details,
                logs=test_record.logs
            )
            rep_artifacts = rep_gen.generate_all_formats(report_data)

            self.db.add(RecoveryReport(
                report_id=test_id,
                test_id=test_id,
                status="PASSED" if report_data.final_status == "PASS" else ("FAILED" if report_data.final_status == "FAIL" else "INCOMPLETE"),
                rto_seconds=report_data.recovery_drill_duration_seconds,
                rpo_minutes=report_data.backup_age_minutes,
                summary=report_data.summary
            ))

            test_record.status = "SUCCESS" if report_data.final_status == "PASS" else "FAILED"
            test_record.completed_at = completed_at

            # 6. Safe Cleanup if requested
            if auto_cleanup:
                cleaned = self.provider.cleanup_target(dst_url)
                test_record.cleaned_up = cleaned
                test_record.logs = (test_record.logs or "") + "\n[CLEANUP] Ephemeral restore sandbox cleaned up safely."

            self.db.commit()
            self.db.refresh(test_record)
            logger.info(f"Recovery Drill [{test_id}] finished with status: {test_record.status}")
            return test_record

        except Exception as e:
            test_record.status = "FAILED"
            test_record.completed_at = datetime.now(timezone.utc)
            test_record.error_details = str(e)
            test_record.logs = (test_record.logs or "") + f"\n[ERROR] Unhandled drill error: {str(e)}"
            self.db.commit()
            self.db.refresh(test_record)
            logger.error(f"Recovery Drill [{test_id}] failed: {e}", exc_info=True)
            return test_record
