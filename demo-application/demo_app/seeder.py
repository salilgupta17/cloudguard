"""
Realistic Synthetic Banking Records Seeder.
"""
import uuid
from datetime import datetime, timezone, timedelta
from faker import Faker
from sqlalchemy.orm import Session
from .models.customer import Customer
from .models.account import Account
from .models.transaction import Transaction

fake = Faker()
Faker.seed(2026)


def seed_banking_data(db: Session, customers_count: int = 8):
    if db.query(Customer).first() is not None:
        return

    customers = []
    accounts = []
    transactions = []
    account_types = ["CHECKING", "SAVINGS", "BUSINESS"]

    for i in range(customers_count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        cust_id = str(uuid.uuid4())
        cust = Customer(
            id=cust_id,
            customer_number=f"CUST-{10000 + i}",
            first_name=first_name,
            last_name=last_name,
            email=f"{first_name.lower()}.{last_name.lower()}_{i}@cloudbank.internal",
            phone=f"+1-555-{1000 + i:04d}",
            kyc_status="VERIFIED"
        )
        db.add(cust)
        customers.append(cust)

    db.commit()

    acc_idx = 1
    for cust in customers:
        num_accounts = 2 if (acc_idx % 2 == 0) else 1
        for a in range(num_accounts):
            acc_id = str(uuid.uuid4())
            acc_num = f"ACC-US-{900000 + acc_idx:06d}"
            acc_type = account_types[(acc_idx - 1) % len(account_types)]
            initial_balance_cents = 50000 + (acc_idx * 15000)

            account = Account(
                id=acc_id,
                customer_id=cust.id,
                account_number=acc_num,
                account_type=acc_type,
                balance_cents=initial_balance_cents,
                currency="USD",
                status="ACTIVE"
            )
            db.add(account)
            accounts.append(account)

            txn_id = str(uuid.uuid4())
            txn_ref = f"TXN-2026-OPEN-{acc_idx:04d}"
            opening_txn = Transaction(
                id=txn_id,
                account_id=acc_id,
                reference_number=txn_ref,
                transaction_type="DEPOSIT",
                amount_cents=initial_balance_cents,
                balance_after_cents=initial_balance_cents,
                description="Account Opening Initial Deposit",
                status="POSTED",
                created_at=datetime.now(timezone.utc) - timedelta(days=30)
            )
            db.add(opening_txn)
            transactions.append(opening_txn)

            subsequent_amount = 5000
            current_balance = initial_balance_cents + subsequent_amount
            account.balance_cents = current_balance

            subsequent_txn = Transaction(
                id=str(uuid.uuid4()),
                account_id=acc_id,
                reference_number=f"TXN-2026-DEP-{acc_idx:04d}",
                transaction_type="DEPOSIT",
                amount_cents=subsequent_amount,
                balance_after_cents=current_balance,
                description="Payroll Direct Deposit",
                status="POSTED",
                created_at=datetime.now(timezone.utc) - timedelta(days=15)
            )
            db.add(subsequent_txn)
            transactions.append(subsequent_txn)

            acc_idx += 1

    db.commit()
