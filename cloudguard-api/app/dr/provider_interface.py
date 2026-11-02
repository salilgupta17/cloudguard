"""
Abstract Interface for Disaster Recovery Providers.
Prepares contract for Local execution (PostgreSQL/pg_dump) and future AWS Backup integration.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class AbstractDisasterRecoveryProvider(ABC):
    @abstractmethod
    def create_backup(self, source_db_url: str, backup_id: str, description: str = "") -> Dict[str, Any]:
        """
        Executes backup dump and produces manifest metadata.
        Returns dictionary containing:
        - backup_id
        - storage_path
        - size_bytes
        - checksum_sha256
        - records_count
        - manifest_dict
        """
        pass

    @abstractmethod
    def restore_backup(self, backup_path: str, source_db_url: str, target_db_url: str) -> Dict[str, Any]:
        """
        Restores backup into an isolated target database with safety verification.
        Returns dictionary containing:
        - success: bool
        - duration_seconds: float
        - logs: str
        - target_sanitized: str
        - error: Optional[str]
        """
        pass

    @abstractmethod
    def cleanup_target(self, target_db_url: str) -> bool:
        """
        Safely disposes of ephemeral isolated test database resources.
        """
        pass
