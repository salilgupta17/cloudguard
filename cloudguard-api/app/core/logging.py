"""
Structured Logging Configuration for CloudGuard API.
Outputs structured JSON / standard formatted logs for observability and audit trails.
"""
import logging
import sys
import json
from datetime import datetime, timezone


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "cloudguard-api",
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields"):
            log_obj["metadata"] = getattr(record, "extra_fields")
        return json.dumps(log_obj)


def get_logger(name: str = "cloudguard-api", log_format: str = "text") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if log_format.lower() == "json":
            handler.setFormatter(StructuredJsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [cloudguard-api:%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
        logger.addHandler(handler)

    return logger

logger = get_logger()
