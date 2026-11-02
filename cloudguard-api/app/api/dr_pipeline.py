"""
Disaster Recovery Pipeline REST APIs.
Endpoints to create backups, list backups, trigger recovery drills, view drill status, and clean up test resources.
A recovery drill is a TEST, not production failover.
"""
import uuid
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.backup_metadata import BackupMetadata
from app.models.recovery_test import RecoveryTest
from app.models.validation_result import ValidationResult
from app.models.recovery_report import RecoveryReport
from app.schemas.backup_metadata import BackupMetadataResponse
from app.schemas.recovery_test import RecoveryTestResponse
from app.schemas.validation_result import ValidationResultResponse
from app.schemas.recovery_report import RecoveryReportResponse
from app.dr.local_provider import LocalPostgresDisasterRecoveryProvider
from app.dr.runner import DisasterRecoveryDrillRunner
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/dr", tags=["Disaster Recovery Pipeline"])


class StartDrillRequest(BaseModel):
    backup_id: str = Field(..., json_schema_extra={"example": "bkp-demo-20261102-001"})
    application_name: Optional[str] = Field(default="demo-banking-application", json_schema_extra={"example": "demo-banking-application"})
    environment: Optional[str] = Field(default="production", json_schema_extra={"example": "production"})
    source_database_url: Optional[str] = Field(default=None, json_schema_extra={"example": "sqlite:///./data/primary.db"})
    target_database_url: Optional[str] = Field(default=None, json_schema_extra={"example": "sqlite:///./data/isolated_test.db"})
    auto_cleanup: Optional[bool] = Field(default=False, json_schema_extra={"example": False})


class CreateBackupRequest(BaseModel):
    source_database_url: Optional[str] = Field(default=None)
    application_name: Optional[str] = Field(default="demo-banking-application")
    description: Optional[str] = Field(default="Manual Disaster Recovery Drill Snapshot")


class DrillMetadataResponse(BaseModel):
    test: RecoveryTestResponse
    backup: Optional[BackupMetadataResponse] = None
    validation_results: List[ValidationResultResponse] = []
    recovery_report: Optional[RecoveryReportResponse] = None


@router.post("/backups", response_model=BackupMetadataResponse, status_code=status.HTTP_201_CREATED)
def create_backup_endpoint(payload: CreateBackupRequest, db: Session = Depends(get_db)):
    """
    Executes a PostgreSQL backup using pg_dump / local provider,
    computes SHA-256 cryptographic hash, saves test manifest, and catalogs metadata.
    """
    provider = LocalPostgresDisasterRecoveryProvider()
    source_url = payload.source_database_url or settings.PRIMARY_DATABASE_URL
    backup_id = f"bkp-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

    res = provider.create_backup(
        source_db_url=source_url,
        backup_id=backup_id,
        description=payload.description or "Automated Backup"
    )

    meta = BackupMetadata(
        backup_id=res["backup_id"],
        application_name=payload.application_name or "demo-banking-application",
        storage_path=res["storage_path"],
        size_bytes=res["size_bytes"],
        checksum_sha256=res["checksum_sha256"],
        records_count=res["records_count"],
        source_database=res["source_database"],
        schema_version=res["schema_version"],
        manifest_json=json.dumps(res["manifest_dict"])
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta


@router.get("/backups", response_model=List[BackupMetadataResponse])
def list_backups_endpoint(limit: int = 50, db: Session = Depends(get_db)):
    """Lists available test backups with metadata and manifests."""
    return db.query(BackupMetadata).order_by(BackupMetadata.created_at.desc()).limit(limit).all()


@router.get("/backups/{backup_id}", response_model=BackupMetadataResponse)
def get_backup_endpoint(backup_id: str, db: Session = Depends(get_db)):
    """Retrieves specific backup metadata and manifest."""
    backup = db.query(BackupMetadata).filter(BackupMetadata.backup_id == backup_id).first()
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID '{backup_id}' not found."
        )
    return backup


