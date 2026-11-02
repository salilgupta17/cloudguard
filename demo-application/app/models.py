"""
SQLAlchemy Domain Models for Demo Application.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
try:
    from app.database import Base
except ImportError:
    from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    tier = Column(String(32), default="STANDARD", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True)
    sku = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    price_cents = Column(Integer, nullable=False)
    in_stock = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    order_number = Column(String(64), unique=True, nullable=False, index=True)
    total_amount_cents = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    customer = relationship("Customer", back_populates="orders")
