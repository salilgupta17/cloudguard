"""
BackupMetadata Model - CloudGuard Backup Catalog.
Tracks backup snapshots, cryptographic hashes, schema versions, source databases, and manifests.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text
try:
    from app.database import Base
except ImportError:
    from ..database import Base


class BackupMetadata(Base):
    __tablename__ = "backup_metadata"

    backup_id = Column(String(64), primary_key=True)
    application_name = Column(String(120), nullable=False, index=True)
    storage_path = Column(String(512), nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    records_count = Column(Integer, default=0, nullable=False)
    source_database = Column(String(120), default="cloudguard_primary", nullable=False)
    schema_version = Column(String(32), default="1.0.0", nullable=False)
    manifest_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
