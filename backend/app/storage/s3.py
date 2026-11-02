"""
AWS S3 Storage Provider for CloudGuard Backups.
Adheres to Rule 10: Never simulates AWS success without genuine cloud authentication.
"""
import json
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from backend.app.storage.base import DRStorageProvider
from backend.app.core.exceptions import ProviderConfigurationError, CorruptedBackupError
from backend.app.core.logging import logger


class S3StorageProvider(DRStorageProvider):
    def __init__(self, bucket_name: str, region_name: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self._s3_client = None

    def _get_client(self):
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client("s3", region_name=self.region_name)
                # Verify credentials and bucket connectivity
                self._s3_client.head_bucket(Bucket=self.bucket_name)
            except (NoCredentialsError, ClientError) as e:
                raise ProviderConfigurationError(
                    f"AWS S3 Connection Failed for bucket '{self.bucket_name}' in region '{self.region_name}'. "
                    f"Ensure valid AWS credentials/IAM role are configured. Details: {str(e)}"
                )
        return self._s3_client

    def save_backup(self, backup_id: str, data_bytes: bytes, manifest: Dict[str, Any]) -> str:
        s3 = self._get_client()
        backup_key = f"backups/{backup_id}.dump"
        manifest_key = f"backups/{backup_id}.manifest.json"

        s3.put_object(
            Bucket=self.bucket_name,
            Key=backup_key,
            Body=data_bytes,
            ServerSideEncryption="aws:kms"
        )
        s3.put_object(
            Bucket=self.bucket_name,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2).encode("utf-8"),
            ContentType="application/json"
        )

        s3_uri = f"s3://{self.bucket_name}/{backup_key}"
        logger.info(f"Successfully uploaded DR backup bundle to {s3_uri}")
        return s3_uri

    def read_backup(self, storage_path: str) -> bytes:
        s3 = self._get_client()
        # Parse s3://bucket/key
        key = storage_path.replace(f"s3://{self.bucket_name}/", "")
        try:
            resp = s3.get_object(Bucket=self.bucket_name, Key=key)
            return resp["Body"].read()
        except Exception as e:
            raise CorruptedBackupError(f"Failed to fetch S3 backup {storage_path}: {e}")

    def read_manifest(self, storage_path: str) -> Dict[str, Any]:
        s3 = self._get_client()
        key = storage_path.replace(f"s3://{self.bucket_name}/", "").replace(".dump", ".manifest.json")
        try:
            resp = s3.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(resp["Body"].read().decode("utf-8"))
        except Exception as e:
            raise CorruptedBackupError(f"Failed to fetch S3 backup manifest: {e}")

    def list_backups(self) -> List[Dict[str, Any]]:
        s3 = self._get_client()
        results = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix="backups/"):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".manifest.json"):
                    manifest_resp = s3.get_object(Bucket=self.bucket_name, Key=obj["Key"])
                    results.append(json.loads(manifest_resp["Body"].read().decode("utf-8")))
        return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)