@router.post("/drills/start", response_model=RecoveryTestResponse, status_code=status.HTTP_201_CREATED)
def start_recovery_drill(payload: StartDrillRequest, db: Session = Depends(get_db)):
    """
    Starts an isolated recovery drill.
    A recovery drill is a TEST, not production failover.
    Restores the backup into a NEW isolated test database, evaluates parity, and records logs.
    """
    runner = DisasterRecoveryDrillRunner(db=db)
    drill_record = runner.run_drill(
        backup_id=payload.backup_id,
        application_name=payload.application_name or "demo-banking-application",
        environment=payload.environment or "production",
        source_db_url=payload.source_database_url,
        target_db_url=payload.target_database_url,
        auto_cleanup=payload.auto_cleanup or False
    )
    return drill_record


@router.get("/drills", response_model=List[RecoveryTestResponse])
def list_drills(limit: int = 50, db: Session = Depends(get_db)):
    """Lists historical disaster recovery drills."""
    return db.query(RecoveryTest).order_by(RecoveryTest.started_at.desc()).limit(limit).all()


@router.get("/drills/{test_id}", response_model=RecoveryTestResponse)
def get_drill_status(test_id: str, db: Session = Depends(get_db)):
    """
    Views recovery drill status, RTO duration, execution logs, and failure details.
    """
    drill = db.query(RecoveryTest).filter(RecoveryTest.test_id == test_id).first()
    if not drill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery drill with ID '{test_id}' not found."
        )
    return drill


@router.get("/drills/{test_id}/metadata", response_model=DrillMetadataResponse)
def get_drill_full_metadata(test_id: str, db: Session = Depends(get_db)):
    """
    Views comprehensive metadata: drill status, backup manifest, validation results, and compliance report.
    """
    drill = db.query(RecoveryTest).filter(RecoveryTest.test_id == test_id).first()
    if not drill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery drill with ID '{test_id}' not found."
        )

    backup = db.query(BackupMetadata).filter(BackupMetadata.backup_id == drill.backup_id).first()
    validations = db.query(ValidationResult).filter(ValidationResult.test_id == test_id).all()
    report = db.query(RecoveryReport).filter(RecoveryReport.test_id == test_id).first()

    return DrillMetadataResponse(
        test=drill,
        backup=backup,
        validation_results=validations,
        recovery_report=report
    )


@router.delete("/drills/{test_id}/cleanup")
def cleanup_drill_sandbox(test_id: str, db: Session = Depends(get_db)):
    """
    Cleans up temporary isolated test database resources safely.
    Interlocks guarantee the primary production database is NEVER touched.
    """
    drill = db.query(RecoveryTest).filter(RecoveryTest.test_id == test_id).first()
    if not drill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery drill with ID '{test_id}' not found."
        )

    if drill.cleaned_up:
        return {"status": "already_cleaned_up", "test_id": test_id}

    target_url = drill.isolated_target_db or settings.RESTORE_TEST_DATABASE_URL
    provider = LocalPostgresDisasterRecoveryProvider()
    cleaned = provider.cleanup_target(target_url)

    drill.cleaned_up = cleaned
    drill.logs = (drill.logs or "") + f"\n[CLEANUP] Manual cleanup executed: cleaned={cleaned}"
    db.commit()

    return {
        "status": "cleaned_up" if cleaned else "cleanup_failed",
        "test_id": test_id,
        "isolated_target": drill.isolated_target_db
    }


@router.post("/aws/eventbridge-webhook", status_code=status.HTTP_202_ACCEPTED)
def receive_eventbridge_restore_event(
    event_payload: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook receiving AWS Backup 'Restore Job State Change' events from Amazon EventBridge.
    Applies deduplication and orchestrates the VPC validation worker.
    """
    from app.dr.eventbridge_handler import EventBridgeRestoreHandler

    result = EventBridgeRestoreHandler.process_restore_event(event_payload, db)
    return result

