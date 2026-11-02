"""
Pydantic Schemas for RecoveryReport API.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RecoveryReportCreate(BaseModel):
    test_id: str
    status: str
    rto_seconds: float
    rpo_minutes: float
    summary: str


class RecoveryReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    test_id: str
    status: str
    rto_seconds: float
    rpo_minutes: float
    summary: str
    created_at: datetime
