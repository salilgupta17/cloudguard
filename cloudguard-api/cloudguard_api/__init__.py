"""
CloudGuard API Package.
"""
import sys
import os

# Add parent directory to path so relative imports inside app work smoothly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.database import engine, Base, get_db
from app.config import settings
from app.models import RecoveryTest, BackupMetadata, ValidationResult, RecoveryReport
from app.main import app

__all__ = [
    "engine",
    "Base",
    "get_db",
    "settings",
    "RecoveryTest",
    "BackupMetadata",
    "ValidationResult",
    "RecoveryReport",
    "app",
]
