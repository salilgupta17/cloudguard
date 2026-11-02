"""
Pydantic Schemas for RecoveryTest API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RecoveryTestCreate(BaseModel):
    application_name: str = Field(..., json_schema_extra={"example": "demo-application"})
    environment: Optional[str] = Field(default="production", json_schema_extra={"example": "production"})
    backup_id: str = Field(..., json_schema_extra={"example": "bkp-demo-20261102-001"})


class RecoveryTestUpdate(BaseModel):
    status: Optional[str] = Field(None, json_schema_extra={"example": "SUCCESS"})
    completed_at: Optional[datetime] = None
    restore_duration_seconds: Optional[float] = None
    logs: Optional[str] = None
    error_details: Optional[str] = None
    cleaned_up: Optional[bool] = None


class RecoveryTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_id: str
    application_name: str
    environment: str
    backup_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    isolated_target_db: Optional[str] = None
    restore_duration_seconds: Optional[float] = None
    logs: Optional[str] = None
    error_details: Optional[str] = None
    cleaned_up: bool = False
