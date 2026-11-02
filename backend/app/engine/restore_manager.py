"""
CloudGuard Isolated Restore Manager.
Enforces Rule 7: Strict isolation guard ensures the primary database can NEVER be targeted for restore.
Restores snapshot into an isolated sandbox database and measures Recovery Time (RTO).
"""
import json
import time
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import create_engine, text, Table, MetaData
from backend.app.models.base import Base
from backend.app.schemas.restore import IsolatedRestoreResult
from backend.app.storage.base import DRStorageProvider
from backend.app.storage.local import LocalFileSystemStorage
from backend.app.core.exceptions import UnsafeRestoreTargetError, CorruptedBackupError, IsolatedRestoreError
from backend.app.core.logging import logger


class IsolatedRestoreManager:
    def __init__(
        self,
        primary_db_url: str,
        isolated_target_db_url: str,
        storage_provider: DRStorageProvider | None = None
    ):
        self.primary_db_url = primary_db_url
        self.isolated_target_db_url = isolated_target_db_url
        self.storage = storage_provider or LocalFileSystemStorage()
        
        # Enforce safety isolation immediately upon instantiation
        self.assert_isolated_target_safety(self.isolated_target_db_url)
        self.restore_engine = create_engine(self.isolated_target_db_url)

    def assert_isolated_target_safety(self, target_url: str) -> None:
        """
        Critical DR Guardrail:
        Asserts that the restore target is an isolated sandbox and cannot overwrite production!
        """
        primary_norm = self.primary_db_url.strip().lower().rstrip("/")
        target_norm = target_url.strip().lower().rstrip("/")

        if primary_norm == target_norm:
            raise UnsafeRestoreTargetError(
                f"FATAL SAFETY INTERLOCK: Restore target '{target_url}' matches primary production database! "
                "CloudGuard aborted restore drill to protect production data."
            )

        # Disallow restore to databases explicitly named 'prod' or 'primary' unless clearly marked as test/restore
        if ("prod" in target_norm or "primary" in target_norm) and not ("test" in target_norm or "isolated" in target_norm or "sandbox" in target_norm):
            raise UnsafeRestoreTargetError(
                f"Target database name '{target_url}' indicates production environment. "
                "Disaster recovery restore drills must be performed against an isolated test target."
            )

    def execute_isolated_restore(self, backup_id: str, storage_path: str) -> IsolatedRestoreResult:
        """
        Executes isolated restore drill from backup into sandbox DB.
        Returns detailed execution metrics including duration for RTO calculation.
        """
        restore_id = f"cg-rst-{uuid.uuid4().hex[:12]}"
        start_time = datetime.now(timezone.utc)
        start_perf = time.perf_counter()
        logger.info(f"Initiating Isolated Restore Drill [{restore_id}] for backup [{backup_id}]...")

        try:
            # 1. Read manifest and payload from storage
            manifest = self.storage.read_manifest(storage_path)
            raw_payload_bytes = self.storage.read_backup(storage_path)

            # 2. Verify SHA-256 Checksum integrity
            computed_checksum = hashlib.sha256(raw_payload_bytes).hexdigest()
            expected_checksum = manifest.get("checksum_sha256")

            if computed_checksum != expected_checksum:
                raise CorruptedBackupError(
                    f"Integrity Check Failed: Backup payload checksum [{computed_checksum[:12]}] "
                    f"does not match manifest [{expected_checksum[:12] if expected_checksum else 'None'}]."
                )

            # 3. Parse backup payload
            try:
                payload_json = json.loads(raw_payload_bytes.decode("utf-8"))
                tables_data: Dict[str, List[Dict[str, Any]]] = payload_json.get("tables", {})
            except Exception as parse_err:
                raise CorruptedBackupError(f"Corrupted or invalid JSON in backup payload: {parse_err}")

            # 4. Clean and recreate tables in the ISOLATED sandbox target
            Base.metadata.drop_all(self.restore_engine)
            Base.metadata.create_all(self.restore_engine)

            tables_restored = 0
            records_restored = 0

            # 5. Restore tables in dependency order (Organizations -> Users -> Orders -> OrderItems -> AuditLogs)
            dependency_order = ["organizations", "users", "orders", "order_items", "audit_logs"]
            all_tables = list(tables_data.keys())
            sorted_tables = [t for t in dependency_order if t in all_tables] + [t for t in all_tables if t not in dependency_order]

            with self.restore_engine.begin() as conn:
                for table_name in sorted_tables:
                    rows = tables_data[table_name]
                    if not rows:
                        tables_restored += 1
                        continue

                    target_table = Base.metadata.tables.get(table_name)
                    if target_table is None:
                        # Fallback reflection if dynamic table
                        target_table = Table(table_name, MetaData(), autoload_with=self.restore_engine)

                    # Normalize ISO datetimes back to python datetimes for SQLAlchemy
                    cleaned_rows = []
                    for row in rows:
                        cleaned = {}
                        for col_name, val in row.items():
                            if isinstance(val, str) and ("T" in val or "-" in val) and len(val) >= 19:
                                try:
                                    cleaned[col_name] = datetime.fromisoformat(val)
                                    continue
                                except ValueError:
                                    pass
                            cleaned[col_name] = val
                        cleaned_rows.append(cleaned)

                    conn.execute(target_table.insert(), cleaned_rows)
                    tables_restored += 1
                    records_restored += len(cleaned_rows)

            duration_seconds = round(time.perf_counter() - start_perf, 3)
            end_time = datetime.now(timezone.utc)

            logger.info(
                f"Isolated Restore Drill [{restore_id}] completed successfully: "
                f"{records_restored} records across {tables_restored} tables in {duration_seconds}s."
            )

            # Sanitize connection string for reporting (hide password)
            sanitized_target = self.isolated_target_db_url.split("@")[-1] if "@" in self.isolated_target_db_url else self.isolated_target_db_url

            return IsolatedRestoreResult(
                restore_id=restore_id,
                backup_id=backup_id,
                target_database_sanitized=sanitized_target,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration_seconds,
                tables_restored=tables_restored,
                records_restored=records_restored,
                status="SUCCESS"
            )

        except (UnsafeRestoreTargetError, CorruptedBackupError):
            raise
        except Exception as e:
            duration_seconds = round(time.perf_counter() - start_perf, 3)
            logger.error(f"Isolated Restore Drill [{restore_id}] failed: {str(e)}", exc_info=True)
            raise IsolatedRestoreError(f"Isolated restore drill failed: {str(e)}")
