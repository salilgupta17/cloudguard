"""
Target Application API Validator.
Tests whether the restored container / application responds to health and data endpoints.
"""
from typing import Dict, Any, List
import httpx


class ApiValidator:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def validate_application_endpoints(self) -> Dict[str, Any]:
        """
        Runs automated health, readiness, and sanity query checks against restored app.
        """
        results = {
            "passed": True,
            "target_url": self.base_url,
            "probes": {},
            "errors": []
        }

        probes_to_test = [
            ("liveness", "/health", 200),
            ("readiness", "/ready", 200),
            ("business_customers", "/api/v1/customers", 200),
            ("business_orders", "/api/v1/orders", 200)
        ]

        with httpx.Client(timeout=self.timeout) as client:
            for probe_name, path, expected_status in probes_to_test:
                url = f"{self.base_url}{path}"
                try:
                    resp = client.get(url)
                    passed = (resp.status_code == expected_status)
                    results["probes"][probe_name] = {
                        "path": path,
                        "status_code": resp.status_code,
                        "passed": passed
                    }
                    if not passed:
                        results["passed"] = False
                        results["errors"].append(f"Probe '{probe_name}' returned HTTP {resp.status_code}, expected {expected_status}")
                except Exception as e:
                    results["passed"] = False
                    err_msg = f"Connection failed to {url}: {str(e)}"
                    results["probes"][probe_name] = {
                        "path": path,
                        "passed": False,
                        "error": err_msg
                    }
                    results["errors"].append(err_msg)

        return results
