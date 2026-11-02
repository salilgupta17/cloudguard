"""
Unit Tests for DisasterRecoveryReportGenerator.
Verifies compliance reporting, RTO/RPO calculation, and executive markdown formatting.
"""
from datetime import datetime, timezone, timedelta
from backend.app.engine.backup_manager import BackupManager
from backend.app.engine.restore_manager import IsolatedRestoreManager
from backend.app.engine.validator import DisasterRecoveryValidator
from backend.app.engine.report_generator import DisasterRecoveryReportGenerator


def test_report_generation_passed(seeded_primary_db, isolated_sandbox_db_url, local_storage):
    primary_url = seeded_primary_db["url"]

    # 1. Full pipeline execution
    backup_mgr = BackupManager(primary_db_url=primary_url, storage_provider=local_storage)
    bkp_resp = backup_mgr.create_backup()

    restore_mgr = IsolatedRestoreManager(
        primary_db_url=primary_url,
        isolated_target_db_url=isolated_sandbox_db_url,
        storage_provider=local_storage
    )
    restore_result = restore_mgr.execute_isolated_restore(
        backup_id=bkp_resp.backup_id,
        storage_path=bkp_resp.storage_path
    )

    validator = DisasterRecoveryValidator(
        primary_db_url=primary_url,
        restored_db_url=isolated_sandbox_db_url
    )
    val_result = validator.run_validation_suite()

    # 2. Generate Report
    report = DisasterRecoveryReportGenerator.generate_report(
        backup_id=bkp_resp.backup_id,
        backup_timestamp=bkp_resp.timestamp,
        restore_result=restore_result,
        validation_result=val_result,
        target_rto_seconds=300.0,
        target_rpo_minutes=60.0,
        execution_mode="LOCAL"
    )

    assert report.status == "PASSED"
    assert report.rto_sla_met is True
    assert report.rpo_sla_met is True
    assert report.verification_score == 100.0
    assert "FULLY COMPLIANT" in report.compliance_verdict

    # 3. Test Markdown rendering
    md_content = DisasterRecoveryReportGenerator.to_markdown(report)
    assert "# CloudGuard Disaster Recovery Audit Report" in md_content
    assert "🟢 PASSED" in md_content
    assert "RTO (Recovery Time Objective)" in md_content
