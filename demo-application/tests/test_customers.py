"""
Automated Tests for Customer Management and Retrieval.
Requirement: Customer retrieval tests.
"""

def test_create_customer(banking_client):
    payload = {
        "first_name": "Alexander",
        "last_name": "Hamilton",
        "email": "a.hamilton@treasury.gov",
        "phone": "+1-202-555-0144",
        "kyc_status": "VERIFIED"
    }
    response = banking_client.post("/api/v1/customers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["first_name"] == "Alexander"
    assert data["last_name"] == "Hamilton"
    assert data["full_name"] == "Alexander Hamilton"
    assert data["email"] == "a.hamilton@treasury.gov"
    assert data["customer_number"].startswith("CUST-")


def test_customer_retrieval_by_id(banking_client):
    # 1. Fetch all seeded customers to obtain an existing customer ID
    list_resp = banking_client.get("/api/v1/customers")
    assert list_resp.status_code == 200
    customers = list_resp.json()
    assert len(customers) > 0
    target_customer = customers[0]

    # 2. Retrieve customer by ID
    get_resp = banking_client.get(f"/api/v1/customers/{target_customer['id']}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["id"] == target_customer["id"]
    assert retrieved["email"] == target_customer["email"]
    assert retrieved["customer_number"] == target_customer["customer_number"]


def test_customer_accounts_retrieval(banking_client):
    list_resp = banking_client.get("/api/v1/customers")
    target_customer = list_resp.json()[0]

    accs_resp = banking_client.get(f"/api/v1/customers/{target_customer['id']}/accounts")
    assert accs_resp.status_code == 200
    accounts = accs_resp.json()
    assert len(accounts) >= 1
    assert accounts[0]["customer_id"] == target_customer["id"]
