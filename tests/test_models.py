"""
Unit Tests for CloudGuard SQLAlchemy Database Models.
Verifies: RecoveryTest, BackupMetadata, ValidationResult, RecoveryReport.
"""
import uuid
from datetime import datetime, timezone
from cloudguard_api import RecoveryTest, BackupMetadata, ValidationResult, RecoveryReport


def test_recovery_test_model_fields_and_persistence(cg_db_session):
    test_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)
    
    rec_test = RecoveryTest(
        test_id=test_id,
        application_name="demo-application",
        environment="staging",
        backup_id="bkp-snap-1001",
        status="PENDING",
        started_at=started
    )
    cg_db_session.add(rec_test)
    cg_db_session.commit()

    saved = cg_db_session.query(RecoveryTest).filter_by(test_id=test_id).first()
    assert saved is not None
    assert saved.test_id == test_id
    assert saved.application_name == "demo-application"
    assert saved.environment == "staging"
    assert saved.backup_id == "bkp-snap-1001"
    assert saved.status == "PENDING"
    assert saved.started_at is not None
    assert saved.completed_at is None

    # Test status update and completion
    saved.status = "SUCCESS"
    saved.completed_at = datetime.now(timezone.utc)
    cg_db_session.commit()

    updated = cg_db_session.query(RecoveryTest).filter_by(test_id=test_id).first()
    assert updated.status == "SUCCESS"
    assert updated.completed_at is not None


def test_backup_metadata_model(cg_db_session):
    backup_id = f"bkp-{uuid.uuid4().hex[:8]}"
    backup = BackupMetadata(
        backup_id=backup_id,
        application_name="demo-application",
        storage_path="/backups/bkp-001.dump",
        size_bytes=1048576,
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        records_count=250
    )
    cg_db_session.add(backup)
    cg_db_session.commit()

    saved = cg_db_session.query(BackupMetadata).filter_by(backup_id=backup_id).first()
    assert saved is not None
    assert saved.application_name == "demo-application"
    assert saved.records_count == 250
    assert len(saved.checksum_sha256) == 64


def test_validation_result_and_report_relationship(cg_db_session):
    test_id = str(uuid.uuid4())
    rec_test = RecoveryTest(
        test_id=test_id,
        application_name="demo-application",
        environment="production",
        backup_id="bkp-rel-test",
        status="RUNNING"
    )
    cg_db_session.add(rec_test)
    cg_db_session.commit()

    # Add Validation Result
    val_id = str(uuid.uuid4())
    val_result = ValidationResult(
        id=val_id,
        test_id=test_id,
        validation_type="DATA_PARITY",
        passed=True,
        details_json='{"tables": ["customers", "orders"], "matched": true}'
    )
    cg_db_session.add(val_result)

    # Add Recovery Report
    rep_id = str(uuid.uuid4())
    report = RecoveryReport(
        report_id=rep_id,
        test_id=test_id,
        status="PASSED",
        rto_seconds=4.25,
        rpo_minutes=15.0,
        summary="Recovery verified with 100% data parity within SLA."
    )
    cg_db_session.add(report)
    cg_db_session.commit()

    # Check back-references
    queried_test = cg_db_session.query(RecoveryTest).filter_by(test_id=test_id).first()
    assert len(queried_test.validation_results) == 1
    assert queried_test.validation_results[0].id == val_id
    assert queried_test.recovery_report is not None
    assert queried_test.recovery_report.report_id == rep_id
    assert queried_test.recovery_report.rto_seconds == 4.25
