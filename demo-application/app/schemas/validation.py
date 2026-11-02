"""
Read-Only Validation Schemas for CloudGuard Verification Engine.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict


class LedgerSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_customers: int
    total_accounts: int
    total_transactions: int
    total_balance_cents: int
    ledger_integrity_passed: bool
    checksum_sha256: str
    status: str


class CustomerExportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_number: str
    full_name: str
    email: str
    phone: str
    kyc_status: str
    accounts_count: int


class AccountExportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_number: str
    customer_id: str
    account_type: str
    balance_cents: int
    currency: str
    status: str
    transactions_count: int
