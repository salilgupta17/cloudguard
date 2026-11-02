"""
ValidationResult REST API Endpoints.
Records and queries detailed verification steps for disaster recovery drills.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.validation_result import ValidationResult
    from app.models.recovery_test import RecoveryTest
    from app.schemas.validation_result import ValidationResultCreate, ValidationResultResponse
    from app.core.logging import logger
except ImportError:
    from ..database import get_db
    from ..models.validation_result import ValidationResult
    from ..models.recovery_test import RecoveryTest
    from ..schemas.validation_result import ValidationResultCreate, ValidationResultResponse
    from ..core.logging import logger

router = APIRouter(prefix="/api/v1/validations", tags=["Validation Results"])


@router.post("", response_model=ValidationResultResponse, status_code=status.HTTP_201_CREATED)
def record_validation_result(payload: ValidationResultCreate, db: Session = Depends(get_db)):
    """Records the outcome of a validation stage (schema, parity, checksum, API probe)."""
    # Verify test exists
    test = db.query(RecoveryTest).filter(RecoveryTest.test_id == payload.test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RecoveryTest with ID '{payload.test_id}' not found."
        )

    record = ValidationResult(
        id=str(uuid.uuid4()),
        test_id=payload.test_id,
        validation_type=payload.validation_type,
        passed=payload.passed,
        details_json=payload.details_json
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Recorded ValidationResult [{record.id}] ({payload.validation_type}: passed={payload.passed})")
    return record


@router.get("", response_model=List[ValidationResultResponse])
def list_validations(
    test_id: Optional[str] = None,
    validation_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lists validation results with optional filtering."""
    query = db.query(ValidationResult)
    if test_id:
        query = query.filter(ValidationResult.test_id == test_id)
    if validation_type:
        query = query.filter(ValidationResult.validation_type == validation_type)
    return query.order_by(ValidationResult.created_at.desc()).limit(limit).all()


@router.get("/by-test/{test_id}", response_model=List[ValidationResultResponse])
def get_validations_by_test(test_id: str, db: Session = Depends(get_db)):
    """Retrieves all validation results associated with a specific RecoveryTest."""
    return db.query(ValidationResult).filter(ValidationResult.test_id == test_id).order_by(ValidationResult.created_at.asc()).all()
