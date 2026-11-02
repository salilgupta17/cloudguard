"""
CloudGuard Disaster Recovery Report Generator.
Synthesizes drill results, integrity audits, SLA compliance, and produces executive DR reports.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.schemas.report import DisasterRecoveryReport
from backend.app.schemas.validation import ValidationSuiteResult
from backend.app.schemas.restore import IsolatedRestoreResult
from backend.app.engine.error_detector import DisasterRecoveryErrorDetector
from backend.app.core.logging import logger


class DisasterRecoveryReportGenerator:
    @staticmethod
    def generate_report(
        backup_id: str,
        backup_timestamp: datetime,
        restore_result: IsolatedRestoreResult | None,
        validation_result: ValidationSuiteResult,
        target_rto_seconds: float = 300.0,
        target_rpo_minutes: float = 60.0,
        execution_mode: str = "LOCAL",
        restore_error: str | None = None
    ) -> DisasterRecoveryReport:
        report_id = f"cg-rep-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        actual_rto = restore_result.duration_seconds if restore_result else 0.0
        rto_met = (actual_rto <= target_rto_seconds) if restore_result else False

        # Calculate RPO: delta between now (or restore start) and when backup was created
        delta_minutes = (now - backup_timestamp).total_seconds() / 60.0
        estimated_rpo = max(round(delta_minutes, 2), 0.0)
        rpo_met = (estimated_rpo <= target_rpo_minutes)

        # Run Error Detector
        findings = DisasterRecoveryErrorDetector.analyze_pipeline_errors(
            restore_error=restore_error,
            validation=validation_result,
            actual_rto_seconds=actual_rto,
            target_rto_seconds=target_rto_seconds,
            estimated_rpo_minutes=estimated_rpo,
            target_rpo_minutes=target_rpo_minutes
        )

        critical_or_high = [f for f in findings if f.get("severity") in ["CRITICAL", "HIGH"]]
        has_critical = len(critical_or_high) > 0 or not validation_result.is_valid or (restore_error is not None)

        if has_critical:
            status = "FAILED"
            verdict = "NON-COMPLIANT: Disaster recovery drill failed data integrity or restore interlock checks. Recovery cannot be guaranteed."
        elif not rto_met or not rpo_met:
            status = "DEGRADED"
            verdict = "DEGRADED COMPLIANCE: Data restored and verified with 100% integrity, but exceeded operational SLA limits."
        else:
            status = "PASSED"
            verdict = "FULLY COMPLIANT: Backup verified, isolated restore drill completed, all tables and foreign keys matched 100%."

        root_causes = [f"{f['category']} [{f['stage']}]: {f['message']}" for f in findings]

        report = DisasterRecoveryReport(
            report_id=report_id,
            generated_at=now,
            execution_mode=execution_mode,
            status=status,
            actual_rto_seconds=actual_rto,
            target_rto_seconds=target_rto_seconds,
            rto_sla_met=rto_met,
            estimated_rpo_minutes=estimated_rpo,
            target_rpo_minutes=target_rpo_minutes,
            rpo_sla_met=rpo_met,
            verification_score=validation_result.verification_score if not restore_error else 0.0,
            backup_id=backup_id,
            backup_timestamp=backup_timestamp,
            isolated_target_db=restore_result.target_database_sanitized if restore_result else "UNAVAILABLE",
            validation_suite=validation_result,
            root_cause_analysis=root_causes,
            compliance_verdict=verdict
        )

        logger.info(f"Disaster Recovery Report [{report_id}] generated with status: {status}")
        return report

    @staticmethod
    def to_markdown(report: DisasterRecoveryReport) -> str:
        """Renders executive markdown compliance summary."""
        status_badge = "🟢 PASSED" if report.status == "PASSED" else ("🟡 DEGRADED" if report.status == "DEGRADED" else "🔴 FAILED")
        
        md = [
            f"# CloudGuard Disaster Recovery Audit Report",
            f"**Report ID**: `{report.report_id}`  ",
            f"**Execution Mode**: `{report.execution_mode}`  ",
            f"**Audit Status**: **{status_badge}**  ",
            f"**Generated**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            "",
            "## Executive Summary",
            f"> {report.compliance_verdict}",
            "",
            "## SLA Benchmarks & Objectives",
            f"| Metric | Target SLA | Measured Actual | Compliance Status |",
            f"|---|---|---|---|",
            f"| **RTO (Recovery Time Objective)** | < {report.target_rto_seconds:.1f}s | {report.actual_rto_seconds:.2f}s | {'✅ MET' if report.rto_sla_met else '❌ BREACHED'} |",
            f"| **RPO (Recovery Point Objective)** | < {report.target_rpo_minutes:.1f} min | {report.estimated_rpo_minutes:.1f} min | {'✅ MET' if report.rpo_sla_met else '❌ BREACHED'} |",
            f"| **Data Integrity Score** | 100.0% | {report.verification_score:.1f}% | {'✅ MET' if report.verification_score == 100.0 else '❌ DEFICIENT'} |",
            "",
            "## Table Parity & Validation Breakdown",
            "| Table Name | Primary Rows | Restored Rows | Row Parity | Schema | Checksum | Foreign Keys |",
            "|---|---|---|---|---|---|---|",
        ]

        for table_name, detail in report.validation_suite.table_details.items():
            row_p = "✅" if detail.row_count_matched else "❌"
            schema_p = "✅" if detail.schema_matched else "❌"
            hash_p = "✅" if detail.checksum_matched else "❌"
            fk_p = "✅" if detail.foreign_keys_valid else "❌"
            md.append(f"| `{table_name}` | {detail.primary_row_count} | {detail.restored_row_count} | {row_p} | {schema_p} | {hash_p} | {fk_p} |")

        if report.root_cause_analysis:
            md.append("")
            md.append("## Diagnostic Findings & Discrepancies")
            for item in report.root_cause_analysis:
                md.append(f"- ⚠️ {item}")

        md.append("")
        md.append("---")
        md.append("*CloudGuard V1 — Reporting & Verification Engine. No unauthorized modifications made to production.*")

        return "\n".join(md)
