"""
CloudWatch Telemetry & Metrics Publisher.
Streams structured metrics and log events to AWS CloudWatch.
Adheres to Rule 10: Gracefully operates in local mode when AWS credentials are not present.
"""
import os
from typing import Dict, Any, Optional
from app.core.logging import logger

CLOUDWATCH_NAMESPACE = "CloudGuard/DisasterRecovery"


class CloudWatchMetricsPublisher:
    """Publishes DR drill telemetry and SLA benchmarks to CloudWatch."""

    def __init__(self, region: Optional[str] = None):
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self._cloudwatch_client = None

    def _get_client(self):
        if self._cloudwatch_client is None:
            aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
            aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
            if not aws_key or not aws_secret or "mock" in aws_key.lower() or "dummy" in aws_key.lower():
                return None
            try:
                import boto3
                self._cloudwatch_client = boto3.client("cloudwatch", region_name=self.region)
            except Exception as e:
                logger.debug(f"CloudWatch client initialization skipped (local mode active): {e}")
                return None
        return self._cloudwatch_client

    def publish_drill_metrics(
        self,
        application_name: str,
        duration_seconds: float,
        backup_age_minutes: float,
        passed: bool,
        check_counts: Optional[Dict[str, int]] = None
    ) -> bool:
        """
        Emits key Disaster Recovery metrics to CloudWatch:
        - RecoveryDrillDuration
        - BackupFreshnessMinutes
        - DrillSuccess (1/0)
        - ValidationChecksPassed / Failed
        """
        client = self._get_client()
        if not client:
            logger.debug(f"[Local Mode] Skipping CloudWatch metric emission for {application_name}")
            return False

        dimensions = [
            {"Name": "ApplicationName", "Value": application_name},
            {"Name": "Environment", "Value": os.environ.get("APP_ENV", "production")}
        ]

        metric_data = [
            {
                "MetricName": "RecoveryDrillDuration",
                "Dimensions": dimensions,
                "Value": float(duration_seconds),
                "Unit": "Seconds"
            },
            {
                "MetricName": "BackupFreshnessMinutes",
                "Dimensions": dimensions,
                "Value": float(backup_age_minutes),
                "Unit": "None"
            },
            {
                "MetricName": "DrillSuccess",
                "Dimensions": dimensions,
                "Value": 1.0 if passed else 0.0,
                "Unit": "Count"
            }
        ]

        if check_counts:
            metric_data.append({
                "MetricName": "ValidationChecksPassed",
                "Dimensions": dimensions,
                "Value": float(check_counts.get("passed", 0)),
                "Unit": "Count"
            })
            metric_data.append({
                "MetricName": "ValidationChecksFailed",
                "Dimensions": dimensions,
                "Value": float(check_counts.get("failed", 0)),
                "Unit": "Count"
            })

        try:
            client.put_metric_data(
                Namespace=CLOUDWATCH_NAMESPACE,
                MetricData=metric_data
            )
            logger.info(f"Published DR telemetry metrics to CloudWatch namespace '{CLOUDWATCH_NAMESPACE}'")
            return True
        except Exception as e:
            logger.warning(f"Failed to publish metrics to CloudWatch: {e}")
            return False
