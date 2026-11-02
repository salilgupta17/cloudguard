"""
Unit Tests for Error Detection and Scenario Diagnostic Classification.
Verifies that CloudGuard accurately detects corruptions, schema drift, and data loss.
"""
import pytest
from pathlib import Path
from sqlalchemy import create_engine, text
from backend.app.engine.backup_manager import BackupManager
from backend.app.engine.restore_manager import IsolatedRestoreManager
from backend.app.engine.validator import DisasterRecoveryValidator
from backend.app.engine.error_detector import DisasterRecoveryErrorDetector
from backend.app.core.exceptions import CorruptedBackupError


def test_corrupted_backup_detection(seeded_primary_db, isolated_sandbox_db_url, local_storage):
    primary_url = seeded_primary_db["url"]

    # 1. Create backup
    backup_mgr = BackupManager(primary_db_url=primary_url, storage_provider=local_storage)
    bkp_resp = backup_mgr.create_backup()

    # 2. Intentionally tamper with the backup payload bytes on disk
    backup_file = Path(bkp_resp.storage_path)
    corrupted_bytes = backup_file.read_bytes() + b"TAMPERED_BYTE"
    backup_file.write_bytes(corrupted_bytes)

    # 3. Attempt restore - should catch checksum mismatch
    restore_mgr = IsolatedRestoreManager(
        primary_db_url=primary_url,
        isolated_target_db_url=isolated_sandbox_db_url,
        storage_provider=local_storage
    )

    with pytest.raises(CorruptedBackupError) as exc_info:
        restore_mgr.execute_isolated_restore(
            backup_id=bkp_resp.backup_id,
            storage_path=bkp_resp.storage_path
        )

    assert "Integrity Check Failed" in str(exc_info.value)

    # 4. Error detector categorizes the error
    findings = DisasterRecoveryErrorDetector.analyze_pipeline_errors(
        restore_error=str(exc_info.value),
        validation=None or type("ValMock", (), {"table_details": {}})(),
        actual_rto_seconds=0.0,
        target_rto_seconds=300.0,
        estimated_rpo_minutes=10.0,
        target_rpo_minutes=60.0
    )

    assert len(findings) == 1
    assert findings[0]["category"] == "BACKUP_CORRUPTION_DETECTED"
    assert findings[0]["severity"] == "CRITICAL"


def test_data_loss_detection(seeded_primary_db, isolated_sandbox_db_url, local_storage):
    primary_url = seeded_primary_db["url"]

    # 1. Create backup and restore normally
    backup_mgr = BackupManager(primary_db_url=primary_url, storage_provider=local_storage)
    bkp_resp = backup_mgr.create_backup()

    restore_mgr = IsolatedRestoreManager(
        primary_db_url=primary_url,
        isolated_target_db_url=isolated_sandbox_db_url,
        storage_provider=local_storage
    )
    restore_mgr.execute_isolated_restore(
        backup_id=bkp_resp.backup_id,
        storage_path=bkp_resp.storage_path
    )

    # 2. Simulate partial data loss in restored DB by deleting an order
    restore_engine = create_engine(isolated_sandbox_db_url)
    with restore_engine.begin() as conn:
        conn.execute(text("DELETE FROM order_items WHERE id IN (SELECT id FROM order_items LIMIT 1)"))

    # 3. Validate
    validator = DisasterRecoveryValidator(
        primary_db_url=primary_url,
        restored_db_url=isolated_sandbox_db_url
    )
    val_result = validator.run_validation_suite()

    assert val_result.is_valid is False
    assert val_result.table_details["order_items"].row_count_matched is False

    # 4. Error detector diagnosis
    findings = DisasterRecoveryErrorDetector.analyze_pipeline_errors(
        restore_error=None,
        validation=val_result,
        actual_rto_seconds=1.5,
        target_rto_seconds=300.0,
        estimated_rpo_minutes=5.0,
        target_rpo_minutes=60.0
    )

    categories = [f["category"] for f in findings]
    assert "DATA_LOSS_DETECTED" in categories
