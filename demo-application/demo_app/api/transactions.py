"""
Transaction API Router - Demo Banking Application.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.account import Account
from ..models.transaction import Transaction
from ..schemas.transaction import TransactionCreate, TransactionResponse
from ..core.exceptions import AccountNotFoundError, InsufficientFundsError, AccountFrozenError, InvalidTransactionError

router = APIRouter(tags=["Transactions"])


@router.post("/api/v1/accounts/{account_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def record_transaction(account_id: str, payload: TransactionCreate, db: Session = Depends(get_db)):
    if payload.amount_cents <= 0:
        raise InvalidTransactionError("Transaction amount must be strictly positive.")

    account = db.query(Account).filter(Account.id == account_id).with_for_update().first()
    if not account:
        raise AccountNotFoundError(account_id)

    if account.status != "ACTIVE":
        raise AccountFrozenError(account.account_number)

    current_balance = account.balance_cents
    if payload.transaction_type == "WITHDRAWAL":
        if current_balance < payload.amount_cents:
            raise InsufficientFundsError(current_balance, payload.amount_cents)
        new_balance = current_balance - payload.amount_cents
    elif payload.transaction_type == "DEPOSIT":
        new_balance = current_balance + payload.amount_cents
    else:
        raise InvalidTransactionError(f"Unsupported transaction type: {payload.transaction_type}")

    reference_number = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    txn_record = Transaction(
        id=str(uuid.uuid4()),
        account_id=account.id,
        reference_number=reference_number,
        transaction_type=payload.transaction_type,
        amount_cents=payload.amount_cents,
        balance_after_cents=new_balance,
        description=payload.description or "Banking Transaction",
        status="POSTED"
    )

    account.balance_cents = new_balance
    db.add(txn_record)
    db.commit()
    db.refresh(txn_record)

    return txn_record


@router.get("/api/v1/accounts/{account_id}/transactions", response_model=List[TransactionResponse])
def list_account_transactions(account_id: str, limit: int = 100, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise AccountNotFoundError(account_id)

    return db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).order_by(Transaction.created_at.desc()).limit(limit).all()


@router.get("/api/v1/transactions", response_model=List[TransactionResponse])
def list_all_transactions(
    transaction_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    return query.order_by(Transaction.created_at.desc()).limit(limit).all()
