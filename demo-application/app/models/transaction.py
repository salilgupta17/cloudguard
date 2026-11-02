"""
Transaction Model - Banking Domain.
Immutable financial ledger record.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .account import Account


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="chk_positive_amount"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    reference_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="Standard Transaction", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="POSTED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
