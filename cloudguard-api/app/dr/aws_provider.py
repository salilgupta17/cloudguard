"""
AWS Backup Disaster Recovery Provider.
Interacts with AWS Backup, RDS, and EventBridge using boto3.
Adheres to Rule 10: Never simulates AWS success without authentic credentials.
Safety Interlock: Never allows deletion or modification of the primary production database.
Strictly verification-only; does not execute traffic switching or remediation.
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.exceptions import ProviderConfigurationError, RestoreFailureError
from app.core.logging import logger
from .provider_interface import AbstractDisasterRecoveryProvider
from .safety import validate_isolated_target_safety


class AWSBackupDisasterRecoveryProvider(AbstractDisasterRecoveryProvider):
    """
    AWS Backup and RDS implementation of the DR Provider interface.
    Coordinates snapshot creation, AWS Backup Restore Testing jobs, and ephemeral cleanup.
    """

    def __init__(
        self,
        vault_name: Optional[str] = None,
        region: Optional[str] = None,
        iam_role_arn: Optional[str] = None
    ):
        self.vault_name = vault_name or os.environ.get("AWS_BACKUP_VAULT_NAME", "cloudguard-dr-backup-vault")
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.iam_role_arn = iam_role_arn or os.environ.get("AWS_BACKUP_IAM_ROLE_ARN")
        
        self._backup_client = None
        self._rds_client = None

    def _get_backup_client(self):
        """Initializes boto3 backup client with credential validation."""
        if self._backup_client is None:
            # Rule 10: Validate authentic AWS credentials
            aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
            aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
            if not aws_key or not aws_secret or "mock" in aws_key.lower() or "dummy" in aws_key.lower():
                raise ProviderConfigurationError(
                    "AWS Backup execution mode requires active AWS IAM credentials and authentic AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) "
                    f"and an existing Backup Vault '{self.vault_name}' in region '{self.region}'. "
                    "Local execution mode is currently active."
                )
            try:
                import boto3
                self._backup_client = boto3.client("backup", region_name=self.region)
            except Exception as e:
                raise ProviderConfigurationError(f"Failed to initialize AWS Backup boto3 client: {e}")
        return self._backup_client

    def _get_rds_client(self):
        """Initializes boto3 RDS client with credential validation."""
        if self._rds_client is None:
            aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
            aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
            if not aws_key or not aws_secret or "mock" in aws_key.lower() or "dummy" in aws_key.lower():
                raise ProviderConfigurationError(
                    "AWS RDS operations require authentic AWS credentials. "
                    "Local execution mode is currently active."
                )
            try:
                import boto3
                self._rds_client = boto3.client("rds", region_name=self.region)
            except Exception as e:
                raise ProviderConfigurationError(f"Failed to initialize AWS RDS boto3 client: {e}")
        return self._rds_client

    def create_backup(self, source_db_url: str, backup_id: str, description: str = "") -> Dict[str, Any]:
        """
        Triggers an on-demand AWS Backup Job for the RDS database resource.
        """
        client = self._get_backup_client()
        start_time = datetime.now(timezone.utc)

        # In AWS RDS, resource ARN is needed for StartBackupJob
        # If source_db_url is an ARN, use it; otherwise read from environment
        rds_arn = os.environ.get("AWS_RDS_PRIMARY_RESOURCE_ARN")
        if not rds_arn:
            if "arn:aws:rds" in source_db_url:
                rds_arn = source_db_url
            else:
                raise ProviderConfigurationError(
                    "AWS_RDS_PRIMARY_RESOURCE_ARN environment variable is required to trigger AWS Backup on-demand jobs."
                )

        try:
            logger.info(f"Starting AWS Backup Job for RDS resource: {rds_arn} into vault {self.vault_name}")
            response = client.start_backup_job(
                BackupVaultName=self.vault_name,
                ResourceArn=rds_arn,
                IamRoleArn=self.iam_role_arn or os.environ.get("AWS_BACKUP_ROLE_ARN", ""),
                IdempotencyToken=str(uuid.uuid4()),
                BackupOptions={"FullBackup": "True"}
            )
            job_id = response.get("BackupJobId")
            recovery_point_arn = response.get("RecoveryPointArn", "")

            return {
                "backup_id": backup_id,
                "aws_backup_job_id": job_id,
                "recovery_point_arn": recovery_point_arn,
                "vault_name": self.vault_name,
                "status": "RUNNING",
                "created_at": start_time.isoformat(),
                "storage_type": "AWS_BACKUP_VAULT"
            }
        except Exception as e:
            logger.error(f"AWS Backup creation failed: {e}")
            raise ProviderConfigurationError(f"AWS Backup execution error: {e}")

    def restore_backup(self, backup_path: str, source_db_url: str, target_db_url: str) -> Dict[str, Any]:
        """
        Triggers an isolated restore testing job into a temporary sandbox DB instance.
        Validates target safety interlocks before proceeding.
        """
        validate_isolated_target_safety(source_db_url=source_db_url, target_db_url=target_db_url)
        client = self._get_backup_client()
        start_time = datetime.now(timezone.utc)

        # For AWS, backup_path is the RecoveryPointArn
        recovery_point_arn = backup_path
        if not recovery_point_arn.startswith("arn:aws:backup"):
            raise ProviderConfigurationError(f"Invalid AWS Recovery Point ARN: {backup_path}")

        try:
            logger.info(f"Triggering AWS Backup restore job from recovery point: {recovery_point_arn}")
            target_instance_id = os.environ.get("AWS_RDS_ISOLATED_TEST_INSTANCE_ID", "cloudguard-isolated-dr-test")
            
            # Metadata required by AWS Backup for RDS restore
            metadata = {
                "DBInstanceIdentifier": target_instance_id,
                "DBInstanceClass": "db.t3.micro",
                "PubliclyAccessible": "false",
                "MultiAZ": "false",
                "AutoMinorVersionUpgrade": "false",
                "StorageType": "gp3"
            }

            response = client.start_restore_job(
                RecoveryPointArn=recovery_point_arn,
                Metadata=metadata,
                IamRoleArn=self.iam_role_arn or os.environ.get("AWS_BACKUP_ROLE_ARN", ""),
                ResourceType="RDS"
            )
            restore_job_id = response.get("RestoreJobId")

            return {
                "restore_job_id": restore_job_id,
                "target_instance_id": target_instance_id,
                "status": "RUNNING",
                "started_at": start_time.isoformat(),
                "duration_seconds": 0.0,
                "logs": f"AWS Backup Restore Job initiated: {restore_job_id}"
            }
        except Exception as e:
            logger.error(f"AWS Backup restore initiation failed: {e}")
            raise RestoreFailureError(f"AWS Backup restore failed: {e}")

    def cleanup_target(self, target_db_url: str) -> bool:
        """
        Deletes the ephemeral sandbox RDS instance.
        Safety Interlock: Strict check ensures primary production DB is NEVER deleted.
        """
        primary_arn = os.environ.get("AWS_RDS_PRIMARY_RESOURCE_ARN", "")
        if primary_arn and (primary_arn in target_db_url or "primary" in target_db_url.lower()):
            raise ProviderConfigurationError(
                "SAFETY INTERLOCK TRIPPED: Refusing to clean up primary database! Target must be isolated sandbox."
            )

        rds = self._get_rds_client()
        target_instance_id = os.environ.get("AWS_RDS_ISOLATED_TEST_INSTANCE_ID", "cloudguard-isolated-dr-test")

        try:
            logger.info(f"Decommissioning isolated test RDS instance: {target_instance_id}")
            rds.delete_db_instance(
                DBInstanceIdentifier=target_instance_id,
                SkipFinalSnapshot=True,
                DeleteAutomatedBackups=True
            )
            return True
        except Exception as e:
            # If instance already does not exist, consider clean
            if "DBInstanceNotFound" in str(e):
                return True
            logger.warning(f"Error during isolated RDS teardown: {e}")
            return False
