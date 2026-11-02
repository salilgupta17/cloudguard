"""
Pydantic Schemas for Disaster Recovery Compliance Reports and Metrics.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.validation import ValidationSuiteResult


class DisasterRecoveryReport(BaseModel):
    report_id: str
    generated_at: datetime
    execution_mode: str
    status: str # PASSED, FAILED, DEGRADED
    
    # SLA Metrics
    actual_rto_seconds: float
    target_rto_seconds: float
    rto_sla_met: bool
    
    estimated_rpo_minutes: float
    target_rpo_minutes: float
    rpo_sla_met: bool
    
    # Verification Summary
    verification_score: float # 0 - 100%
    backup_id: str
    backup_timestamp: datetime
    isolated_target_db: str
    
    validation_suite: ValidationSuiteResult
    root_cause_analysis: List[str] = Field(default_factory=list)
    compliance_verdict: str


class DRMetricsSummary(BaseModel):
    total_drills: int
    successful_drills: int
    failed_drills: int
    success_rate_percent: float
    avg_rto_seconds: float
    latest_rpo_minutes: float
    sla_compliance_rate: float
