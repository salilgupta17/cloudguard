"""
Applications REST API Endpoints.
Lists protected applications, their database infrastructure, backup policies, and recovery summaries.
Strictly read-only monitoring and reporting.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.recovery_test import RecoveryTest
from app.models.backup_metadata import BackupMetadata
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])

# Registered protected applications catalog
PROTECTED_APPLICATIONS_CATALOG = [
    {
        "id": "app-demo-banking",
        "name": "demo-banking-application",
        "display_name": "Demo Core Banking Platform",
        "description": "Critical core banking service with ledger accounting, customer deposits, withdrawals, and balance verification.",
        "environment": "production",
        "tier": "Tier 1 - Mission Critical",
        "framework": "FastAPI (Python 3.12) + Uvicorn",
        "container_image": "cloudguard/demo-application:latest",
        "database": {
            "engine": "PostgreSQL 16",
            "primary_database": "cloudguard_primary",
            "primary_host": "postgres:5432",
            "isolated_test_database": "cloudguard_isolated_test",
            "tables": ["customers", "accounts", "transactions"],
            "constraints": ["foreign_keys", "balance_check_positive", "atomic_transfers"]
        },
        "recovery_objectives": {
            "rto_target_seconds": 300,
            "rto_target_label": "5 Minutes",
            "rpo_target_minutes": 60,
            "rpo_target_label": "1 Hour",
            "rto_methodological_note": "Observed drill duration reflects synthetic sandbox restore + validation time. Actual production RTO includes DNS cutover, traffic diversion, and cluster scaling.",
            "rpo_methodological_note": "Backup age reflects snapshot freshness at drill execution. Actual RPO requires transaction log replay and ledger audit."
        },
        "probes": {
            "health_endpoint": "/health",
            "readiness_endpoint": "/ready",
            "read_only_validation_endpoints": [
                "/api/v1/validation/customers/export",
                "/api/v1/validation/accounts/export",
                "/api/v1/validation/ledger/summary"
            ]
        }
    }
]


@router.get("", response_model=List[dict])
def list_applications(db: Session = Depends(get_db)):
    """
    Returns registered protected applications with live backup and recovery drill statistics.
    """
    result = []
    for app in PROTECTED_APPLICATIONS_CATALOG:
        app_name = app["name"]

        # Live backup stats
        backups = db.query(BackupMetadata).filter(
            BackupMetadata.application_name == app_name
        ).order_by(desc(BackupMetadata.created_at)).all()

        total_backups = len(backups)
        latest_backup = backups[0] if backups else None

        # Live recovery drill stats
        drills = db.query(RecoveryTest).filter(
            RecoveryTest.application_name == app_name
        ).order_by(desc(RecoveryTest.started_at)).all()

        total_drills = len(drills)
        passed_drills = sum(1 for d in drills if d.status == "SUCCESS")
        failed_drills = sum(1 for d in drills if d.status in ("FAILED", "ERROR"))
        latest_drill = drills[0] if drills else None

        app_data = dict(app)
        app_data["live_statistics"] = {
            "total_backups": total_backups,
            "latest_backup_id": latest_backup.backup_id if latest_backup else None,
            "latest_backup_created_at": latest_backup.created_at.isoformat() if latest_backup and latest_backup.created_at else None,
            "latest_backup_records": latest_backup.records_count if latest_backup else 0,
            "latest_backup_size_bytes": latest_backup.size_bytes if latest_backup else 0,
            "total_recovery_tests": total_drills,
            "passed_tests": passed_drills,
            "failed_tests": failed_drills,
            "success_rate_percent": round((passed_drills / total_drills * 100), 1) if total_drills > 0 else 100.0,
            "latest_test_id": latest_drill.test_id if latest_drill else None,
            "latest_test_status": latest_drill.status if latest_drill else "N/A",
            "latest_test_started_at": latest_drill.started_at.isoformat() if latest_drill and latest_drill.started_at else None,
            "latest_restore_duration_seconds": latest_drill.restore_duration_seconds if latest_drill else None
        }
        result.append(app_data)

    return result


@router.get("/{app_name}", response_model=dict)
def get_application_details(app_name: str, db: Session = Depends(get_db)):
    """
    Returns granular application details including schema, live backup records, and drill history.
    """
    apps = list_applications(db=db)
    matched = next((a for a in apps if a["name"] == app_name or a["id"] == app_name), None)
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protected application '{app_name}' not found."
        )
    return matched
