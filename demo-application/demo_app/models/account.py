"""
Account Model - Banking Domain.
"""
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .customer import Customer
    from .transaction import Transaction


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("balance_cents >= 0", name="chk_positive_balance"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    account_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), default="CHECKING", nullable=False)
    balance_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
