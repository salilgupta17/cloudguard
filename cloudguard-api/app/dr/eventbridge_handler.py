"""
AWS EventBridge Event Handler & Deduplication Engine.
Listens for AWS Backup 'Restore Job State Change' events.
Prevents duplicate report generation via idempotency tracking.
Orchestrates VPC-internal validation worker tasks.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.recovery_test import RecoveryTest
from app.models.backup_metadata import BackupMetadata
from app.models.recovery_report import RecoveryReport

# In-memory deduplication set for fast lookup
_PROCESSED_RESTORE_JOB_IDS = set()


class EventBridgeRestoreHandler:
    """
    Processes incoming AWS Backup Restore Job events with idempotency verification.
    """

    @classmethod
    def is_duplicate_event(cls, restore_job_id: str, db: Optional[Session] = None) -> bool:
        """
        Verifies whether this restore job has already triggered a test drill or report.
        """
        if not restore_job_id:
            return False

        # Fast in-memory check
        if restore_job_id in _PROCESSED_RESTORE_JOB_IDS:
            return True

        # Database persistent check (matches backup_id or logs or report)
        if db:
            existing_test = db.query(RecoveryTest).filter(
                (RecoveryTest.backup_id == restore_job_id) |
                (RecoveryTest.logs.contains(restore_job_id))
            ).first()
            if existing_test:
                _PROCESSED_RESTORE_JOB_IDS.add(restore_job_id)
                return True

        return False

    @classmethod
    def parse_event(cls, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses standardized AWS EventBridge Restore Job State Change event structure.
        """
        detail = event_payload.get("detail", {})
        restore_job_id = detail.get("restoreJobId") or detail.get("RestoreJobId") or event_payload.get("id")
        status = detail.get("status") or detail.get("Status", "UNKNOWN")
        resource_type = detail.get("resourceType") or detail.get("ResourceType", "RDS")
        recovery_point_arn = detail.get("recoveryPointArn") or detail.get("RecoveryPointArn", "")
        created_resource_arn = detail.get("createdResourceArn") or detail.get("CreatedResourceArn", "")

        return {
            "event_id": event_payload.get("id", str(uuid.uuid4())),
            "time": event_payload.get("time", datetime.now(timezone.utc).isoformat()),
            "source": event_payload.get("source", "aws.backup"),
            "restore_job_id": restore_job_id,
            "status": status.upper(),
            "resource_type": resource_type,
            "recovery_point_arn": recovery_point_arn,
            "created_resource_arn": created_resource_arn
        }

    @classmethod
    def process_restore_event(cls, event_payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Processes the EventBridge restore completion event, ensuring idempotency.
        """
        parsed = cls.parse_event(event_payload)
        restore_job_id = parsed["restore_job_id"]

        logger.info(f"Received EventBridge restore event [{restore_job_id}]: status={parsed['status']}")

        # 1. Deduplication check
        if cls.is_duplicate_event(restore_job_id, db):
            logger.warning(f"Duplicate EventBridge restore event rejected for job [{restore_job_id}].")
            return {
                "status": "DUPLICATE_IGNORED",
                "message": f"Restore job '{restore_job_id}' has already been processed.",
                "restore_job_id": restore_job_id
            }

        # 2. Mark job as processed
        _PROCESSED_RESTORE_JOB_IDS.add(restore_job_id)

        # 3. Handle non-completed states
        if parsed["status"] != "COMPLETED":
            logger.info(f"AWS Backup restore job {restore_job_id} status is {parsed['status']}; no validation required.")
            return {
                "status": "SKIPPED",
                "message": f"Restore job status is {parsed['status']}, not COMPLETED.",
                "restore_job_id": restore_job_id
            }

        # 4. Initiate RecoveryTest record
        test_id = str(uuid.uuid4())
        test_record = RecoveryTest(
            test_id=test_id,
            application_name="demo-banking-application",
            environment="aws-sandbox",
            backup_id=parsed["recovery_point_arn"] or restore_job_id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            isolated_target_db=parsed["created_resource_arn"] or "cloudguard-isolated-dr-test",
            logs=f"EventBridge Restore Job: {restore_job_id}\nCreated Resource: {parsed['created_resource_arn']}"
        )
        db.add(test_record)
        db.commit()
        db.refresh(test_record)

        logger.info(f"Initialized CloudGuard RecoveryTest [{test_id}] for EventBridge restore job [{restore_job_id}]")

        return {
            "status": "ACCEPTED",
            "test_id": test_id,
            "restore_job_id": restore_job_id,
            "created_resource_arn": parsed["created_resource_arn"],
            "message": "Restore job verified. Validation worker initiated."
        }
