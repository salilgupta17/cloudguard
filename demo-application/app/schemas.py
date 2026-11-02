"""
Pydantic Schemas for Demo Application.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class CustomerCreate(BaseModel):
    full_name: str
    email: str
    tier: Optional[str] = "STANDARD"


class CustomerResponse(BaseModel):
    id: str
    full_name: str
    email: str
    tier: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    sku: str
    name: str
    price_cents: int
    in_stock: Optional[bool] = True


class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    price_cents: int
    in_stock: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    customer_id: str
    total_amount_cents: int


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    order_number: str
    total_amount_cents: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
