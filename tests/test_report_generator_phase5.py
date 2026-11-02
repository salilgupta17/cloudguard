"""
Automated Tests for Phase 5: CloudGuard Disaster Recovery Report Generator.
Verifies:
1. Multi-format report generation (JSON, PDF, Human-readable HTML).
2. Presence of all 15 required report dimensions.
3. Methodological distinctions for RTO and RPO.
4. Report storage interface (Local and S3 adapters).
5. Report REST APIs (list, view, download in JSON, HTML, PDF).
6. Non-remediation constraint (strictly reporting-only).
"""
import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from report_service import (
    ReportGenerator,
    ReportData,
    ConfiguredTargets,
    DetectedFailure,
    HtmlReportGenerator,
    PdfReportGenerator,
    LocalReportStorage,
    S3ReportStorage
)


@pytest.fixture
def sample_report_data():
    now = datetime.now(timezone.utc)
    started = now - timedelta(seconds=12)
    backup_time = now - timedelta(minutes=25)

    return ReportData(
        application_name="demo-banking-application",
        test_id="drill-phase5-test-12345",
        backup_id="bkp-phase5-snapshot-001",
        backup_timestamp=backup_time.isoformat(),
        restore_job_status="SUCCESS",
        database_health={"passed": True, "tables_evaluated": 3},
        docker_application_health={"passed": True, "container_status": "RUNNING"},
        api_validation_results={"passed": True, "probes_audited": 4},
        data_integrity_checks={"passed": True, "manifest_records_matched": True},
        recovery_drill_duration_seconds=1.45,
        backup_age_minutes=25.0,
        configured_targets=ConfiguredTargets(target_rto_seconds=300.0, target_rpo_minutes=60.0),
        detected_failures=[],
        error_details=None,
        log_reference="logs/drills/drill-phase5-test-12345.log",
        execution_logs_snippet="[START] Drill initiated.\n[RESTORE] Restored 18 records.\n[SUCCESS] Verification complete.",
        final_status="PASS",
        started_at=started.isoformat(),
        completed_at=now.isoformat(),
        generated_at=now.isoformat(),
        rto_met=True,
        rpo_met=True,
        summary="RECOVERY TEST PASSED: Full database parity and API readiness verified for demo-banking-application."
    )


def test_report_contains_all_15_required_items(sample_report_data):
    """
    Verifies that the generated report contains all 15 required items:
    1. Application name
    2. Recovery test ID
    3. Backup identifier and timestamp
    4. Restore job status
    5. Database health
    6. Docker application health
    7. API validation results
    8. Data integrity checks
    9. Recovery drill duration
    10. Backup age / recovery point freshness
    11. Configured RTO and RPO targets
    12. Detected failures
    13. Error details and log references
    14. Final PASS/FAIL/INCOMPLETE status
    15. Test start and completion timestamps
    """
    rep = sample_report_data.to_dict()

    # 1. Application name
    assert rep["application_name"] == "demo-banking-application"
    # 2. Recovery test ID
    assert rep["test_id"] == "drill-phase5-test-12345"
    # 3. Backup identifier and timestamp
    assert rep["backup_id"] == "bkp-phase5-snapshot-001"
    assert rep["backup_timestamp"] is not None
    # 4. Restore job status
    assert rep["restore_job_status"] == "SUCCESS"
    # 5. Database health
    assert rep["database_health"]["passed"] is True
    # 6. Docker application health
    assert rep["docker_application_health"]["passed"] is True
    # 7. API validation results
    assert rep["api_validation_results"]["passed"] is True
    # 8. Data integrity checks
    assert rep["data_integrity_checks"]["passed"] is True
    # 9. Recovery drill duration
    assert rep["recovery_drill_duration_seconds"] == 1.45
    # 10. Backup age / recovery point freshness
    assert rep["backup_age_minutes"] == 25.0
    # 11. Configured RTO and RPO targets
    assert rep["configured_targets"]["target_rto_seconds"] == 300.0
    assert rep["configured_targets"]["target_rpo_minutes"] == 60.0
    # 12. Detected failures
    assert isinstance(rep["detected_failures"], list)
    # 13. Error details and log references
    assert "log_reference" in rep
    assert "execution_logs_snippet" in rep
    # 14. Final PASS/FAIL/INCOMPLETE status
    assert rep["final_status"] in ["PASS", "FAIL", "INCOMPLETE"]
    # 15. Test start and completion timestamps
    assert rep["started_at"] is not None
    assert rep["completed_at"] is not None


def test_rto_and_rpo_methodological_distinctions(sample_report_data):
    """
    Verifies that the report explicitly distinguishes:
    1. Observed recovery drill duration from actual production RTO.
    2. Backup snapshot age from proving actual RPO.
    """
    rep = sample_report_data

    # RTO distinction check
    assert "drill duration" in rep.rto_methodological_note.lower()
    assert "production rto" in rep.rto_methodological_note.lower()
    assert "dns cutover" in rep.rto_methodological_note.lower()

    # RPO disclaimer check
    assert "backup age alone does not prove actual rpo" in rep.rpo_methodological_note.lower()
    assert "wal" in rep.rpo_methodological_note.lower() or "transaction log" in rep.rpo_methodological_note.lower()


