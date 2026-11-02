"""
Pydantic Schemas for Customer Entity.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class CustomerCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=64, json_schema_extra={"example": "Jane"})
    last_name: str = Field(..., min_length=1, max_length=64, json_schema_extra={"example": "Doe"})
    email: str = Field(..., json_schema_extra={"example": "jane.doe@example-bank.com"})
    phone: str = Field(..., min_length=7, max_length=32, json_schema_extra={"example": "+1-555-0199"})
    kyc_status: Optional[str] = Field(default="VERIFIED", json_schema_extra={"example": "VERIFIED"})


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_number: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: str
    kyc_status: str
    created_at: datetime
    updated_at: datetime
