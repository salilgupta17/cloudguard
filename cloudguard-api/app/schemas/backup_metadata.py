"""
Pydantic Schemas for BackupMetadata API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BackupMetadataCreate(BaseModel):
    backup_id: str
    application_name: str
    storage_path: str
    size_bytes: int
    checksum_sha256: str
    records_count: int
    source_database: Optional[str] = "cloudguard_primary"
    schema_version: Optional[str] = "1.0.0"
    manifest_json: Optional[str] = None


class BackupMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    backup_id: str
    application_name: str
    storage_path: str
    size_bytes: int
    checksum_sha256: str
    records_count: int
    source_database: str
    schema_version: str
    manifest_json: Optional[str] = None
    created_at: datetime
