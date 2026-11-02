"""
Automated Tests for Phase 3: Local Disaster Recovery Test Pipeline.
Verifies pg_dump/local backup, manifest generation, isolated restore execution,
production database protection, logs/duration tracking, failure recording, and cleanup.
"""
import uuid
import pytest
from pathlib import Path
from sqlalchemy import create_engine, text

from demo_app.models.base import Base as BankingBase
from demo_app.seeder import seed_banking_data
from app.dr.safety import assert_safe_restore_target
from app.dr.local_provider import LocalPostgresDisasterRecoveryProvider
from app.dr.aws_provider import AWSBackupDisasterRecoveryProvider
from app.dr.runner import DisasterRecoveryDrillRunner
from app.core.exceptions import UnsafeRestoreTargetError, CorruptedBackupError, ProviderConfigurationError
from cloudguard_api import RecoveryTest, BackupMetadata


@pytest.fixture
def dr_env(tmp_path):
    backup_dir = tmp_path / "dr_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Primary Database (Seeded Source)
    primary_file = tmp_path / "primary_source.db"
    primary_url = f"sqlite:///{primary_file.as_posix()}"
    p_engine = create_engine(primary_url)
    BankingBase.metadata.create_all(p_engine)

    from sqlalchemy.orm import sessionmaker
    SessionP = sessionmaker(bind=p_engine)
    with SessionP() as sp:
        seed_banking_data(sp, customers_count=3)

    # Isolated Target Database (New Sandbox)
    target_file = tmp_path / "isolated_sandbox_drill.db"
    target_url = f"sqlite:///{target_file.as_posix()}"

    provider = LocalPostgresDisasterRecoveryProvider(backup_dir=backup_dir)

    return {
        "backup_dir": backup_dir,
        "primary_url": primary_url,
        "target_url": target_url,
        "provider": provider,
        "primary_file": primary_file,
        "target_file": target_file
    }


def test_create_backup_with_metadata_and_manifest(dr_env):
    """
    Requirement 1 & 2: Create backup and save metadata including timestamp,
    source database, schema version, and test manifest.
    """
    provider = dr_env["provider"]
    backup_id = f"bkp-test-{uuid.uuid4().hex[:8]}"
    
    result = provider.create_backup(
        source_db_url=dr_env["primary_url"],
        backup_id=backup_id,
        description="Phase 3 DR Drill Verification Snapshot"
    )

    assert result["backup_id"] == backup_id
    assert Path(result["storage_path"]).exists()
    assert result["size_bytes"] > 0
    assert len(result["checksum_sha256"]) == 64
    assert result["records_count"] > 0
    assert result["schema_version"] == "2.0.0"

    # Verify manifest file on disk
    manifest = result["manifest_dict"]
    assert manifest["backup_id"] == backup_id
    assert "timestamp" in manifest
    assert "source_database" in manifest
    assert "tables" in manifest
    assert "customers" in manifest["tables"]
    assert "accounts" in manifest["tables"]
    assert "transactions" in manifest["tables"]
    assert manifest["test_manifest"]["isolation_mode"] == "SEGREGATED_SANDBOX"


def test_safety_interlock_prevents_primary_overwrite(dr_env):
    """
    Requirement 4: Never overwrite the original database.
    """
    primary_url = dr_env["primary_url"]

    # 1. Targeting the exact same URL must trigger fatal safety interlock
    with pytest.raises(UnsafeRestoreTargetError) as exc_info:
        assert_safe_restore_target(source_db_url=primary_url, target_db_url=primary_url)
    assert "FATAL SAFETY INTERLOCK" in str(exc_info.value)

    # 2. Targeting a production database name must be rejected
    with pytest.raises(UnsafeRestoreTargetError) as exc_info2:
        assert_safe_restore_target(
            source_db_url=primary_url,
            target_db_url="postgresql+psycopg2://admin:pwd@db-host:5432/banking_production_db"
        )
    assert "SAFETY VIOLATION" in str(exc_info2.value)


def test_isolated_restore_and_duration_logging(dr_env):
    """
    Requirement 3, 5 & 6: Restore backup into a NEW isolated test database,
    measure restore duration, and capture execution logs.
    """
    provider = dr_env["provider"]
    backup_id = f"bkp-test-{uuid.uuid4().hex[:8]}"
    
    # 1. Create backup
    bkp_res = provider.create_backup(source_db_url=dr_env["primary_url"], backup_id=backup_id)

    # 2. Restore into isolated sandbox
    restore_res = provider.restore_backup(
        backup_path=bkp_res["storage_path"],
        source_db_url=dr_env["primary_url"],
        target_db_url=dr_env["target_url"]
    )

    assert restore_res["success"] is True
    assert restore_res["duration_seconds"] > 0.0
    assert restore_res["records_restored"] == bkp_res["records_count"]
    assert "Safety Interlock Passed" in restore_res["logs"]
    assert "Cryptographic SHA-256 Checksum Verified" in restore_res["logs"]
    assert "Isolated Restore Drill Completed Successfully" in restore_res["logs"]

    # Verify target database now contains data
    target_engine = create_engine(dr_env["target_url"])
    with target_engine.connect() as conn:
        cust_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        assert cust_count >= 3


