"""
Account API Router - Demo Banking Application.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.customer import Customer
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.account import AccountCreate, AccountResponse
from ..core.exceptions import CustomerNotFoundError, AccountNotFoundError

router = APIRouter(prefix="/api/v1/accounts", tags=["Bank Accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise CustomerNotFoundError(payload.customer_id)

    acc_id = str(uuid.uuid4())
    account_number = f"ACC-US-{uuid.uuid4().hex[:10].upper()}"
    initial_deposit = payload.initial_deposit_cents or 0

    with db.begin_nested():
        account = Account(
            id=acc_id,
            customer_id=payload.customer_id,
            account_number=account_number,
            account_type=payload.account_type,
            balance_cents=initial_deposit,
            currency=payload.currency or "USD",
            status="ACTIVE"
        )
        db.add(account)

        if initial_deposit > 0:
            txn = Transaction(
                id=str(uuid.uuid4()),
                account_id=acc_id,
                reference_number=f"TXN-OPEN-{uuid.uuid4().hex[:8].upper()}",
                transaction_type="DEPOSIT",
                amount_cents=initial_deposit,
                balance_after_cents=initial_deposit,
                description="Opening Deposit",
                status="POSTED"
            )
            db.add(txn)

    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=List[AccountResponse])
def list_accounts(
    account_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Account)
    if account_type:
        query = query.filter(Account.account_type == account_type)
    if status_filter:
        query = query.filter(Account.status == status_filter)
    return query.order_by(Account.created_at.desc()).limit(limit).all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account_by_id(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise AccountNotFoundError(account_id)
    return account


@router.get("/by-number/{account_number}", response_model=AccountResponse)
def get_account_by_number(account_number: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_number == account_number).first()
    if not account:
        raise AccountNotFoundError(account_number)
    return account
