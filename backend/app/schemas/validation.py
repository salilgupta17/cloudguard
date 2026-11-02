"""
Pydantic Schemas for Database & API Validation Results.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TableValidationResult(BaseModel):
    table_name: str
    primary_row_count: int
    restored_row_count: int
    row_count_matched: bool
    schema_matched: bool
    checksum_matched: bool
    foreign_keys_valid: bool
    missing_columns: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class ValidationSuiteResult(BaseModel):
    is_valid: bool
    verification_score: float # 0.0 to 100.0%
    tables_evaluated: int
    tables_passed: int
    tables_failed: int
    total_primary_rows: int
    total_restored_rows: int
    table_details: Dict[str, TableValidationResult]
    errors_detected: List[str] = Field(default_factory=list)
