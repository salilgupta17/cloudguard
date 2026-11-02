"""
Database Parity, Relational Integrity, and Schema Compatibility Validator.
Executes deep database checks against an isolated restored database and
verifies records directly against the backup-specific test manifest.
"""
import time
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy import create_engine, inspect, text

from .models import ValidationCheck, CheckStatus, ErrorCategory


class DatabaseValidator:
    """
    Validates PostgreSQL / SQLite restored databases across:
    1. Connectivity
    2. Required tables
    3. Schema compatibility
    4. Expected test records (compared against backup test manifest)
    5. Foreign key consistency
    6. Transaction ledger integrity
    """

    EXPECTED_BANKING_TABLES = ["customers", "accounts", "transactions"]
    EXPECTED_COLUMNS = {
        "customers": ["id", "customer_number", "first_name", "last_name", "email", "phone", "kyc_status", "created_at"],
        "accounts": ["id", "customer_id", "account_number", "account_type", "balance_cents", "currency", "status", "created_at"],
        "transactions": ["id", "account_id", "reference_number", "transaction_type", "amount_cents", "balance_after_cents", "description", "status", "created_at"]
    }

    def __init__(
        self,
        arg1: Optional[str] = None,
        arg2: Optional[Any] = None,
        restored_db_url: Optional[str] = None,
        backup_manifest: Optional[Dict[str, Any]] = None,
        primary_db_url: Optional[str] = None
    ):
        """
        Flexible constructor supporting both:
        - Modern Phase 4: DatabaseValidator(restored_db_url, backup_manifest)
        - Backward Compatible: DatabaseValidator(primary_db_url, restored_db_url)
        """
        if arg1 and arg2 and isinstance(arg2, str) and "://" in arg2:
            # Called as DatabaseValidator(primary_url, restored_url)
            self.primary_db_url = arg1
            self.restored_db_url = arg2
            self.manifest = backup_manifest or {}
        else:
            self.restored_db_url = restored_db_url or arg1
            self.manifest = backup_manifest or (arg2 if isinstance(arg2, dict) else {})
            self.primary_db_url = primary_db_url

        connect_args = {"check_same_thread": False} if self.restored_db_url and self.restored_db_url.startswith("sqlite") else {}
        self.engine = create_engine(self.restored_db_url, connect_args=connect_args) if self.restored_db_url else None
        self.primary_engine = create_engine(self.primary_db_url) if self.primary_db_url else None

    def run_all_checks(self) -> List[ValidationCheck]:
        """Runs all 6 database checks and returns standardized ValidationCheck records."""
        checks: List[ValidationCheck] = []

        # 1. Connectivity
        conn_check = self.check_connectivity()
        checks.append(conn_check)

        if conn_check.status != CheckStatus.PASS:
            # If connectivity fails, dependent DB checks cannot proceed
            for check_name in [
                "database.required_tables",
                "database.schema_compatibility",
                "database.expected_records",
                "database.foreign_key_consistency",
                "database.transaction_integrity"
            ]:
                checks.append(ValidationCheck(
                    check_name=check_name,
                    status=CheckStatus.SKIPPED,
                    duration=0.0,
                    observed_value="Database unreachable",
                    expected_value="Reachable database",
                    error_message=f"Skipped because database connectivity check failed: {conn_check.error_message}",
                    error_category=ErrorCategory.DATABASE_ERROR
                ))
            return checks

        # 2. Required tables
        tables_check = self.check_required_tables()
        checks.append(tables_check)

        # 3. Schema compatibility
        schema_check = self.check_schema_compatibility()
        checks.append(schema_check)

        # 4. Expected test records (manifest comparison)
        records_check = self.check_expected_test_records()
        checks.append(records_check)

        # 5. Foreign key consistency
        fk_check = self.check_foreign_key_consistency()
        checks.append(fk_check)

        # 6. Transaction integrity
        tx_check = self.check_transaction_integrity()
        checks.append(tx_check)

        return checks

    def check_connectivity(self) -> ValidationCheck:
        """Verifies database connectivity via ping / test query."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            if not self.engine:
                raise ValueError("No restored database engine configured")
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="database.connectivity",
                status=CheckStatus.PASS,
                duration=dur,
                observed_value="Connected successfully",
                expected_value="Connected successfully",
                error_message=None,
                error_category=None,
                timestamp=now
            )
        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="database.connectivity",
                status=CheckStatus.FAIL,
                duration=dur,
                observed_value="Connection failed",
                expected_value="Connected successfully",
                error_message=f"Database connectivity failed: {str(e)}",
                error_category=ErrorCategory.DATABASE_ERROR,
                timestamp=now
            )

    def check_required_tables(self) -> ValidationCheck:
        """Verifies all required application tables exist in the restored database."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            insp = inspect(self.engine)
            existing_tables = set(insp.get_table_names())

            manifest_tables = self.manifest.get("tables", {})
            expected = list(manifest_tables.keys()) if manifest_tables else self.EXPECTED_BANKING_TABLES

            missing = [t for t in expected if t not in existing_tables]
            dur = time.perf_counter() - t0

            if not missing:
                return ValidationCheck(
                    check_name="database.required_tables",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value=sorted(list(existing_tables & set(expected))),
                    expected_value=sorted(expected),
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="database.required_tables",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value=sorted(list(existing_tables & set(expected))),
                    expected_value=sorted(expected),
                    error_message=f"Restored database is missing required tables: {missing}",
                    error_category=ErrorCategory.DATABASE_ERROR,
                    timestamp=now
                )
        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="database.required_tables",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value=None,
                expected_value=self.EXPECTED_BANKING_TABLES,
                error_message=f"Unexpected error inspecting database tables: {str(e)}",
                error_category=ErrorCategory.DATABASE_ERROR,
                timestamp=now
            )

    def check_schema_compatibility(self) -> ValidationCheck:
        """Verifies table columns match the expected application schema or manifest."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            insp = inspect(self.engine)
            discrepancies: List[str] = []
            observed_columns_summary = {}
            existing_tables = set(insp.get_table_names())

            manifest_tables = self.manifest.get("tables", {})
            expected_tables = manifest_tables.keys() if manifest_tables else self.EXPECTED_COLUMNS.keys()

            for table in expected_tables:
                if table not in existing_tables:
                    discrepancies.append(f"Table '{table}' missing for schema inspection")
                    continue

                actual_cols = {c["name"] for c in insp.get_columns(table)}
                observed_columns_summary[table] = sorted(list(actual_cols))

                if manifest_tables and table in manifest_tables and "columns" in manifest_tables[table]:
                    exp_cols = set(manifest_tables[table]["columns"])
                else:
                    exp_cols = set(self.EXPECTED_COLUMNS.get(table, []))

                if exp_cols:
                    missing_cols = exp_cols - actual_cols
                    if missing_cols:
                        discrepancies.append(f"Table '{table}' missing required columns: {sorted(list(missing_cols))}")

            dur = time.perf_counter() - t0
            if not discrepancies:
                return ValidationCheck(
                    check_name="database.schema_compatibility",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value=observed_columns_summary,
                    expected_value="All expected columns matched",
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="database.schema_compatibility",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value=observed_columns_summary,
                    expected_value="All expected columns matched",
                    error_message="; ".join(discrepancies),
                    error_category=ErrorCategory.DATABASE_ERROR,
                    timestamp=now
                )
        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="database.schema_compatibility",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value=None,
                expected_value="Valid schema",
                error_message=f"Schema compatibility inspection error: {str(e)}",
                error_category=ErrorCategory.DATABASE_ERROR,
                timestamp=now
            )

    def check_expected_test_records(self) -> ValidationCheck:
        """
        Compares restored records against the backup-specific test manifest,
        not current production data.
        """
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            manifest_tables = self.manifest.get("tables", {})
            total_expected_manifest = self.manifest.get("total_records")

            observed_counts = {}
            expected_counts = {}
            discrepancies = []
            total_observed = 0

            with self.engine.connect() as conn:
                insp = inspect(self.engine)
                existing = set(insp.get_table_names())

                tables_to_check = manifest_tables.keys() if manifest_tables else self.EXPECTED_BANKING_TABLES

                for tbl in tables_to_check:
                    if tbl not in existing:
                        discrepancies.append(f"Table '{tbl}' does not exist to count records")
                        continue

                    actual_count = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() or 0
                    observed_counts[tbl] = actual_count
                    total_observed += actual_count

                    if manifest_tables and tbl in manifest_tables:
                        exp_count = manifest_tables[tbl].get("row_count", 0)
                        expected_counts[tbl] = exp_count
                        if actual_count != exp_count:
                            discrepancies.append(
                                f"Table '{tbl}' record count mismatch: expected {exp_count} from manifest, observed {actual_count}"
                            )

                        exp_hash = manifest_tables[tbl].get("checksum_sha256")
                        if exp_hash and actual_count == exp_count:
                            rows = conn.execute(text(f"SELECT * FROM {tbl}")).mappings().all()
                            actual_hash = self._hash_rows(rows)
                            if actual_hash != exp_hash:
                                discrepancies.append(f"Table '{tbl}' checksum mismatch against manifest")

            if total_expected_manifest is not None:
                expected_counts["total_records"] = total_expected_manifest
                observed_counts["total_records"] = total_observed
                if total_observed != total_expected_manifest:
                    discrepancies.append(
                        f"Total records mismatch: expected {total_expected_manifest} from manifest, observed {total_observed}"
                    )

            dur = time.perf_counter() - t0

            if not discrepancies:
                return ValidationCheck(
                    check_name="database.expected_records",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value=observed_counts,
                    expected_value=expected_counts or observed_counts,
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="database.expected_records",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value=observed_counts,
                    expected_value=expected_counts,
                    error_message="; ".join(discrepancies),
                    error_category=ErrorCategory.DATA_INTEGRITY_ERROR,
                    timestamp=now
                )

        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="database.expected_records",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value=None,
                expected_value=self.manifest.get("tables"),
                error_message=f"Failed verifying expected test records against manifest: {str(e)}",
                error_category=ErrorCategory.DATA_INTEGRITY_ERROR,
                timestamp=now
            )

    def check_foreign_key_consistency(self) -> ValidationCheck:
        """Verifies relational integrity: no orphaned accounts or orphaned transactions."""
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            insp = inspect(self.engine)
            existing = set(insp.get_table_names())
            discrepancies = []

            with self.engine.connect() as conn:
                if "accounts" in existing and "customers" in existing:
                    orphan_accounts = conn.execute(text(
                        "SELECT COUNT(*) FROM accounts WHERE customer_id NOT IN (SELECT id FROM customers)"
                    )).scalar() or 0
                    if orphan_accounts > 0:
                        discrepancies.append(f"Detected {orphan_accounts} orphaned accounts with invalid customer_id")

                if "transactions" in existing and "accounts" in existing:
                    orphan_txns = conn.execute(text(
                        "SELECT COUNT(*) FROM transactions WHERE account_id NOT IN (SELECT id FROM accounts)"
                    )).scalar() or 0
                    if orphan_txns > 0:
                        discrepancies.append(f"Detected {orphan_txns} orphaned transactions with invalid account_id")

            dur = time.perf_counter() - t0
            if not discrepancies:
                return ValidationCheck(
                    check_name="database.foreign_key_consistency",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value={"orphaned_accounts": 0, "orphaned_transactions": 0},
                    expected_value={"orphaned_accounts": 0, "orphaned_transactions": 0},
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="database.foreign_key_consistency",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value={"violations": discrepancies},
                    expected_value={"orphaned_accounts": 0, "orphaned_transactions": 0},
                    error_message="; ".join(discrepancies),
                    error_category=ErrorCategory.DATA_INTEGRITY_ERROR,
                    timestamp=now
                )

        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="database.foreign_key_consistency",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value=None,
                expected_value={"orphaned_records": 0},
                error_message=f"Foreign key consistency check failed: {str(e)}",
                error_category=ErrorCategory.DATA_INTEGRITY_ERROR,
                timestamp=now
            )

    def check_transaction_integrity(self) -> ValidationCheck:
        """
        Audits financial ledger integrity:
        Verifies that account balances match the sum of credits minus debits,
        transaction amounts are strictly positive, and balances are non-negative.
        """
        t0 = time.perf_counter()
        now = datetime.now(timezone.utc).isoformat()
        try:
            insp = inspect(self.engine)
            existing = set(insp.get_table_names())
            if "accounts" not in existing or "transactions" not in existing:
                return ValidationCheck(
                    check_name="database.transaction_integrity",
                    status=CheckStatus.SKIPPED,
                    duration=time.perf_counter() - t0,
                    observed_value="Missing accounts or transactions table",
                    expected_value="Both tables present",
                    error_message="Cannot audit transaction integrity: accounts or transactions table missing",
                    error_category=ErrorCategory.DATA_INTEGRITY_ERROR,
                    timestamp=now
                )

            discrepancies = []
            audited_count = 0

            with self.engine.connect() as conn:
                neg_txns = conn.execute(text(
                    "SELECT COUNT(*) FROM transactions WHERE amount_cents <= 0"
                )).scalar() or 0
                if neg_txns > 0:
                    discrepancies.append(f"Found {neg_txns} transactions with non-positive amount")

                neg_accs = conn.execute(text(
                    "SELECT COUNT(*) FROM accounts WHERE balance_cents < 0"
                )).scalar() or 0
                if neg_accs > 0:
                    discrepancies.append(f"Found {neg_accs} accounts with negative balance")

                accounts = conn.execute(text("SELECT id, account_number, balance_cents FROM accounts")).mappings().all()
                audited_count = len(accounts)

                for acc in accounts:
                    acc_id = acc["id"]
                    stored_balance = acc["balance_cents"]

                    txns = conn.execute(text(
                        "SELECT transaction_type, amount_cents FROM transactions WHERE account_id = :acc_id"
                    ), {"acc_id": acc_id}).mappings().all()

                    calculated = 0
                    for tx in txns:
                        tx_type = tx["transaction_type"]
                        amt = tx["amount_cents"]
                        if tx_type in ["DEPOSIT", "TRANSFER_IN"]:
                            calculated += amt
                        elif tx_type in ["WITHDRAWAL", "TRANSFER_OUT"]:
                            calculated -= amt

                    if calculated != stored_balance:
                        discrepancies.append(
                            f"Account {acc['account_number']} balance discrepancy: stored={stored_balance}, calculated={calculated}"
                        )

            dur = time.perf_counter() - t0
            if not discrepancies:
                return ValidationCheck(
                    check_name="database.transaction_integrity",
                    status=CheckStatus.PASS,
                    duration=dur,
                    observed_value={"accounts_audited": audited_count, "ledger_integrity_passed": True},
                    expected_value={"ledger_integrity_passed": True},
                    error_message=None,
                    error_category=None,
                    timestamp=now
                )
            else:
                return ValidationCheck(
                    check_name="database.transaction_integrity",
                    status=CheckStatus.FAIL,
                    duration=dur,
                    observed_value={"accounts_audited": audited_count, "discrepancies": discrepancies},
                    expected_value={"ledger_integrity_passed": True},
                    error_message="; ".join(discrepancies),
                    error_category=ErrorCategory.DATA_INTEGRITY_ERROR,
                    timestamp=now
                )

        except Exception as e:
            dur = time.perf_counter() - t0
            return ValidationCheck(
                check_name="database.transaction_integrity",
                status=CheckStatus.ERROR,
                duration=dur,
                observed_value=None,
                expected_value={"ledger_integrity_passed": True},
                error_message=f"Transaction integrity check error: {str(e)}",
                error_category=ErrorCategory.DATA_INTEGRITY_ERROR,
                timestamp=now
            )

    def validate_schema_and_parity(self) -> Dict[str, Any]:
        """
        Backward compatibility helper comparing primary vs restored engines directly.
        Used by Phase 1/2 tests.
        """
        if not self.primary_engine or not self.engine:
            return {"passed": True, "tables_evaluated": 0, "table_reports": {}, "errors": []}

        p_insp = inspect(self.primary_engine)
        r_insp = inspect(self.engine)

        p_tables = [t for t in p_insp.get_table_names() if not t.startswith("alembic_") and not t.startswith("sqlite_")]
        r_tables = set(r_insp.get_table_names())

        results = {
            "passed": True,
            "tables_evaluated": len(p_tables),
            "table_reports": {},
            "errors": []
        }

        with self.primary_engine.connect() as p_conn, self.engine.connect() as r_conn:
            for table in p_tables:
                if table not in r_tables:
                    err = f"Table '{table}' missing in restored database"
                    results["passed"] = False
                    results["errors"].append(err)
                    results["table_reports"][table] = {"exists": False, "error": err}
                    continue

                p_cols = {c["name"] for c in p_insp.get_columns(table)}
                r_cols = {c["name"] for c in r_insp.get_columns(table)}
                missing_cols = list(p_cols - r_cols)

                p_count = p_conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
                r_count = r_conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
                row_parity = (p_count == r_count)

                p_rows = p_conn.execute(text(f"SELECT * FROM {table}")).mappings().all()
                r_rows = r_conn.execute(text(f"SELECT * FROM {table}")).mappings().all()

                p_hash = self._hash_rows(p_rows)
                r_hash = self._hash_rows(r_rows)
                checksum_parity = (p_hash == r_hash)

                table_passed = (len(missing_cols) == 0 and row_parity and checksum_parity)
                if not table_passed:
                    results["passed"] = False
                    if missing_cols:
                        results["errors"].append(f"Table '{table}' missing columns: {missing_cols}")
                    if not row_parity:
                        results["errors"].append(f"Table '{table}' row mismatch: {p_count} vs {r_count}")
                    if not checksum_parity and row_parity:
                        results["errors"].append(f"Table '{table}' checksum mismatch")

                results["table_reports"][table] = {
                    "exists": True,
                    "schema_matched": len(missing_cols) == 0,
                    "missing_columns": missing_cols,
                    "primary_row_count": p_count,
                    "restored_row_count": r_count,
                    "row_count_matched": row_parity,
                    "checksum_matched": checksum_parity,
                    "passed": table_passed
                }

        return results

    def _hash_rows(self, rows) -> str:
        serialized_rows = []
        for r in rows:
            row_dict = {}
            for k, v in dict(r).items():
                if isinstance(v, datetime):
                    row_dict[k] = v.isoformat()
                else:
                    row_dict[k] = v
            serialized_rows.append(row_dict)
        serialized_rows.sort(key=lambda x: json.dumps(x, sort_keys=True, default=str))
        payload = json.dumps(serialized_rows, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
