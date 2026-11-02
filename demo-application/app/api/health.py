"""
Health and Database Readiness Endpoints for Banking Application.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter(tags=["Monitoring & Probes"])


@router.get("/health", summary="Application Health Liveness Probe")
def health_probe():
    """Returns 200 if the FastAPI application process is alive."""
    return {
        "status": "healthy",
        "service": "demo-banking-application",
        "version": "1.0.0"
    }


@router.get("/ready", summary="Database Readiness Probe")
def readiness_probe(db: Session = Depends(get_db)):
    """Validates PostgreSQL database connection and query readiness."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": "demo-banking-application",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness check failed: {str(e)}"
        )
