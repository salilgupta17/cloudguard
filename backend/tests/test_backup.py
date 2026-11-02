"""
Unit Tests for BackupManager and Manifest Generation.
"""
from backend.app.engine.backup_manager import BackupManager


def test_backup_creation_and_manifest(seeded_primary_db, local_storage):
    primary_url = seeded_primary_db["url"]
    expected_counts = seeded_primary_db["counts"]

    manager = BackupManager(primary_db_url=primary_url, storage_provider=local_storage)
    resp = manager.create_backup(description="Automated Test Snapshot")

    assert resp.status == "AVAILABLE"
    assert resp.tables_count >= 5  # organizations, users, orders, order_items, audit_logs
    assert resp.total_records == sum(expected_counts.values())
    assert len(resp.checksum_sha256) == 64

    # Read back manifest from storage
    manifest = local_storage.read_manifest(resp.storage_path)
    assert manifest["backup_id"] == resp.backup_id
    assert manifest["total_records"] == resp.total_records
    assert "organizations" in manifest["tables"]
    assert manifest["tables"]["organizations"]["row_count"] == expected_counts["organizations"]
