"""
Validation Engine Orchestrator.
Combines Database parity validation and API health validation into unified DR test results.
"""
import json
from typing import Dict, Any, List
try:
    from app.db_validator import DatabaseValidator
    from app.api_validator import ApiValidator
except ImportError:
    from .db_validator import DatabaseValidator
    from .api_validator import ApiValidator


class ValidationEngine:
    def __init__(
        self,
        primary_db_url: str,
        restored_db_url: str,
        target_app_url: str | None = None
    ):
        self.db_validator = DatabaseValidator(primary_db_url, restored_db_url)
        self.target_app_url = target_app_url
        self.api_validator = ApiValidator(target_app_url) if target_app_url else None

    def run_full_validation(self) -> Dict[str, Any]:
        """
        Executes complete verification pipeline:
        - DB Schema Parity
        - DB Row Counts
        - DB Checksums
        - Container API Probes (if URL provided)
        """
        db_results = self.db_validator.validate_schema_and_parity()
        api_results = self.api_validator.validate_application_endpoints() if self.api_validator else None

        overall_passed = db_results["passed"] and (api_results["passed"] if api_results else True)

        findings: List[str] = list(db_results.get("errors", []))
        if api_results and api_results.get("errors"):
            findings.extend(api_results["errors"])

        return {
            "overall_passed": overall_passed,
            "database_validation": db_results,
            "api_validation": api_results,
            "findings": findings
        }