def test_multi_format_generation_json_pdf_html(sample_report_data, tmp_path):
    """
    Verifies generation of reports in:
    - JSON (valid schema and serialized strings)
    - PDF (valid binary stream with %PDF- header)
    - HTML (valid document with styling and executive layout)
    """
    storage = LocalReportStorage(base_dir=tmp_path / "reports")
    generator = ReportGenerator(storage=storage)

    artifacts = generator.generate_all_formats(sample_report_data)

    # 1. JSON
    json_str = artifacts["json_content"]
    parsed = json.loads(json_str)
    assert parsed["application_name"] == "demo-banking-application"
    assert parsed["final_status"] == "PASS"
    assert Path(artifacts["json_uri"]).exists()

    # 2. HTML
    html_str = artifacts["html_content"]
    assert "<!DOCTYPE html>" in html_str
    assert "demo-banking-application" in html_str
    assert "Disaster Recovery Drill Report" in html_str
    assert "PASS" in html_str
    assert Path(artifacts["html_uri"]).exists()

    # 3. PDF
    pdf_bytes = artifacts["pdf_bytes"]
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000
    assert Path(artifacts["pdf_uri"]).exists()


def test_local_report_storage_operations(tmp_path):
    """Verifies LocalReportStorage save, get, exists, and list operations."""
    storage = LocalReportStorage(base_dir=tmp_path / "reports_storage")

    # Save
    storage.save_report("drill-001", "json", '{"status": "PASS"}')
    storage.save_report("drill-001", "html", "<html><body>Pass</body></html>")
    storage.save_report("drill-001", "pdf", b"%PDF-1.4 mock")

    # Exists
    assert storage.report_exists("drill-001", "json") is True
    assert storage.report_exists("drill-001", "pdf") is True
    assert storage.report_exists("drill-001", "txt") is False

    # Get
    assert storage.get_report("drill-001", "json") == '{"status": "PASS"}'
    assert storage.get_report("drill-001", "pdf") == b"%PDF-1.4 mock"

    # List
    reports = storage.list_reports()
    assert len(reports) == 1
    assert reports[0]["report_id"] == "drill-001"
    assert set(reports[0]["formats"]) == {"json", "html", "pdf"}


def test_s3_report_storage_requires_authentic_credentials():
    """Verifies S3ReportStorage validates AWS credentials and rejects mock calls."""
    storage = S3ReportStorage(bucket_name="cloudguard-test-bucket")
    # In test environment without real AWS keys, accessing client must raise ValueError
    import os
    orig_key = os.environ.pop("AWS_ACCESS_KEY_ID", None)
    orig_secret = os.environ.pop("AWS_SECRET_ACCESS_KEY", None)

    try:
        with pytest.raises(ValueError, match="AWS_ACCESS_KEY_ID"):
            storage.save_report("test-drill", "json", "{}")
    finally:
        if orig_key:
            os.environ["AWS_ACCESS_KEY_ID"] = orig_key
        if orig_secret:
            os.environ["AWS_SECRET_ACCESS_KEY"] = orig_secret


def test_report_rest_apis_view_and_download(cg_client, dr_env):
    """
    Test REST APIs:
    - View JSON report: GET /api/v1/reports/{report_id}
    - View HTML report: GET /api/v1/reports/{report_id}/html
    - View PDF report: GET /api/v1/reports/{report_id}/pdf
    - Download report files: GET /api/v1/reports/{report_id}/download?format=pdf|html|json
    """
    # 1. Run a drill to create a fresh report
    create_bkp = cg_client.post("/api/v1/dr/backups", json={
        "source_database_url": dr_env["primary_url"],
        "application_name": "demo-banking-application"
    })
    bkp_id = create_bkp.json()["backup_id"]

    start_drill = cg_client.post("/api/v1/dr/drills/start", json={
        "backup_id": bkp_id,
        "application_name": "demo-banking-application",
        "target_database_url": dr_env["target_url"]
    })
    drill_data = start_drill.json()
    test_id = drill_data["test_id"]

    # 2. View JSON report
    resp_json = cg_client.get(f"/api/v1/reports/{test_id}")
    assert resp_json.status_code == 200
    rep_json = resp_json.json()
    assert rep_json["test_id"] == test_id
    assert rep_json["application_name"] == "demo-banking-application"
    assert "recovery_drill_duration_seconds" in rep_json
    assert "backup_age_minutes" in rep_json
    assert "rto_methodological_note" in rep_json
    assert "rpo_methodological_note" in rep_json

    # 3. View HTML report
    resp_html = cg_client.get(f"/api/v1/reports/{test_id}/html")
    assert resp_html.status_code == 200
    assert "text/html" in resp_html.headers["content-type"]
    assert "<!DOCTYPE html>" in resp_html.text
    assert test_id[:8] in resp_html.text

    # 4. View PDF report
    resp_pdf = cg_client.get(f"/api/v1/reports/{test_id}/pdf")
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    assert resp_pdf.content.startswith(b"%PDF-")

    # 5. Download endpoints
    for fmt, expected_mime in [
        ("pdf", "application/pdf"),
        ("html", "text/html"),
        ("json", "application/json")
    ]:
        dl_resp = cg_client.get(f"/api/v1/reports/{test_id}/download?format={fmt}")
        assert dl_resp.status_code == 200
        assert expected_mime in dl_resp.headers["content-type"]
        assert f"attachment; filename=cloudguard-dr-report-{test_id[:8]}.{fmt}" in dl_resp.headers["content-disposition"]


def test_non_remediation_constraint_in_reports(sample_report_data):
    """
    Crucial Constraint:
    'Do not include automated remediation recommendations,
    execution buttons, or recovery actions.'
    Verifies that the generated reports and HTML/PDF artifacts are strictly
    diagnostic and do not contain remediation buttons or self-healing triggers.
    """
    html = HtmlReportGenerator.generate(sample_report_data)
    json_str = sample_report_data.model_dump_json()

    prohibited_keywords = [
        "remediation",
        "execute recovery",
        "trigger failover",
        "self-heal",
        "apply fix",
        "action button"
    ]

    for kw in prohibited_keywords:
        assert kw not in html.lower(), f"Prohibited keyword '{kw}' found in HTML report"
        assert kw not in json_str.lower(), f"Prohibited keyword '{kw}' found in JSON report"
