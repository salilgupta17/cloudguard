"""
Customer API Router - Demo Banking Application.
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.customer import Customer
from ..models.account import Account
from ..schemas.customer import CustomerCreate, CustomerResponse
from ..schemas.account import AccountResponse
from ..core.exceptions import CustomerNotFoundError, DuplicateRecordError

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    existing_email = db.query(Customer).filter(Customer.email == payload.email).first()
    if existing_email:
        raise DuplicateRecordError(f"Customer with email '{payload.email}' already exists.")

    cust_id = str(uuid.uuid4())
    customer_number = f"CUST-{uuid.uuid4().hex[:8].upper()}"

    customer = Customer(
        id=cust_id,
        customer_number=customer_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        kyc_status=payload.kyc_status or "VERIFIED"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=List[CustomerResponse])
def list_customers(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Customer).order_by(Customer.created_at.desc()).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise CustomerNotFoundError(customer_id)
    return customer


@router.get("/{customer_id}/accounts", response_model=List[AccountResponse])
def list_customer_accounts(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise CustomerNotFoundError(customer_id)
    return db.query(Account).filter(Account.customer_id == customer_id).all()
