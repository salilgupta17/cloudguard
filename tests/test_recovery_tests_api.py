"""
API Endpoint Tests for CloudGuard Backend.
Verifies REST routes for recovery tests, backups, validations, and reports.
"""
def test_create_and_query_recovery_test(cg_client):
    # 1. Create RecoveryTest
    payload = {
        "application_name": "demo-application",
        "environment": "production",
        "backup_id": "bkp-api-001"
    }
    create_resp = cg_client.post("/api/v1/recovery-tests", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert "test_id" in data
    assert data["status"] == "RUNNING"
    assert data["application_name"] == "demo-application"
    test_id = data["test_id"]

    # 2. Get by test_id
    get_resp = cg_client.get(f"/api/v1/recovery-tests/{test_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["test_id"] == test_id

    # 3. Patch status to SUCCESS
    patch_resp = cg_client.patch(f"/api/v1/recovery-tests/{test_id}", json={"status": "SUCCESS"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "SUCCESS"
    assert patch_resp.json()["completed_at"] is not None

    # 4. List tests
    list_resp = cg_client.get("/api/v1/recovery-tests")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_backup_metadata_endpoints(cg_client):
    payload = {
        "backup_id": "bkp-meta-test-01",
        "application_name": "demo-application",
        "storage_path": "./backups/test.dump",
        "size_bytes": 2048,
        "checksum_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "records_count": 42
    }
    create_resp = cg_client.post("/api/v1/backups", json=payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["backup_id"] == "bkp-meta-test-01"

    get_resp = cg_client.get("/api/v1/backups/bkp-meta-test-01")
    assert get_resp.status_code == 200
    assert get_resp.json()["records_count"] == 42


def test_validations_and_reports_endpoints(cg_client):
    # Create test first
    test_resp = cg_client.post("/api/v1/recovery-tests", json={
        "application_name": "demo-application",
        "environment": "staging",
        "backup_id": "bkp-vr-01"
    })
    test_id = test_resp.json()["test_id"]

    # Post validation result
    val_resp = cg_client.post("/api/v1/validations", json={
        "test_id": test_id,
        "validation_type": "DATABASE_SCHEMA",
        "passed": True,
        "details_json": '{"schema_diff": []}'
    })
    assert val_resp.status_code == 201
    assert val_resp.json()["passed"] is True

    # Get validations by test
    by_test_resp = cg_client.get(f"/api/v1/validations/by-test/{test_id}")
    assert by_test_resp.status_code == 200
    assert len(by_test_resp.json()) == 1

    # Post report
    rep_resp = cg_client.post("/api/v1/reports", json={
        "test_id": test_id,
        "status": "PASSED",
        "rto_seconds": 3.4,
        "rpo_minutes": 10.0,
        "summary": "Drill completed within SLA."
    })
    assert rep_resp.status_code == 201
    assert rep_resp.json()["status"] == "PASSED"

    # Get report by test
    get_rep = cg_client.get(f"/api/v1/reports/by-test/{test_id}")
    assert get_rep.status_code == 200
    assert get_rep.json()["rto_seconds"] == 3.4
