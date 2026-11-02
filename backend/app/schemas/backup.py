"""
Pydantic Schemas for Backup Metadata and Manifests.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TableBackupSummary(BaseModel):
    table_name: str
    row_count: int
    columns: List[str]
    checksum: str


class BackupManifest(BaseModel):
    backup_id: str
    timestamp: datetime
    execution_mode: str
    source_database_type: str
    tables_count: int
    total_records: int
    size_bytes: int
    checksum_sha256: str
    tables: Dict[str, TableBackupSummary]
    schema_version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BackupCreateRequest(BaseModel):
    execution_mode: Optional[str] = "LOCAL"
    description: Optional[str] = "Scheduled Disaster Recovery Snapshot"


class BackupCreateResponse(BaseModel):
    backup_id: str
    timestamp: datetime
    execution_mode: str
    storage_path: str
    checksum_sha256: str
    size_bytes: int
    tables_count: int
    total_records: int
    status: str
