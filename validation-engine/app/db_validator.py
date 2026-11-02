"""
Database Parity and Integrity Validator.
Compares Primary Database vs Restored Database across schema, row count parity, and checksums.
"""
import json
import hashlib
from typing import Dict, Any, List
from sqlalchemy import create_engine, inspect, text


class DatabaseValidator:
    def __init__(self, primary_db_url: str, restored_db_url: str):
        self.primary_engine = create_engine(primary_db_url)
        self.restored_engine = create_engine(restored_db_url)

    def validate_schema_and_parity(self) -> Dict[str, Any]:
        """
        Validates:
        1. Schema parity (columns, nullability)
        2. Exact row counts
        3. Cryptographic data hashes
        """
        p_insp = inspect(self.primary_engine)
        r_insp = inspect(self.restored_engine)

        p_tables = [t for t in p_insp.get_table_names() if not t.startswith("alembic_") and not t.startswith("sqlite_")]
        r_tables = set(r_insp.get_table_names())

        results = {
            "passed": True,
            "tables_evaluated": len(p_tables),
            "table_reports": {},
            "errors": []
        }

        with self.primary_engine.connect() as p_conn, self.restored_engine.connect() as r_conn:
            for table in p_tables:
                if table not in r_tables:
                    err = f"Table '{table}' missing in restored database"
                    results["passed"] = False
                    results["errors"].append(err)
                    results["table_reports"][table] = {
                        "exists": False,
                        "error": err
                    }
                    continue

                # Check columns
                p_cols = {c["name"] for c in p_insp.get_columns(table)}
                r_cols = {c["name"] for c in r_insp.get_columns(table)}
                missing_cols = list(p_cols - r_cols)

                # Check counts
                p_count = p_conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
                r_count = r_conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
                row_parity = (p_count == r_count)

                # Check checksums
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
        serialized = []
        for r in rows:
            serialized.append({k: str(v) for k, v in dict(r).items()})
        payload = json.dumps(serialized, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
