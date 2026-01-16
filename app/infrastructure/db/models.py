from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base
from app.domain.enums import AccountType, CategoryKind, TransactionType


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default=AccountType.BANK.value)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        foreign_keys="Transaction.account_id",
    )

    outgoing_transfers: Mapped[list["Transaction"]] = relationship(
        back_populates="from_account",
        foreign_keys="Transaction.from_account_id",
    )

    incoming_transfers: Mapped[list["Transaction"]] = relationship(
        back_populates="to_account",
        foreign_keys="Transaction.to_account_id",
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # kind: expense / income
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default=CategoryKind.EXPENSE.value)

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    parent: Mapped["Category | None"] = relationship(remote_side=[id])
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # occurred_at — дата операции (без времени)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)

    # type: income / expense / transfer
    type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Для income/expense:
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    # Для transfer:
    from_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    to_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    # Храним деньги в "копейках/центах" (int), чтобы не ловить float-ошибки
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    account: Mapped["Account | None"] = relationship(
        back_populates="transactions",
        foreign_keys=[account_id],
    )
    category: Mapped["Category | None"] = relationship(
        back_populates="transactions",
        foreign_keys=[category_id],
    )

    from_account: Mapped["Account | None"] = relationship(
        back_populates="outgoing_transfers",
        foreign_keys=[from_account_id],
    )
    to_account: Mapped["Account | None"] = relationship(
        back_populates="incoming_transfers",
        foreign_keys=[to_account_id],
    )

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="amount_positive"),
    )


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("month_start", "category_id", name="uq_budget_month_category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Храним первый день месяца (например 2026-01-01)
    month_start: Mapped[date] = mapped_column(index=True)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    category: Mapped["Category"] = relationship()

    limit_cents: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
