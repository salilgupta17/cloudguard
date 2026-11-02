"""
Automated Tests for Read-Only Validation Endpoints.
Requirement: Read-only API endpoints for CloudGuard validation engine.
"""

def test_validation_ledger_summary(banking_client):
    response = banking_client.get("/api/v1/validation/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_customers"] >= 3
    assert data["total_accounts"] >= 3
    assert data["total_transactions"] >= 3
    assert data["total_balance_cents"] > 0
    assert data["ledger_integrity_passed"] is True
    assert len(data["checksum_sha256"]) == 64


def test_validation_customers_export(banking_client):
    response = banking_client.get("/api/v1/validation/customers/export")
    assert response.status_code == 200
    customers = response.json()
    assert len(customers) >= 3
    for c in customers:
        assert "customer_number" in c
        assert "accounts_count" in c
        assert c["accounts_count"] >= 1


def test_validation_accounts_export(banking_client):
    response = banking_client.get("/api/v1/validation/accounts/export")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) >= 3
    for a in accounts:
        assert "account_number" in a
        assert "balance_cents" in a
        assert "transactions_count" in a
        assert a["transactions_count"] >= 1


def test_validation_ledger_mathematical_integrity(banking_client):
    response = banking_client.get("/api/v1/validation/ledger/integrity")
    assert response.status_code == 200
    data = response.json()
    assert data["integrity_passed"] is True
    assert data["discrepancies_count"] == 0
    assert len(data["discrepancies"]) == 0
