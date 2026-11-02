"""
Abstract Storage Provider for CloudGuard Backups.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path


class DRStorageProvider(ABC):
    @abstractmethod
    def save_backup(self, backup_id: str, data_bytes: bytes, manifest: Dict[str, Any]) -> str:
        """Stores backup data and manifest. Returns the storage path/URI."""
        pass

    @abstractmethod
    def read_backup(self, storage_path: str) -> bytes:
        """Reads raw backup data from storage path/URI."""
        pass

    @abstractmethod
    def read_manifest(self, storage_path: str) -> Dict[str, Any]:
        """Retrieves backup metadata manifest."""
        pass

    @abstractmethod
    def list_backups(self) -> List[Dict[str, Any]]:
        """Returns list of available backups with their manifests."""
        pass
