"""
Health and Readiness Probes for CloudGuard API.
Follows cloud-native observability standards.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from app.database import get_db
    from app.config import settings
    from app.core.logging import logger
except ImportError:
    from ..database import get_db
    from ..config import settings
    from ..core.logging import logger

router = APIRouter(tags=["Health & Readiness"])


@router.get("/health", summary="Liveness Probe")
def liveness_check():
    """
    Liveness probe: verifies process is alive and responding to traffic.
    Used by ECS/Kubernetes/Docker to decide if the container must be restarted.
    """
    return {
        "status": "healthy",
        "service": "cloudguard-api",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }


@router.get("/ready", summary="Readiness Probe")
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe: verifies all backing services (database, backup volume) are functional.
    Used by load balancers before routing production traffic.
    """
    checks = {
        "database": "unknown",
        "backup_storage": "unknown"
    }

    # 1. Check Database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as db_err:
        logger.error(f"Readiness check failed on database: {db_err}")
        checks["database"] = f"unhealthy: {str(db_err)}"

    # 2. Check Backup Storage path
    try:
        backup_path = Path(settings.BACKUP_DIR)
        if backup_path.exists() and backup_path.is_dir():
            checks["backup_storage"] = "healthy"
        else:
            checks["backup_storage"] = "unhealthy: directory not found"
    except Exception as fs_err:
        logger.error(f"Readiness check failed on backup storage: {fs_err}")
        checks["backup_storage"] = f"unhealthy: {str(fs_err)}"

    is_ready = all(v == "healthy" for v in checks.values())

    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "service": "cloudguard-api",
                "checks": checks
            }
        )

    return {
        "status": "ready",
        "service": "cloudguard-api",
        "checks": checks
    }
