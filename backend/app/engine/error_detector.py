"""
CloudGuard Disaster Recovery Error Detection & Root Cause Analysis Engine.
Adheres to V1 Scope: Performs diagnostic classification and reporting ONLY.
Never performs automatic fixing, restarts, or failovers.
"""
from typing import List, Dict, Any
from backend.app.schemas.validation import ValidationSuiteResult


class DisasterRecoveryErrorDetector:
    @staticmethod
    def analyze_pipeline_errors(
        restore_error: str | None,
        validation: ValidationSuiteResult,
        actual_rto_seconds: float,
        target_rto_seconds: float,
        estimated_rpo_minutes: float,
        target_rpo_minutes: float
    ) -> List[Dict[str, Any]]:
        """
        Diagnoses failures across the DR lifecycle and produces structured diagnostic findings.
        """
        findings: List[Dict[str, Any]] = []

        # 1. Restore Execution Errors
        if restore_error:
            category = "RESTORE_CRITICAL_FAILURE"
            if "checksum" in restore_error.lower():
                category = "BACKUP_CORRUPTION_DETECTED"
            elif "interlock" in restore_error.lower() or "safety" in restore_error.lower():
                category = "SAFETY_VIOLATION_UNSAFE_TARGET"
            
            findings.append({
                "stage": "ISOLATED_RESTORE",
                "severity": "CRITICAL",
                "category": category,
                "message": restore_error,
                "impact": "Disaster recovery drill could not complete. Recovery capability unverified."
            })

        # 2. Validation & Parity Errors
        for table_name, details in validation.table_details.items():
            if not details.schema_matched:
                findings.append({
                    "stage": "SCHEMA_VALIDATION",
                    "severity": "HIGH",
                    "category": "SCHEMA_DRIFT",
                    "table": table_name,
                    "message": f"Schema mismatch in table '{table_name}'. Missing columns: {details.missing_columns}",
                    "impact": "Application may experience runtime query errors if restored from this backup."
                })

            if not details.row_count_matched:
                diff = details.primary_row_count - details.restored_row_count
                findings.append({
                    "stage": "DATA_PARITY_VALIDATION",
                    "severity": "CRITICAL",
                    "category": "DATA_LOSS_DETECTED",
                    "table": table_name,
                    "message": f"Row count disparity in '{table_name}': {diff} records lost during restore.",
                    "impact": "Incomplete business records restored. Data integrity compromised."
                })

            if not details.checksum_matched and details.row_count_matched:
                findings.append({
                    "stage": "CHECKSUM_VERIFICATION",
                    "severity": "HIGH",
                    "category": "DATA_MODIFICATION_CORRUPTION",
                    "table": table_name,
                    "message": f"Cryptographic checksum failed for table '{table_name}'.",
                    "impact": "Data content altered or corrupted despite matching row count."
                })

            if not details.foreign_keys_valid:
                findings.append({
                    "stage": "REFERENTIAL_INTEGRITY",
                    "severity": "CRITICAL",
                    "category": "FOREIGN_KEY_ORPHAN",
                    "table": table_name,
                    "message": f"Foreign key integrity violated in table '{table_name}'.",
                    "impact": "Dangling records violate relational constraints."
                })

        # 3. SLA Breaches
        if actual_rto_seconds > target_rto_seconds:
            findings.append({
                "stage": "SLA_MONITORING",
                "severity": "MEDIUM",
                "category": "RTO_SLA_BREACH",
                "message": f"Actual RTO ({actual_rto_seconds}s) exceeded target SLA ({target_rto_seconds}s).",
                "impact": "Recovery takes longer than committed business recovery objective."
            })

        if estimated_rpo_minutes > target_rpo_minutes:
            findings.append({
                "stage": "SLA_MONITORING",
                "severity": "MEDIUM",
                "category": "RPO_SLA_BREACH",
                "message": f"Backup lag ({estimated_rpo_minutes:.1f}m) exceeded target RPO ({target_rpo_minutes}m).",
                "impact": "Potential data loss window exceeds tolerated business RPO threshold."
            })

        return findings
