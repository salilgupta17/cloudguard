"""
Application and API Validator.
Tests whether the isolated restored application container starts,
responds to /health, /ready, and satisfies read-only business validation APIs.
"""
import time
from typing import List, Optional
from datetime import datetime, timezone

from .models import ValidationCheck, CheckStatus, ErrorCategory
from .app_runner import IsolatedAppLauncher


class ApplicationValidator:
    """
    Validates the isolated application instance:
    1. Docker container status
    2. Application startup
    3. GET /health
    4. GET /ready
    5. Read-only business API responses
    """

    def __init__(self, launcher: IsolatedAppLauncher):
        self.launcher = launcher

    def run_all_checks(self) -> List[ValidationCheck]:
        """Runs all 5 application checks and returns standardized ValidationCheck records."""
        checks: List[ValidationCheck] = []

        # 1. Container status
        container_check = self.check_container_status()
        checks.append(container_check)

        # 2. Application startup
        startup_check = self.check_startup()
        checks.append(startup_check)

        if startup_check.status != CheckStatus.PASS:
            for check_name, label in [
                ("application.health_endpoint", "GET /health liveness probe"),
                ("application.ready_endpoint", "GET /ready readiness probe"),
                ("application.readonly_business_apis", "Read-only business APIs probe")
            ]:
                checks.append(ValidationCheck(
                    check_name=check_name,
                    status=CheckStatus.SKIPPED,
                    duration=0.0,
                    observed_value="Application not running",
                    expected_value="Application running",
                    error_message=f"Skipped because application startup failed: {startup_check.error_message}",
                    error_category=ErrorCategory.APPLICATION_ERROR
                ))
            return checks

        # Retrieve client
        try:
            client = self.launcher.get_client()
        except Exception as e:
            err_msg = f"Failed to acquire application client: {str(e)}"
            for check_name in [
                "application.health_endpoint",
                "application.ready_endpoint",
                "application.readonly_business_apis"
            ]:
                checks.append(ValidationCheck(
                    check_name=check_name,
                    status=CheckStatus.ERROR,
                    duration=0.0,
                    observed_value="Client error",
                    expected_value="Active HTTP client",
                    error_message=err_msg,
                    error_category=ErrorCategory.APPLICATION_ERROR
                ))
            return checks

        # 3. GET /health
        health_check = self.check_health_endpoint(client)
        checks.append(health_check)

        # 4. GET /ready
        ready_check = self.check_ready_endpoint(client)
        checks.append(ready_check)

        # 5. Read-only business API responses
        biz_check = self.check_readonly_business_apis(client)
        checks.append(biz_check)

        return checks

    def check_container_status(self) -> ValidationCheck:
        """Verifies container status is RUNNING and Healthy."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            info = self.launcher.inspect_container_status()
            dur = time.perf_counter() - t0
            is_running = info.get("running", False)

            if is_running:
                return ValidationCheck(
                    check_name="application.container_status",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value=info,
                    expected_value={"status": "RUNNING", "running": True},
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                err = info.get("error") or f"Container '{info.get('container_name')}' is not in running state (status: {info.get('status')})"
                return ValidationCheck(
                    check_name="application.container_status",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value=info,
                    expected_value={"status": "RUNNING", "running": True},
                    error_message=err,
                    error_category=ErrorCategory.APPLICATION_ERROR,
                    timestamp=now
                )
        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="application.container_status",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value=None,
                expected_value={"status": "RUNNING"},
                error_message=f"Failed inspecting container status: {str(e)}",
                error_category=ErrorCategory.APPLICATION_ERROR,
                timestamp=now
            )

    def check_startup(self) -> ValidationCheck:
        """Verifies the application process initialized and bound correctly."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        dur = time.perf_counter() - t0
        if self.launcher.is_started:
            return ValidationCheck(
                check_name="application.startup",
                status=CheckStatus.PASS,
                duration=dur,
                observed_value="Application initialized and listening",
                expected_value="Application initialized and listening",
                error_message=None,
                error_category=None,
                timestamp=now
            )
        else:
            err = self.launcher._startup_error or "Application failed to start"
            return ValidationCheck(
                check_name="application.startup",
                status=CheckStatus.FAIL,
                duration=dur,
                observed_value="Application startup failed",
                expected_value="Application initialized and listening",
                error_message=err,
                error_category=ErrorCategory.APPLICATION_ERROR,
                timestamp=now
            )

    def check_health_endpoint(self, client) -> ValidationCheck:
        """Checks GET /health liveness probe."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            resp = client.get("/health")
            dur = time.perf_counter() - t0
            if resp.status_code == 200:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                return ValidationCheck(
                    check_name="application.health_endpoint",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value={"status_code": 200, "body": data},
                    expected_value={"status_code": 200},
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="application.health_endpoint",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value={"status_code": resp.status_code, "body": resp.text[:200]},
                    expected_value={"status_code": 200},
                    error_message=f"GET /health returned HTTP {resp.status_code}: {resp.text[:200]}",
                    error_category=ErrorCategory.API_ERROR,
                    timestamp=now
                )
        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="application.health_endpoint",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value="HTTP request failed",
                expected_value={"status_code": 200},
                error_message=f"GET /health request exception: {str(e)}",
                error_category=ErrorCategory.API_ERROR,
                timestamp=now
            )

    def check_ready_endpoint(self, client) -> ValidationCheck:
        """Checks GET /ready readiness probe verifying database connectivity."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            resp = client.get("/ready")
            dur = time.perf_counter() - t0
            if resp.status_code == 200:
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                return ValidationCheck(
                    check_name="application.ready_endpoint",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value={"status_code": 200, "body": data},
                    expected_value={"status_code": 200},
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="application.ready_endpoint",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value={"status_code": resp.status_code, "body": resp.text[:200]},
                    expected_value={"status_code": 200},
                    error_message=f"GET /ready returned HTTP {resp.status_code}: {resp.text[:200]}",
                    error_category=ErrorCategory.API_ERROR,
                    timestamp=now
                )
        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="application.ready_endpoint",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value="HTTP request failed",
                expected_value={"status_code": 200},
                error_message=f"GET /ready request exception: {str(e)}",
                error_category=ErrorCategory.API_ERROR,
                timestamp=now
            )

    def check_readonly_business_apis(self, client) -> ValidationCheck:
        """
        Executes read-only business validation APIs:
        - /api/v1/validation/summary
        - /api/v1/validation/customers/export
        - /api/v1/validation/accounts/export
        - /api/v1/validation/ledger/integrity
        """
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        endpoints = [
            ("/api/v1/validation/summary", "Summary Audit"),
            ("/api/v1/validation/customers/export", "Customers Export"),
            ("/api/v1/validation/accounts/export", "Accounts Export"),
            ("/api/v1/validation/ledger/integrity", "Ledger Integrity Verification")
        ]

        probes_results = {}
        discrepancies = []

        try:
            for path, label in endpoints:
                resp = client.get(path)
                status_ok = (resp.status_code == 200)
                body = resp.json() if status_ok and resp.headers.get("content-type", "").startswith("application/json") else {}

                probes_results[path] = {
                    "label": label,
                    "status_code": resp.status_code,
                    "passed": status_ok
                }

                if not status_ok:
                    discrepancies.append(f"{label} ({path}) returned HTTP {resp.status_code}")
                elif path == "/api/v1/validation/ledger/integrity":
                    if not body.get("integrity_passed", True):
                        discrepancies.append(f"Ledger integrity API reported internal discrepancies: {body.get('discrepancies_count', 0)}")

            dur = time.perf_counter() - t0
            if not discrepancies:
                return ValidationCheck(
                    check_name="application.readonly_business_apis",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value={"probes": probes_results, "all_probes_passed": True},
                    expected_value={"all_probes_passed": True},
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="application.readonly_business_apis",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value={"probes": probes_results, "all_probes_passed": False},
                    expected_value={"all_probes_passed": True},
                    error_message="; ".join(discrepancies),
                    error_category=ErrorCategory.API_ERROR,
                    timestamp=now
                )

        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="application.readonly_business_apis",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value="Exception probing business endpoints",
                expected_value={"all_probes_passed": True},
                error_message=f"Business API validation exception: {str(e)}",
                error_category=ErrorCategory.API_ERROR,
                timestamp=now
            )
