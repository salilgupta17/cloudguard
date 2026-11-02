"""
Report Storage System.
Supports storing disaster recovery reports locally on disk, with an extensible
interface prepared for AWS S3 bucket persistence.
"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional


class ReportStorageInterface(ABC):
    """Abstract interface for Disaster Recovery Report persistence."""

    @abstractmethod
    def save_report(self, report_id: str, format_type: str, content: bytes | str) -> str:
        """Saves report content in specified format ('json', 'html', 'pdf'). Returns URI or path."""
        pass

    @abstractmethod
    def get_report(self, report_id: str, format_type: str) -> bytes | str:
        """Retrieves stored report content."""
        pass

    @abstractmethod
    def list_reports(self) -> List[Dict[str, Any]]:
        """Lists available report artifacts."""
        pass

    @abstractmethod
    def report_exists(self, report_id: str, format_type: str) -> bool:
        """Checks if a report artifact exists."""
        pass


class LocalReportStorage(ReportStorageInterface):
    """Local filesystem report storage engine."""

    def __init__(self, base_dir: Path | str = "./reports"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, report_id: str, format_type: str) -> Path:
        ext = format_type.lower().lstrip(".")
        return self.base_dir / f"{report_id}.{ext}"

    def save_report(self, report_id: str, format_type: str, content: bytes | str) -> str:
        target_path = self._get_path(report_id, format_type)
        if isinstance(content, bytes):
            target_path.write_bytes(content)
        else:
            target_path.write_text(content, encoding="utf-8")
        return str(target_path.resolve())

    def get_report(self, report_id: str, format_type: str) -> bytes | str:
        target_path = self._get_path(report_id, format_type)
        if not target_path.exists():
            raise FileNotFoundError(f"Report artifact '{report_id}.{format_type}' not found at {target_path}")
        if format_type.lower() == "pdf":
            return target_path.read_bytes()
        return target_path.read_text(encoding="utf-8")

    def report_exists(self, report_id: str, format_type: str) -> bool:
        return self._get_path(report_id, format_type).exists()

    def list_reports(self) -> List[Dict[str, Any]]:
        reports_map: Dict[str, Dict[str, Any]] = {}
        for file in self.base_dir.glob("*.*"):
            if file.suffix.lower() in [".json", ".html", ".pdf"]:
                rep_id = file.stem
                if rep_id not in reports_map:
                    reports_map[rep_id] = {
                        "report_id": rep_id,
                        "formats": [],
                        "created_at": file.stat().st_ctime
                    }
                fmt = file.suffix.lower().lstrip(".")
                reports_map[rep_id]["formats"].append(fmt)

        return sorted(list(reports_map.values()), key=lambda x: x["created_at"], reverse=True)


class S3ReportStorage(ReportStorageInterface):
    """
    AWS S3 Disaster Recovery Report Storage Adapter.
    Prepared for cloud production archiving with authentic AWS credential checks.
    """

    def __init__(self, bucket_name: str = "cloudguard-dr-reports", prefix: str = "reports/"):
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/") + "/"
        self._s3_client = None

    def _get_client(self):
        if self._s3_client is None:
            import boto3
            # Strict AWS credential validation
            aws_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
            if not aws_key or not aws_secret:
                raise ValueError("AWS S3 report storage requires valid AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
            self._s3_client = boto3.client("s3")
        return self._s3_client

    def save_report(self, report_id: str, format_type: str, content: bytes | str) -> str:
        client = self._get_client()
        key = f"{self.prefix}{report_id}.{format_type.lower()}"
        body = content.encode("utf-8") if isinstance(content, str) else content
        content_type = "application/pdf" if format_type == "pdf" else ("text/html" if format_type == "html" else "application/json")
        client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type
        )
        return f"s3://{self.bucket_name}/{key}"

    def get_report(self, report_id: str, format_type: str) -> bytes | str:
        client = self._get_client()
        key = f"{self.prefix}{report_id}.{format_type.lower()}"
        resp = client.get_object(Bucket=self.bucket_name, Key=key)
        data = resp["Body"].read()
        if format_type.lower() == "pdf":
            return data
        return data.decode("utf-8")

    def report_exists(self, report_id: str, format_type: str) -> bool:
        try:
            client = self._get_client()
            key = f"{self.prefix}{report_id}.{format_type.lower()}"
            client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    def list_reports(self) -> List[Dict[str, Any]]:
        client = self._get_client()
        resp = client.list_objects_v2(Bucket=self.bucket_name, Prefix=self.prefix)
        items = []
        for obj in resp.get("Contents", []):
            items.append({
                "key": obj["Key"],
                "size_bytes": obj["Size"],
                "last_modified": obj["LastModified"].isoformat()
            })
        return items
