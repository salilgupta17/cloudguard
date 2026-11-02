"""
Unit Tests for DisasterRecoveryValidator.
Verifies data parity, schema parity, cryptographic checksums, and relational integrity.
"""
from backend.app.engine.backup_manager import BackupManager
from backend.app.engine.restore_manager import IsolatedRestoreManager
from backend.app.engine.validator import DisasterRecoveryValidator


def test_validation_suite_success(seeded_primary_db, isolated_sandbox_db_url, local_storage):
    primary_url = seeded_primary_db["url"]

    # 1. Backup
    backup_mgr = BackupManager(primary_db_url=primary_url, storage_provider=local_storage)
    bkp_resp = backup_mgr.create_backup()

    # 2. Restore to isolated sandbox
    restore_mgr = IsolatedRestoreManager(
        primary_db_url=primary_url,
        isolated_target_db_url=isolated_sandbox_db_url,
        storage_provider=local_storage
    )
    restore_mgr.execute_isolated_restore(
        backup_id=bkp_resp.backup_id,
        storage_path=bkp_resp.storage_path
    )

    # 3. Validate
    validator = DisasterRecoveryValidator(
        primary_db_url=primary_url,
        restored_db_url=isolated_sandbox_db_url
    )
    val_result = validator.run_validation_suite()

    assert val_result.is_valid is True
    assert val_result.verification_score == 100.0
    assert val_result.tables_failed == 0
    assert val_result.tables_passed >= 5
    assert len(val_result.errors_detected) == 0

    for table_name, detail in val_result.table_details.items():
        assert detail.row_count_matched is True
        assert detail.schema_matched is True
        assert detail.checksum_matched is True
        assert detail.foreign_keys_valid is True
