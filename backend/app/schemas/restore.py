"""
Pydantic Schemas for Isolated Restore Operations.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class IsolatedRestoreRequest(BaseModel):
    backup_id: str
    execution_mode: Optional[str] = "LOCAL"
    target_database_override: Optional[str] = Field(
        default=None,
        description="Optional isolated sandbox connection string. Must pass safety validation!"
    )


class IsolatedRestoreResult(BaseModel):
    restore_id: str
    backup_id: str
    target_database_sanitized: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    tables_restored: int
    records_restored: int
    status: str # SUCCESS, FAILED
    error_message: Optional[str] = None
