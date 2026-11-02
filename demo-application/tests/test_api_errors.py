"""
Automated Tests for API Error Handling and Business Constraints.
Requirement: API errors tests.
"""

def test_error_customer_not_found(banking_client):
    response = banking_client.get("/api/v1/customers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_error_account_not_found(banking_client):
    response = banking_client.get("/api/v1/accounts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_error_duplicate_customer_email(banking_client):
    # Retrieve existing customer
    cust_resp = banking_client.get("/api/v1/customers")
    existing_email = cust_resp.json()[0]["email"]

    # Attempt to create new customer with identical email
    payload = {
        "first_name": "Duplicate",
        "last_name": "User",
        "email": existing_email,
        "phone": "+1-555-0999"
    }
    response = banking_client.post("/api/v1/customers", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_error_insufficient_funds_withdrawal(banking_client):
    acc_resp = banking_client.get("/api/v1/accounts")
    account = acc_resp.json()[0]
    current_balance = account["balance_cents"]

    # Attempt to withdraw more than available balance
    excessive_amount = current_balance + 1000000 # $10,000 more
    payload = {
        "transaction_type": "WITHDRAWAL",
        "amount_cents": excessive_amount,
        "description": "Overdraft Attempt"
    }
    response = banking_client.post(f"/api/v1/accounts/{account['id']}/transactions", json=payload)
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


def test_error_invalid_transaction_amount(banking_client):
    acc_resp = banking_client.get("/api/v1/accounts")
    account = acc_resp.json()[0]

    # Attempt deposit with negative or zero amount
    payload = {
        "transaction_type": "DEPOSIT",
        "amount_cents": 0,
        "description": "Zero Amount"
    }
    response = banking_client.post(f"/api/v1/accounts/{account['id']}/transactions", json=payload)
    # Pydantic validates amount_cents > 0, returns 422
    assert response.status_code == 422


def test_error_create_account_nonexistent_customer(banking_client):
    payload = {
        "customer_id": "00000000-0000-0000-0000-000000000000",
        "account_type": "SAVINGS",
        "initial_deposit_cents": 5000
    }
    response = banking_client.post("/api/v1/accounts", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
