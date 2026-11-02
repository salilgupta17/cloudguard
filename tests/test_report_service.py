"""
Unit Tests for report-service module.
"""
from datetime import datetime, timezone, timedelta
from report_service import ReportGenerator, ReportFormatter


def test_report_generator_passed():
    now = datetime.now(timezone.utc)
    backup_time = now - timedelta(minutes=15)
    start_time = now - timedelta(seconds=10)
    end_time = now

    report = ReportGenerator.generate_report(
        test_id="test-rep-01",
        application_name="demo-application",
        backup_created_at=backup_time,
        test_started_at=start_time,
        test_completed_at=end_time,
        validation_passed=True,
        validation_findings=[],
        target_rto_seconds=300.0,
        target_rpo_minutes=60.0
    )

    assert report["status"] == "PASSED"
    assert report["rto_met"] is True
    assert report["rpo_met"] is True
    assert "RECOVERY TEST PASSED" in report["summary"]

    md = ReportFormatter.to_markdown(report)
    assert "🟢 **PASSED**" in md
    assert "Recovery Time Objective (RTO)" in md


def test_report_generator_degraded_on_sla_breach():
    now = datetime.now(timezone.utc)
    backup_time = now - timedelta(hours=2) # 120 minutes vs 60m target RPO
    start_time = now - timedelta(seconds=5)
    end_time = now

    report = ReportGenerator.generate_report(
        test_id="test-rep-02",
        application_name="demo-application",
        backup_created_at=backup_time,
        test_started_at=start_time,
        test_completed_at=end_time,
        validation_passed=True,
        validation_findings=[],
        target_rto_seconds=300.0,
        target_rpo_minutes=60.0
    )

    assert report["status"] == "DEGRADED"
    assert report["rpo_met"] is False
    assert "RECOVERY TEST DEGRADED" in report["summary"]


def test_report_generator_failed():
    now = datetime.now(timezone.utc)
    report = ReportGenerator.generate_report(
        test_id="test-rep-03",
        application_name="demo-application",
        backup_created_at=now,
        test_started_at=now,
        test_completed_at=now,
        validation_passed=False,
        validation_findings=["Checksum mismatch in orders table"]
    )

    assert report["status"] == "FAILED"
    assert "RECOVERY TEST FAILED" in report["summary"]