def test_handle_restore_failures_and_record_details(dr_env):
    """
    Requirement 7: Handle restore failures by recording their details.
    """
    provider = dr_env["provider"]
    backup_id = f"bkp-fail-{uuid.uuid4().hex[:8]}"

    # 1. Create backup
    bkp_res = provider.create_backup(source_db_url=dr_env["primary_url"], backup_id=backup_id)

    # 2. Corrupt the dump file
    dump_path = Path(bkp_res["storage_path"])
    dump_path.write_text("CORRUPTED_NON_JSON_DATA", encoding="utf-8")

    # 3. Attempt restore - should fail checksum check
    with pytest.raises(CorruptedBackupError) as exc_info:
        provider.restore_backup(
            backup_path=str(dump_path),
            source_db_url=dr_env["primary_url"],
            target_db_url=dr_env["target_url"]
        )
    assert "Cryptographic checksum failed" in str(exc_info.value)


def test_safe_cleanup_of_temporary_test_resources(dr_env):
    """
    Requirement 8: Clean up temporary test resources safely.
    """
    provider = dr_env["provider"]
    backup_id = f"bkp-clean-{uuid.uuid4().hex[:8]}"
    
    bkp_res = provider.create_backup(source_db_url=dr_env["primary_url"], backup_id=backup_id)
    provider.restore_backup(
        backup_path=bkp_res["storage_path"],
        source_db_url=dr_env["primary_url"],
        target_db_url=dr_env["target_url"]
    )

    # Verify target file exists
    assert dr_env["target_file"].exists()

    # Clean up isolated target
    cleaned = provider.cleanup_target(dr_env["target_url"])
    assert cleaned is True

    # Critical Assertion: Primary database must still exist and be intact!
    assert dr_env["primary_file"].exists()
    p_engine = create_engine(dr_env["primary_url"])
    with p_engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM customers")).scalar() >= 3


def test_dr_pipeline_rest_apis(cg_client, dr_env):
    """
    Test REST APIs:
    - List test backups
    - Start an isolated recovery drill
    - View recovery drill status
    - View backup and restore metadata
    - Safe cleanup endpoint
    """
    # 1. Create Backup via API
    create_bkp_resp = cg_client.post("/api/v1/dr/backups", json={
        "source_database_url": dr_env["primary_url"],
        "application_name": "demo-banking-application",
        "description": "API Integration Test Backup"
    })
    assert create_bkp_resp.status_code == 201
    bkp_data = create_bkp_resp.json()
    backup_id = bkp_data["backup_id"]
    assert bkp_data["schema_version"] == "2.0.0"

    # 2. List backups via API
    list_bkp_resp = cg_client.get("/api/v1/dr/backups")
    assert list_bkp_resp.status_code == 200
    assert any(b["backup_id"] == backup_id for b in list_bkp_resp.json())

    # 3. View backup metadata
    get_bkp_resp = cg_client.get(f"/api/v1/dr/backups/{backup_id}")
    assert get_bkp_resp.status_code == 200
    assert get_bkp_resp.json()["backup_id"] == backup_id

    # 4. Start an isolated recovery drill
    drill_resp = cg_client.post("/api/v1/dr/drills/start", json={
        "backup_id": backup_id,
        "application_name": "demo-banking-application",
        "environment": "staging",
        "target_database_url": dr_env["target_url"],
        "auto_cleanup": False
    })
    assert drill_resp.status_code == 201
    drill_data = drill_resp.json()
    test_id = drill_data["test_id"]
    assert drill_data["status"] == "SUCCESS"
    assert drill_data["restore_duration_seconds"] > 0.0

    # 5. View recovery drill status & logs
    status_resp = cg_client.get(f"/api/v1/dr/drills/{test_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["test_id"] == test_id
    assert "Isolated Restore Drill Completed Successfully" in status_resp.json()["logs"]

    # 6. View drill full metadata
    meta_resp = cg_client.get(f"/api/v1/dr/drills/{test_id}/metadata")
    assert meta_resp.status_code == 200
    meta_data = meta_resp.json()
    assert meta_data["test"]["test_id"] == test_id
    assert meta_data["backup"]["backup_id"] == backup_id
    assert len(meta_data["validation_results"]) >= 1
    assert meta_data["recovery_report"]["status"] == "PASSED"

    # 7. Safe cleanup endpoint
    clean_resp = cg_client.delete(f"/api/v1/dr/drills/{test_id}/cleanup")
    assert clean_resp.status_code == 200
    assert clean_resp.json()["status"] == "cleaned_up"


def test_aws_backup_provider_interface_configuration_check():
    """
    Requirement 11: Prepare interfaces for future AWS Backup integration,
    validating credentials without simulating fake success (Rule 10).
    """
    provider = AWSBackupDisasterRecoveryProvider()
    with pytest.raises(ProviderConfigurationError) as exc_info:
        provider.create_backup("postgresql://prod-db", "bkp-aws-01")
    assert "AWS Backup execution mode requires active AWS IAM credentials" in str(exc_info.value)
