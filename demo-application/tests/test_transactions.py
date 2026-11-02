"""
Automated Tests for Transaction Recording and Listing.
Requirement: Transaction listing tests and database transaction verification.
"""

def test_record_deposit_transaction(banking_client):
    # Fetch target account
    acc_resp = banking_client.get("/api/v1/accounts")
    account = acc_resp.json()[0]
    initial_balance = account["balance_cents"]

    payload = {
        "transaction_type": "DEPOSIT",
        "amount_cents": 15000,
        "description": "Wire Transfer Inflow"
    }
    response = banking_client.post(f"/api/v1/accounts/{account['id']}/transactions", json=payload)
    assert response.status_code == 201
    txn = response.json()
    assert txn["account_id"] == account["id"]
    assert txn["amount_cents"] == 15000
    assert txn["transaction_type"] == "DEPOSIT"
    assert txn["balance_after_cents"] == initial_balance + 15000
    assert txn["status"] == "POSTED"
    assert txn["reference_number"].startswith("TXN-")

    # Verify updated account balance
    updated_acc = banking_client.get(f"/api/v1/accounts/{account['id']}").json()
    assert updated_acc["balance_cents"] == initial_balance + 15000


def test_record_withdrawal_transaction(banking_client):
    acc_resp = banking_client.get("/api/v1/accounts")
    account = acc_resp.json()[0]
    initial_balance = account["balance_cents"]

    withdrawal_amount = 5000
    assert initial_balance >= withdrawal_amount

    payload = {
        "transaction_type": "WITHDRAWAL",
        "amount_cents": withdrawal_amount,
        "description": "ATM Cash Withdrawal"
    }
    response = banking_client.post(f"/api/v1/accounts/{account['id']}/transactions", json=payload)
    assert response.status_code == 201
    txn = response.json()
    assert txn["amount_cents"] == withdrawal_amount
    assert txn["transaction_type"] == "WITHDRAWAL"
    assert txn["balance_after_cents"] == initial_balance - withdrawal_amount

    # Verify updated account balance
    updated_acc = banking_client.get(f"/api/v1/accounts/{account['id']}").json()
    assert updated_acc["balance_cents"] == initial_balance - withdrawal_amount


def test_list_account_transactions(banking_client):
    acc_resp = banking_client.get("/api/v1/accounts")
    account = acc_resp.json()[0]

    # Retrieve transactions for this account
    txns_resp = banking_client.get(f"/api/v1/accounts/{account['id']}/transactions")
    assert txns_resp.status_code == 200
    txns = txns_resp.json()
    assert len(txns) >= 1
    assert all(t["account_id"] == account["id"] for t in txns)


def test_list_all_transactions(banking_client):
    txns_resp = banking_client.get("/api/v1/transactions")
    assert txns_resp.status_code == 200
    all_txns = txns_resp.json()
    assert len(all_txns) >= 3
