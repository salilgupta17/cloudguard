"""
Comprehensive Automated Tests for Phase 4: CloudGuard Validation Engine.
Verifies:
1. Complete passing validation pipeline across Database, Application, and Recovery dimensions.
2. Manifest-driven record comparison (isolated from production data).
3. Standardized check structure: check_name, status, duration, observed_value, expected_value, error_message, timestamp.
4. Error classification into all required categories:
   - DATABASE_ERROR
   - APPLICATION_ERROR
   - API_ERROR
   - DATA_INTEGRITY_ERROR
   - BACKUP_ERROR
   - RESTORE_ERROR
   - TIMEOUT_ERROR
5. Non-remediation constraint (reporting only, no automatic fixing).
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text

from demo_app.models.base import Base as BankingBase
from demo_app.seeder import seed_banking_data
from validation_engine import (
    ValidationEngine,
    DatabaseValidator,
    IsolatedAppLauncher,
    ApplicationValidator,
    RecoveryValidator,
    CheckStatus,
    ErrorCategory,
    ValidationCheck
)


@pytest.fixture
def isolated_banking_env(tmp_path):
    """
    Creates an isolated restored database populated with synthetic banking data
    and generates a corresponding backup test manifest.
    """
    db_file = tmp_path / "restored_isolated_sandbox.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    engine = create_engine(db_url)
    BankingBase.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    with Session() as session:
        seed_banking_data(session, customers_count=3)

    # Inspect seeded counts
    with engine.connect() as conn:
        c_count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar() or 0
        a_count = conn.execute(text("SELECT COUNT(*) FROM accounts")).scalar() or 0
        t_count = conn.execute(text("SELECT COUNT(*) FROM transactions")).scalar() or 0

    manifest = {
        "backup_id": "bkp-manifest-test-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_database": "primary_banking_db",
        "schema_version": "2.0.0",
        "total_records": c_count + a_count + t_count,
        "tables": {
            "customers": {
                "row_count": c_count,
                "columns": ["id", "customer_number", "first_name", "last_name", "email", "phone", "kyc_status", "created_at", "updated_at"]
            },
            "accounts": {
                "row_count": a_count,
                "columns": ["id", "customer_id", "account_number", "account_type", "balance_cents", "currency", "status", "created_at", "updated_at"]
            },
            "transactions": {
                "row_count": t_count,
                "columns": ["id", "account_id", "reference_number", "transaction_type", "amount_cents", "balance_after_cents", "description", "status", "created_at"]
            }
        }
    }

    return {
        "db_url": db_url,
        "engine": engine,
        "manifest": manifest,
        "counts": {"customers": c_count, "accounts": a_count, "transactions": t_count}
    }


def test_validation_engine_complete_pass_scenario(isolated_banking_env):
    """
    Passing Scenario:
    Verifies all 15 checks across Database, Application, and Recovery pass
    when the database matches the manifest and SLAs are honored.
    """
    env = isolated_banking_env
    engine = ValidationEngine(
        restored_db_url=env["db_url"],
        backup_manifest=env["manifest"],
        restore_duration_seconds=1.25,
        backup_created_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        drill_started_at=datetime.now(timezone.utc),
        target_rto_seconds=300.0,
        target_rpo_minutes=60.0,
        test_id="test-drill-pass-001"
    )

    report = engine.run_full_validation()

    assert report["overall_passed"] is True
    assert report["test_id"] == "test-drill-pass-001"
    assert report["summary_counts"]["PASS"] >= 14
    assert report["summary_counts"]["FAIL"] == 0
    assert report["summary_counts"]["ERROR"] == 0
    assert len(report["findings"]) == 0

    # Verify check data structures
    checks = report["checks"]
    check_names = [c["check_name"] for c in checks]

    # Required DATABASE checks
    assert "database.connectivity" in check_names
    assert "database.required_tables" in check_names
    assert "database.schema_compatibility" in check_names
    assert "database.expected_records" in check_names
    assert "database.foreign_key_consistency" in check_names
    assert "database.transaction_integrity" in check_names

    # Required APPLICATION checks
    assert "application.container_status" in check_names
    assert "application.startup" in check_names
    assert "application.health_endpoint" in check_names
    assert "application.ready_endpoint" in check_names
    assert "application.readonly_business_apis" in check_names

    # Required RECOVERY checks
    assert "recovery.restore_duration" in check_names
    assert "recovery.backup_freshness" in check_names
    assert "recovery.recovery_objectives" in check_names
    assert "recovery.validation_execution_time" in check_names

    # Verify fields on every check record
    for c in checks:
        assert "check_name" in c
        assert c["status"] in ["PASS", "FAIL", "SKIPPED", "ERROR"]
        assert isinstance(c["duration"], float)
        assert "observed_value" in c
        assert "expected_value" in c
        assert "timestamp" in c


def test_manifest_driven_comparison_not_production_data(isolated_banking_env, tmp_path):
    """
    CRITICAL REQUIREMENT:
    'Compare expected records against the backup-specific test manifest,
    not current production data.'
    Verifies that when production database data evolves after backup,
    validation checks against manifest records and succeeds without drift penalty.
    """
    env = isolated_banking_env

    # Simulate production database with extra newer records added after backup snapshot
    prod_file = tmp_path / "prod_source_evolved.db"
    prod_url = f"sqlite:///{prod_file.as_posix()}"
    prod_engine = create_engine(prod_url)
    BankingBase.metadata.create_all(prod_engine)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=prod_engine)
    with Session() as s:
        seed_banking_data(s, customers_count=10) # 10 customers vs 3 in restored

    # Validate restored DB against manifest (which specifies 3 customers)
    engine = ValidationEngine(
        restored_db_url=env["db_url"],
        primary_db_url=prod_url, # Pass evolved production DB as reference
        backup_manifest=env["manifest"],
        restore_duration_seconds=2.0,
        target_rto_seconds=300.0,
        target_rpo_minutes=60.0
    )

    report = engine.run_full_validation()

    # Must pass because restored DB matches the backup-specific manifest!
    expected_records_check = next(c for c in report["checks"] if c["check_name"] == "database.expected_records")
    assert expected_records_check["status"] == "PASS"
    assert report["overall_passed"] is True


def test_failing_scenario_database_error_on_connectivity_failure():
    """
    Failing Scenario: DATABASE_ERROR
    Verifies connectivity failure classifies into DATABASE_ERROR and skips dependent checks.
    """
    validator = DatabaseValidator(restored_db_url="sqlite:////nonexistent/invalid/dir/db.sqlite")
    checks = validator.run_all_checks()

    conn_check = next(c for c in checks if c["check_name"] == "database.connectivity")
    assert conn_check["status"] == "FAIL"
    assert conn_check["error_category"] == "DATABASE_ERROR"
    assert "failed" in conn_check["error_message"].lower()

    # Verify dependent checks are SKIPPED with DATABASE_ERROR classification
    skipped_checks = [c for c in checks if c["check_name"] != "database.connectivity"]
    assert len(skipped_checks) == 5
    for sc in skipped_checks:
        assert sc["status"] == "SKIPPED"
        assert sc["error_category"] == "DATABASE_ERROR"


def test_failing_scenario_database_error_on_missing_table(isolated_banking_env):
    """
    Failing Scenario: DATABASE_ERROR
    Verifies that dropping a required table produces a FAIL with DATABASE_ERROR.
    """
    env = isolated_banking_env
    # Drop transactions table
    with env["engine"].connect() as conn:
        conn.execute(text("DROP TABLE transactions"))
        conn.commit()

    validator = DatabaseValidator(restored_db_url=env["db_url"], backup_manifest=env["manifest"])
    table_check = validator.check_required_tables()

    assert table_check["status"] == "FAIL"
    assert table_check["error_category"] == "DATABASE_ERROR"
    assert "missing required tables" in table_check["error_message"].lower()
    assert "transactions" in table_check["error_message"]


def test_failing_scenario_data_integrity_error_on_record_count_discrepancy(isolated_banking_env):
    """
    Failing Scenario: DATA_INTEGRITY_ERROR
    Verifies that record count mismatch against manifest produces DATA_INTEGRITY_ERROR.
    """
    env = isolated_banking_env
    # Manifest expects 100 transactions, but restored DB has fewer
    manifest = dict(env["manifest"])
    manifest["tables"] = dict(manifest["tables"])
    manifest["tables"]["transactions"] = {
        "row_count": 999, # Tampered / higher expectation
        "columns": manifest["tables"]["transactions"]["columns"]
    }

    validator = DatabaseValidator(restored_db_url=env["db_url"], backup_manifest=manifest)
    rec_check = validator.check_expected_test_records()

    assert rec_check["status"] == "FAIL"
    assert rec_check["error_category"] == "DATA_INTEGRITY_ERROR"
    assert "record count mismatch" in rec_check["error_message"].lower()


def test_failing_scenario_data_integrity_error_on_foreign_key_violation(isolated_banking_env):
    """
    Failing Scenario: DATA_INTEGRITY_ERROR
    Verifies that orphaned records produce DATA_INTEGRITY_ERROR.
    """
    env = isolated_banking_env
    # Inject an orphaned account referencing nonexistent customer
    with env["engine"].connect() as conn:
        conn.execute(text(
            "INSERT INTO accounts (id, customer_id, account_number, account_type, balance_cents, currency, status, created_at, updated_at) "
            "VALUES ('orphan-acc-1', 'nonexistent-customer-id', 'ACC-ORPHAN-99', 'CHECKING', 50000, 'USD', 'ACTIVE', '2026-11-02', '2026-11-02')"
        ))
        conn.commit()

    validator = DatabaseValidator(restored_db_url=env["db_url"], backup_manifest=env["manifest"])
    fk_check = validator.check_foreign_key_consistency()

    assert fk_check["status"] == "FAIL"
    assert fk_check["error_category"] == "DATA_INTEGRITY_ERROR"
    assert "orphaned accounts" in fk_check["error_message"].lower()


def test_failing_scenario_data_integrity_error_on_ledger_math_discrepancy(isolated_banking_env):
    """
    Failing Scenario: DATA_INTEGRITY_ERROR
    Verifies ledger tampering (stored balance != sum of transactions) produces DATA_INTEGRITY_ERROR.
    """
    env = isolated_banking_env
    # Tamper with an account's stored balance
    with env["engine"].connect() as conn:
        conn.execute(text("UPDATE accounts SET balance_cents = balance_cents + 50000 WHERE id = (SELECT id FROM accounts LIMIT 1)"))
        conn.commit()

    validator = DatabaseValidator(restored_db_url=env["db_url"], backup_manifest=env["manifest"])
    tx_check = validator.check_transaction_integrity()

    assert tx_check["status"] == "FAIL"
    assert tx_check["error_category"] == "DATA_INTEGRITY_ERROR"
    assert "balance discrepancy" in tx_check["error_message"].lower()


def test_failing_scenario_application_error_on_unhealthy_container():
    """
    Failing Scenario: APPLICATION_ERROR
    Verifies container status failure produces APPLICATION_ERROR.
    """
    # 1. Test container inspection error
    launcher_docker = IsolatedAppLauncher(
        restored_db_url="sqlite:///./data/fake.db",
        container_name="nonexistent-cloudguard-container-xyz"
    )
    validator_docker = ApplicationValidator(launcher=launcher_docker)
    container_check = validator_docker.check_container_status()

    assert container_check["status"] == "FAIL"
    assert container_check["error_category"] == "APPLICATION_ERROR"
    assert container_check["error_message"] is not None

    # 2. Test local standalone process failure
    launcher_local = IsolatedAppLauncher(restored_db_url="sqlite:///./data/fake.db")
    launcher_local._startup_error = "Container exited unexpectedly with status 137"
    validator_local = ApplicationValidator(launcher=launcher_local)
    local_check = validator_local.check_container_status()

    assert local_check["status"] == "FAIL"
    assert local_check["error_category"] == "APPLICATION_ERROR"
    assert "137" in local_check["error_message"]


def test_failing_scenario_api_error_on_non_200_response():
    """
    Failing Scenario: API_ERROR
    Verifies HTTP failure on health/ready probe classifies into API_ERROR.
    """
    class MockClient:
        def get(self, path):
            class MockResponse:
                status_code = 503
                text = "Service Unavailable: Database pool exhausted"
                headers = {"content-type": "text/plain"}
            return MockResponse()

    launcher = IsolatedAppLauncher(restored_db_url="sqlite:///dummy.db")
    launcher.is_started = True
    validator = ApplicationValidator(launcher=launcher)

    health_check = validator.check_health_endpoint(client=MockClient())
    ready_check = validator.check_ready_endpoint(client=MockClient())

    assert health_check["status"] == "FAIL"
    assert health_check["error_category"] == "API_ERROR"
    assert "503" in health_check["error_message"]

    assert ready_check["status"] == "FAIL"
    assert ready_check["error_category"] == "API_ERROR"
    assert "503" in ready_check["error_message"]


def test_failing_scenario_backup_error_on_rpo_freshness_breach():
    """
    Failing Scenario: BACKUP_ERROR
    Verifies that a stale backup breaching target RPO produces BACKUP_ERROR.
    """
    # Backup was created 180 minutes ago, target RPO is 60 minutes
    stale_backup_time = datetime.now(timezone.utc) - timedelta(minutes=180)
    drill_time = datetime.now(timezone.utc)

    validator = RecoveryValidator(
        backup_created_at=stale_backup_time,
        drill_started_at=drill_time,
        target_rpo_minutes=60.0
    )
    rpo_check = validator.check_backup_freshness()

    assert rpo_check["status"] == "FAIL"
    assert rpo_check["error_category"] == "BACKUP_ERROR"
    assert "breached target rpo" in rpo_check["error_message"].lower()


def test_failing_scenario_timeout_error_on_rto_duration_breach():
    """
    Failing Scenario: TIMEOUT_ERROR
    Verifies that restore duration breaching target RTO produces TIMEOUT_ERROR.
    """
    # Restore took 450 seconds, target RTO is 300 seconds
    validator = RecoveryValidator(
        restore_duration_seconds=450.0,
        target_rto_seconds=300.0
    )
    rto_check = validator.check_restore_duration()

    assert rto_check["status"] == "FAIL"
    assert rto_check["error_category"] == "TIMEOUT_ERROR"
    assert "breached target rto" in rto_check["error_message"].lower()


def test_non_remediation_constraint(isolated_banking_env):
    """
    Crucial Constraint:
    'Do not attempt to fix detected errors.'
    Verifies that the validation engine is strictly reporting-only
    and never modifies, drops, or alters database state.
    """
    env = isolated_banking_env

    # Count initial records
    with env["engine"].connect() as conn:
        before_count = conn.execute(text("SELECT COUNT(*) FROM accounts")).scalar() or 0

    # Tamper with an account to force validation error
    with env["engine"].connect() as conn:
        conn.execute(text("UPDATE accounts SET balance_cents = 99999999 WHERE id = (SELECT id FROM accounts LIMIT 1)"))
        conn.commit()

    # Run validation engine
    engine = ValidationEngine(
        restored_db_url=env["db_url"],
        backup_manifest=env["manifest"],
        restore_duration_seconds=1.0
    )
    report = engine.run_full_validation()

    # Validation detects error
    assert report["overall_passed"] is False

    # Verify that the validator DID NOT auto-fix or revert the account balance
    with env["engine"].connect() as conn:
        tampered_balance = conn.execute(text("SELECT balance_cents FROM accounts WHERE balance_cents = 99999999")).scalar()
        after_count = conn.execute(text("SELECT COUNT(*) FROM accounts")).scalar() or 0

    assert tampered_balance == 99999999
    assert after_count == before_count
