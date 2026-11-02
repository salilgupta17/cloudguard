"""
Pydantic Schemas for Transaction Entity.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class TransactionCreate(BaseModel):
    transaction_type: Literal["DEPOSIT", "WITHDRAWAL"] = Field(..., json_schema_extra={"example": "DEPOSIT"})
    amount_cents: int = Field(..., gt=0, json_schema_extra={"example": 5000})
    description: Optional[str] = Field(default="Standard Transaction", max_length=255, json_schema_extra={"example": "ATM Cash Deposit"})


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    reference_number: str
    transaction_type: str
    amount_cents: int
    balance_after_cents: int
    description: str
    status: str
    created_at: datetime
