"""
Automated Tests for Database Connectivity and Health Probes.
Requirement: Database connectivity tests.
"""
from sqlalchemy import text


def test_database_connectivity(banking_db):
    """Direct database connectivity test."""
    result = banking_db.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_banking_app_health_liveness(banking_client):
    """Application health endpoint test."""
    response = banking_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "demo-banking-application"


def test_banking_app_database_readiness(banking_client):
    """Database readiness endpoint test."""
    response = banking_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
