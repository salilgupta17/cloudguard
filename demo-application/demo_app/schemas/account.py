"""
Pydantic Schemas for Account Entity.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class AccountCreate(BaseModel):
    customer_id: str = Field(..., json_schema_extra={"example": "c56a4180-65aa-42ec-a945-5fd21dec0538"})
    account_type: Literal["CHECKING", "SAVINGS", "BUSINESS"] = Field(default="CHECKING", json_schema_extra={"example": "CHECKING"})
    initial_deposit_cents: Optional[int] = Field(default=0, ge=0, json_schema_extra={"example": 10000})
    currency: Optional[str] = Field(default="USD", min_length=3, max_length=3, json_schema_extra={"example": "USD"})


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    account_number: str
    account_type: str
    balance_cents: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
