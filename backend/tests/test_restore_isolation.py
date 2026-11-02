"""
Unit Tests for IsolatedRestoreManager and DR Safety Interlock Rules.
Verifies Rule 7: Never restore over the production database!
"""
import pytest
from backend.app.engine.backup_manager import BackupManager
from backend.app.engine.restore_manager import IsolatedRestoreManager
from backend.app.core.exceptions import UnsafeRestoreTargetError


def test_safety_interlock_prevents_primary_overwrite(seeded_primary_db, local_storage):
    primary_url = seeded_primary_db["url"]

    # Passing identical primary URL as target must immediately trigger safety interlock
    with pytest.raises(UnsafeRestoreTargetError) as exc_info:
        IsolatedRestoreManager(
            primary_db_url=primary_url,
            isolated_target_db_url=primary_url,
            storage_provider=local_storage
        )

    assert "FATAL SAFETY INTERLOCK" in str(exc_info.value)


def test_isolated_restore_execution(seeded_primary_db, isolated_sandbox_db_url, local_storage):
    primary_url = seeded_primary_db["url"]
    expected_counts = seeded_primary_db["counts"]

    # 1. Create backup
    backup_mgr = BackupManager(primary_db_url=primary_url, storage_provider=local_storage)
    bkp_resp = backup_mgr.create_backup()

    # 2. Restore into isolated sandbox
    restore_mgr = IsolatedRestoreManager(
        primary_db_url=primary_url,
        isolated_target_db_url=isolated_sandbox_db_url,
        storage_provider=local_storage
    )
    result = restore_mgr.execute_isolated_restore(
        backup_id=bkp_resp.backup_id,
        storage_path=bkp_resp.storage_path
    )

    assert result.status == "SUCCESS"
    assert result.tables_restored >= 5
    assert result.records_restored == sum(expected_counts.values())
    assert result.duration_seconds > 0.0
