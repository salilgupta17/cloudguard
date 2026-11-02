"""
CloudGuard Backup Manager.
Creates verified snapshot dumps with per-table and archive SHA-256 checksums and manifests.
"""
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from backend.app.schemas.backup import BackupManifest, TableBackupSummary, BackupCreateResponse
from backend.app.storage.base import DRStorageProvider
from backend.app.storage.local import LocalFileSystemStorage
from backend.app.core.exceptions import BackupCreationError
from backend.app.core.logging import logger


class BackupManager:
    def __init__(self, primary_db_url: str, storage_provider: DRStorageProvider | None = None):
        self.primary_db_url = primary_db_url
        self.storage = storage_provider or LocalFileSystemStorage()
        self.engine = create_engine(primary_db_url)

    def create_backup(self, description: str = "Disaster Recovery Drill Snapshot") -> BackupCreateResponse:
        """
        Executes a consistent snapshot extraction from the primary database,
        computes cryptographic checksums, generates metadata manifest, and stores the bundle.
        """
        backup_id = f"cg-bkp-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc)
        logger.info(f"Initiating DR Backup [{backup_id}] from primary DB...")

        try:
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            
            # Filter internal/system or CloudGuard reporting tables if present
            tracked_tables = [
                t for t in table_names 
                if not t.startswith("cg_") and not t.startswith("sqlite_")
            ]

            payload_data: Dict[str, List[Dict[str, Any]]] = {}
            tables_manifest: Dict[str, TableBackupSummary] = {}
            total_records = 0

            with self.engine.connect() as conn:
                for table_name in tracked_tables:
                    columns = [col["name"] for col in inspector.get_columns(table_name)]
                    
                    # Fetch all rows ordered by primary key if available for deterministic hashing
                    pk_constraint = inspector.get_pk_constraint(table_name)
                    pk_cols = pk_constraint.get("constrained_columns") or columns[:1]
                    order_clause = f" ORDER BY {', '.join(pk_cols)}" if pk_cols else ""

                    rows_result = conn.execute(text(f"SELECT * FROM {table_name}{order_clause}")).mappings().all()
                    
                    serialized_rows = []
                    for row in rows_result:
                        row_dict = {}
                        for k, v in dict(row).items():
                            if isinstance(v, datetime):
                                row_dict[k] = v.isoformat()
                            else:
                                row_dict[k] = v
                        serialized_rows.append(row_dict)

                    row_count = len(serialized_rows)
                    total_records += row_count
                    payload_data[table_name] = serialized_rows

                    # Calculate table checksum
                    table_json = json.dumps(serialized_rows, sort_keys=True)
                    table_hash = hashlib.sha256(table_json.encode("utf-8")).hexdigest()

                    tables_manifest[table_name] = TableBackupSummary(
                        table_name=table_name,
                        row_count=row_count,
                        columns=columns,
                        checksum=table_hash
                    )

            # Package full payload
            full_payload_json = json.dumps({
                "backup_id": backup_id,
                "timestamp": timestamp.isoformat(),
                "tables": payload_data
            }, sort_keys=True)
            payload_bytes = full_payload_json.encode("utf-8")
            full_checksum = hashlib.sha256(payload_bytes).hexdigest()
            size_bytes = len(payload_bytes)

            # Build Manifest
            manifest = BackupManifest(
                backup_id=backup_id,
                timestamp=timestamp,
                execution_mode="LOCAL",
                source_database_type=self.engine.name,
                tables_count=len(tracked_tables),
                total_records=total_records,
                size_bytes=size_bytes,
                checksum_sha256=full_checksum,
                tables=tables_manifest,
                metadata={"description": description}
            )

            # Persist bundle to storage provider
            storage_path = self.storage.save_backup(
                backup_id=backup_id,
                data_bytes=payload_bytes,
                manifest=manifest.model_dump(mode="json")
            )

            logger.info(
                f"DR Backup [{backup_id}] created successfully: "
                f"{total_records} records across {len(tracked_tables)} tables. SHA-256: {full_checksum[:12]}..."
            )

            return BackupCreateResponse(
                backup_id=backup_id,
                timestamp=timestamp,
                execution_mode="LOCAL",
                storage_path=storage_path,
                checksum_sha256=full_checksum,
                size_bytes=size_bytes,
                tables_count=len(tracked_tables),
                total_records=total_records,
                status="AVAILABLE"
            )

        except Exception as e:
            logger.error(f"Failed to create backup [{backup_id}]: {str(e)}", exc_info=True)
            raise BackupCreationError(f"Backup creation failed: {str(e)}")
