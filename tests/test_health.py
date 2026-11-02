"""
Unit and Integration Tests for Health and Readiness Endpoints.
Requirement: Health and readiness endpoints.
"""
def test_cloudguard_liveness_endpoint(cg_client):
    response = cg_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cloudguard-api"


def test_cloudguard_readiness_endpoint(cg_client):
    response = cg_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "healthy"
    assert data["checks"]["backup_storage"] == "healthy"


def test_demo_app_liveness_endpoint(demo_client):
    response = demo_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "banking" in data["service"] or "demo" in data["service"]


def test_demo_app_readiness_endpoint(demo_client):
    response = demo_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
