"""
BackupMetadata REST API Endpoints.
Catalogs backup snapshots, manifests, and checksums.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.backup_metadata import BackupMetadata
    from app.schemas.backup_metadata import BackupMetadataCreate, BackupMetadataResponse
    from app.core.logging import logger
except ImportError:
    from ..database import get_db
    from ..models.backup_metadata import BackupMetadata
    from ..schemas.backup_metadata import BackupMetadataCreate, BackupMetadataResponse
    from ..core.logging import logger

router = APIRouter(prefix="/api/v1/backups", tags=["Backup Metadata"])


@router.post("", response_model=BackupMetadataResponse, status_code=status.HTTP_201_CREATED)
def register_backup(payload: BackupMetadataCreate, db: Session = Depends(get_db)):
    """Registers a verified backup snapshot manifest."""
    existing = db.query(BackupMetadata).filter(BackupMetadata.backup_id == payload.backup_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Backup with ID '{payload.backup_id}' already registered."
        )

    record = BackupMetadata(
        backup_id=payload.backup_id,
        application_name=payload.application_name,
        storage_path=payload.storage_path,
        size_bytes=payload.size_bytes,
        checksum_sha256=payload.checksum_sha256,
        records_count=payload.records_count
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Registered BackupMetadata [{payload.backup_id}] for {payload.application_name}")
    return record


@router.get("", response_model=List[BackupMetadataResponse])
def list_backups(
    application_name: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists registered backup snapshots."""
    query = db.query(BackupMetadata)
    if application_name:
        query = query.filter(BackupMetadata.application_name == application_name)
    return query.order_by(BackupMetadata.created_at.desc()).limit(limit).all()


@router.get("/{backup_id}", response_model=BackupMetadataResponse)
def get_backup(backup_id: str, db: Session = Depends(get_db)):
    """Retrieves single backup snapshot metadata by ID."""
    record = db.query(BackupMetadata).filter(BackupMetadata.backup_id == backup_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup with ID '{backup_id}' not found."
        )
    return record
