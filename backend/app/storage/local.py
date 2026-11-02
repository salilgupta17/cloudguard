"""
Local Filesystem Storage Provider for CloudGuard Backups.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from backend.app.storage.base import DRStorageProvider
from backend.app.core.exceptions import CorruptedBackupError
from backend.app.core.logging import logger


class LocalFileSystemStorage(DRStorageProvider):
    def __init__(self, base_dir: Path | str = "./backups"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_backup(self, backup_id: str, data_bytes: bytes, manifest: Dict[str, Any]) -> str:
        backup_file = self.base_dir / f"{backup_id}.dump"
        manifest_file = self.base_dir / f"{backup_id}.manifest.json"

        # Write data payload
        backup_file.write_bytes(data_bytes)
        
        # Write metadata manifest
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        
        logger.info(f"Saved local backup bundle [{backup_id}] to {backup_file}")
        return str(backup_file.resolve())

    def read_backup(self, storage_path: str) -> bytes:
        p = Path(storage_path)
        if not p.exists():
            raise CorruptedBackupError(f"Backup file not found at path: {storage_path}")
        return p.read_bytes()

    def read_manifest(self, storage_path: str) -> Dict[str, Any]:
        p = Path(storage_path)
        manifest_path = p.with_suffix(".manifest.json")
        if not manifest_path.exists():
            # Try appending if suffix manipulation didn't hit
            manifest_path = Path(f"{storage_path}.manifest.json")
            if not manifest_path.exists():
                raise CorruptedBackupError(f"Manifest file missing for backup: {storage_path}")
        
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise CorruptedBackupError(f"Failed to parse backup manifest: {e}")

    def list_backups(self) -> List[Dict[str, Any]]:
        backups = []
        for manifest_file in self.base_dir.glob("*.manifest.json"):
            try:
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                backups.append(manifest)
            except Exception as e:
                logger.warning(f"Error reading manifest {manifest_file}: {e}")
        return sorted(backups, key=lambda x: x.get("timestamp", ""), reverse=True)
