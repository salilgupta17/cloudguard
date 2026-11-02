"""
Automated Tests for Bank Account Creation and Retrieval.
Requirement: Account retrieval tests.
"""

def test_create_bank_account_with_initial_deposit(banking_client):
    # Fetch an existing customer
    cust_resp = banking_client.get("/api/v1/customers")
    customer = cust_resp.json()[0]

    payload = {
        "customer_id": customer["id"],
        "account_type": "CHECKING",
        "initial_deposit_cents": 25000,
        "currency": "USD"
    }
    response = banking_client.post("/api/v1/accounts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["customer_id"] == customer["id"]
    assert data["account_type"] == "CHECKING"
    assert data["balance_cents"] == 25000
    assert data["status"] == "ACTIVE"
    assert data["account_number"].startswith("ACC-US-")


def test_account_retrieval_by_id(banking_client):
    # Fetch existing accounts
    list_resp = banking_client.get("/api/v1/accounts")
    assert list_resp.status_code == 200
    accounts = list_resp.json()
    assert len(accounts) > 0
    target_account = accounts[0]

    # Retrieve account by ID
    get_resp = banking_client.get(f"/api/v1/accounts/{target_account['id']}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["id"] == target_account["id"]
    assert retrieved["account_number"] == target_account["account_number"]
    assert retrieved["balance_cents"] == target_account["balance_cents"]


def test_account_retrieval_by_account_number(banking_client):
    list_resp = banking_client.get("/api/v1/accounts")
    target_account = list_resp.json()[0]

    get_resp = banking_client.get(f"/api/v1/accounts/by-number/{target_account['account_number']}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["id"] == target_account["id"]
    assert retrieved["account_number"] == target_account["account_number"]
