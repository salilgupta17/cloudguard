"""
Pydantic Schemas for ValidationResult API.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ValidationResultCreate(BaseModel):
    test_id: str
    validation_type: str
    passed: bool
    details_json: str


class ValidationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    test_id: str
    validation_type: str
    passed: bool
    details_json: str
    created_at: datetime
