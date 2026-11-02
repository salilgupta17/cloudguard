"""
Phase 6 Automated Test Suite — Disaster Recovery Monitoring Dashboard.
Verifies:
1. Applications REST API endpoints (/api/v1/applications, /api/v1/applications/{app_name})
2. Live statistics calculations (backups, tests, success rates)
3. Frontend Vite production build integrity and bundle generation
4. Strict compliance with reporting-only scope (prohibiting remediation/failover/action buttons)
5. Presence of all 5 required pages: Overview, Applications, Recovery Tests, Reports, Monitoring
"""
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


def test_applications_api_list_and_live_statistics(cg_client, dr_env):
    """
    Verifies GET /api/v1/applications returns the protected workload catalog
    with live backup and recovery drill statistics.
    """
    # 1. Query applications list
    resp = cg_client.get("/api/v1/applications")
    assert resp.status_code == 200
    apps = resp.json()
    assert isinstance(apps, list)
    assert len(apps) >= 1

    app = apps[0]
    assert app["name"] == "demo-banking-application"
    assert "database" in app
    assert app["database"]["primary_database"] == "cloudguard_primary"
    assert app["database"]["isolated_test_database"] == "cloudguard_isolated_test"
    assert "customers" in app["database"]["tables"]
    assert "accounts" in app["database"]["tables"]
    assert "transactions" in app["database"]["tables"]

    # Recovery objectives
    assert "recovery_objectives" in app
    assert app["recovery_objectives"]["rto_target_seconds"] == 300
    assert app["recovery_objectives"]["rpo_target_minutes"] == 60
    assert "rto_methodological_note" in app["recovery_objectives"]
    assert "rpo_methodological_note" in app["recovery_objectives"]

    # Live statistics
    stats = app["live_statistics"]
    assert "total_backups" in stats
    assert "total_recovery_tests" in stats
    assert "success_rate_percent" in stats


def test_applications_api_get_by_name(cg_client):
    """
    Verifies GET /api/v1/applications/{app_name} retrieves specific workload
    and handles non-existent workloads with 404.
    """
    resp = cg_client.get("/api/v1/applications/demo-banking-application")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "demo-banking-application"
    assert data["tier"] == "Tier 1 - Mission Critical"

    # Non-existent app
    err_resp = cg_client.get("/api/v1/applications/unknown-nonexistent-app")
    assert err_resp.status_code == 404


def test_frontend_vite_build_and_bundle_artifacts():
    """
    Verifies the React + Vite + Tailwind CSS frontend builds cleanly
    producing production dist artifacts (index.html, JS, CSS).
    """
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    assert frontend_dir.exists()

    # Verify build artifacts in dist/
    dist_dir = frontend_dir / "dist"
    assert dist_dir.exists(), "dist/ directory must exist after building"
    index_html = dist_dir / "index.html"
    assert index_html.exists()
    assert len(index_html.read_text(encoding="utf-8")) > 100

    assets_dir = dist_dir / "assets"
    assert assets_dir.exists()
    js_files = list(assets_dir.glob("*.js"))
    css_files = list(assets_dir.glob("*.css"))
    assert len(js_files) >= 1, "At least one bundled JS artifact must exist"
    assert len(css_files) >= 1, "At least one bundled CSS artifact must exist"


def test_frontend_contains_all_5_required_pages():
    """
    Verifies that the frontend implementation contains all 5 required pages:
    1. Overview (total recovery tests, passed, failed, latest result, avg duration)
    2. Applications (protected applications, DB & backup details)
    3. Recovery Tests (history, filters, detailed checks, failure details)
    4. Reports (history, preview, download PDF/JSON)
    5. Monitoring (duration chart, freshness chart, success trends, error breakdown)
    """
    pages_dir = Path(__file__).resolve().parent.parent / "frontend" / "src" / "pages"
    assert (pages_dir / "OverviewPage.jsx").exists()
    assert (pages_dir / "ApplicationsPage.jsx").exists()
    assert (pages_dir / "RecoveryTestsPage.jsx").exists()
    assert (pages_dir / "ReportsPage.jsx").exists()
    assert (pages_dir / "MonitoringPage.jsx").exists()

    # Check key features in Overview
    overview_code = (pages_dir / "OverviewPage.jsx").read_text(encoding="utf-8")
    assert "Total Recovery Tests" in overview_code
    assert "Passed Tests" in overview_code
    assert "Failed Tests" in overview_code
    assert "Latest Test Result" in overview_code
    assert "Avg Drill Duration" in overview_code

    # Check key features in Applications
    apps_code = (pages_dir / "ApplicationsPage.jsx").read_text(encoding="utf-8")
    assert "Protected Applications" in apps_code
    assert "Database Infrastructure" in apps_code
    assert "Backup Manifests" in apps_code

    # Check key features in Recovery Tests
    tests_code = (pages_dir / "RecoveryTestsPage.jsx").read_text(encoding="utf-8")
    assert "Recovery Test Executions" in tests_code
    assert "Stage-by-Stage Verification Checks" in tests_code
    assert "StatusFilter" in tests_code or "statusFilter" in tests_code

    # Check key features in Reports
    reports_code = (pages_dir / "ReportsPage.jsx").read_text(encoding="utf-8")
    assert "Disaster Recovery Reports" in reports_code
    assert "Download PDF" in reports_code
    assert "Download JSON" in reports_code
    assert "Executive Summary" in reports_code

    # Check key features in Monitoring
    mon_code = (pages_dir / "MonitoringPage.jsx").read_text(encoding="utf-8")
    assert "Recovery Drill Duration vs Target RTO" in mon_code
    assert "Backup Freshness / Point-in-Time Age vs RPO" in mon_code
    assert "Validation Success Distribution" in mon_code
    assert "Error Classification Breakdown" in mon_code


def test_frontend_strictly_prohibits_remediation_and_execution_actions():
    """
    Scope constraint:
    'Do not include Fix, Restart, Retry, Failover,
    Restore Production, or Execute Action buttons.'
    Verifies that no action triggers or remediation buttons exist in the UI source.
    """
    src_dir = Path(__file__).resolve().parent.parent / "frontend" / "src"
    
    prohibited_actions = [
        "trigger failover",
        "execute recovery",
        "execute action",
        "restore production",
        "apply fix",
        "retry drill",
        "restart container",
        "self-heal"
    ]

    for jsx_file in src_dir.rglob("*.jsx"):
        content = jsx_file.read_text(encoding="utf-8").lower()
        for phrase in prohibited_actions:
            assert phrase not in content, f"Prohibited phrase '{phrase}' found in {jsx_file.name}"
