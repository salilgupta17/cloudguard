"""
CloudGuard Configuration Management with Pydantic Settings.
Enforces validation rules, execution modes (LOCAL vs AWS), and safety isolation.
"""
from typing import Literal, List
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from backend.app.core.exceptions import UnsafeRestoreTargetError


class Settings(BaseSettings):
    # App & Environment
    APP_NAME: str = "CloudGuard Disaster Recovery Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Execution Mode: LOCAL or AWS
    EXECUTION_MODE: Literal["LOCAL", "AWS"] = "LOCAL"
    
    # Database Settings
    PRIMARY_DATABASE_URL: str = Field(
        default="sqlite:///./data/primary_monitored.db",
        description="Connection URL for the primary monitored application database"
    )
    RESTORE_TEST_DATABASE_URL: str = Field(
        default="sqlite:///./data/isolated_restore_test.db",
        description="Isolated sandbox target database used strictly for restore drills"
    )
    
    # Local DR Storage
    LOCAL_BACKUP_DIR: Path = Field(
        default=Path("./backups"),
        description="Directory where local backup snapshots and manifests are stored"
    )
    
    # Disaster Recovery SLAs & Targets
    TARGET_RTO_SECONDS: int = Field(
        default=300,
        description="Target Recovery Time Objective in seconds (default: 5 minutes)"
    )
    TARGET_RPO_MINUTES: int = Field(
        default=60,
        description="Target Recovery Point Objective in minutes (default: 1 hour)"
    )
    BACKUP_RETENTION_DAYS: int = Field(default=30)
    
    # AWS Mode Configurations
    AWS_REGION: str = "us-east-1"
    AWS_S3_DR_BUCKET: str = "cloudguard-dr-vault-us-east-1"
    AWS_BACKUP_VAULT_NAME: str = "cloudguard-dr-backup-vault"
    AWS_RDS_SOURCE_INSTANCE_ID: str = "cloudguard-primary-rds"
    AWS_RDS_RESTORE_TEST_SUBNET_GROUP: str = "cloudguard-isolated-subnet-group"
    AWS_RDS_RESTORE_SECURITY_GROUP_ID: str = "sg-0123456789abcdef0"
    
    # API & CORS
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_isolation_safety(self) -> "Settings":
        """
        Enforce DR Rule 7: Never restore over the production database!
        Guarantees that Primary and Restore Target databases can NEVER be identical.
        """
        primary_clean = self.PRIMARY_DATABASE_URL.strip().lower()
        restore_clean = self.RESTORE_TEST_DATABASE_URL.strip().lower()
        
        if primary_clean == restore_clean:
            raise UnsafeRestoreTargetError(
                f"CRITICAL SAFETY VIOLATION: RESTORE_TEST_DATABASE_URL cannot be identical to PRIMARY_DATABASE_URL! "
                f"Both point to: {self.PRIMARY_DATABASE_URL}. "
                "CloudGuard requires an isolated target database to prevent data corruption."
            )
        
        # Ensure local backup directory exists
        self.LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        return self


settings = Settings()
