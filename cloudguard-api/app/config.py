"""
Configuration Settings for CloudGuard API.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CloudGuard Disaster Recovery API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text" # "text" or "json"

    # CloudGuard API Metadata Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data/cloudguard.db"
    )

    # Monitored Primary Database
    PRIMARY_DATABASE_URL: str = os.getenv(
        "PRIMARY_DATABASE_URL",
        "sqlite:///./data/demo_banking.db"
    )

    # Isolated Target Database for DR Restore Drill
    RESTORE_TEST_DATABASE_URL: str = os.getenv(
        "RESTORE_TEST_DATABASE_URL",
        "sqlite:///./data/isolated_restore.db"
    )

    # API endpoints for validation
    DEMO_APP_API_URL: str = os.getenv("DEMO_APP_API_URL", "http://localhost:8001")
    RESTORED_APP_API_URL: str = os.getenv("RESTORED_APP_API_URL", "http://localhost:8002")

    # Local backup and reports directories
    BACKUP_DIR: Path = Path(os.getenv("BACKUP_DIR", "./backups"))
    REPORTS_DIR: Path = Path(os.getenv("REPORTS_DIR", "./reports"))

    # SLAs
    TARGET_RTO_SECONDS: float = 300.0
    TARGET_RPO_MINUTES: float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)
