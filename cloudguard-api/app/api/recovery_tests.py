"""
RecoveryTest REST API Endpoints.
Handles drill lifecycle tracking: test_id, application_name, environment, backup_id, status, started_at, completed_at.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.recovery_test import RecoveryTest
    from app.schemas.recovery_test import RecoveryTestCreate, RecoveryTestUpdate, RecoveryTestResponse
    from app.core.logging import logger
except ImportError:
    from ..database import get_db
    from ..models.recovery_test import RecoveryTest
    from ..schemas.recovery_test import RecoveryTestCreate, RecoveryTestUpdate, RecoveryTestResponse
    from ..core.logging import logger

router = APIRouter(prefix="/api/v1/recovery-tests", tags=["Recovery Tests"])


@router.post("", response_model=RecoveryTestResponse, status_code=status.HTTP_201_CREATED)
def create_recovery_test(payload: RecoveryTestCreate, db: Session = Depends(get_db)):
    """Initiates a new RecoveryTest drill record."""
    test_id = str(uuid.uuid4())
    record = RecoveryTest(
        test_id=test_id,
        application_name=payload.application_name,
        environment=payload.environment or "production",
        backup_id=payload.backup_id,
        status="RUNNING",
        started_at=datetime.now(timezone.utc)
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Initialized RecoveryTest drill [{test_id}] for {record.application_name}")
    return record


@router.get("", response_model=List[RecoveryTestResponse])
def list_recovery_tests(
    application_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists historical recovery tests with optional filters."""
    query = db.query(RecoveryTest)
    if application_name:
        query = query.filter(RecoveryTest.application_name == application_name)
    if status:
        query = query.filter(RecoveryTest.status == status)
    return query.order_by(RecoveryTest.started_at.desc()).limit(limit).all()


@router.get("/{test_id}", response_model=RecoveryTestResponse)
def get_recovery_test(test_id: str, db: Session = Depends(get_db)):
    """Retrieves single recovery test record by ID."""
    record = db.query(RecoveryTest).filter(RecoveryTest.test_id == test_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecoveryTest with ID '{test_id}' not found."
        )
    return record


@router.patch("/{test_id}", response_model=RecoveryTestResponse)
def update_recovery_test(test_id: str, payload: RecoveryTestUpdate, db: Session = Depends(get_db)):
    """Updates drill outcome status and completion timestamp."""
    record = db.query(RecoveryTest).filter(RecoveryTest.test_id == test_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecoveryTest with ID '{test_id}' not found."
        )
    if payload.status:
        record.status = payload.status
    if payload.completed_at is not None:
        record.completed_at = payload.completed_at
    elif payload.status in ["SUCCESS", "FAILED"]:
        record.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)
    logger.info(f"Updated RecoveryTest [{test_id}] status to {record.status}")
    return record
