from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.infrastructure.db.models import Transaction, Account, Category
from app.domain.enums import TransactionType


@dataclass(frozen=True)
class AccountBalanceRow:
    account_id: int
    account_name: str
    balance_cents: int


@dataclass(frozen=True)
class PeriodSummary:
    income_cents: int
    expense_cents: int
    net_cents: int


@dataclass(frozen=True)
class CategoryTotalRow:
    category_id: int
    category_name: str
    total_cents: int


class ReportsRepo:
    def __init__(self, session: Session):
        self.session = session

    def account_balances(self) -> list[AccountBalanceRow]:
        """
        Баланс по счетам:
        - income: +amount на account_id
        - expense: -amount на account_id
        - transfer: -amount с from_account_id, +amount на to_account_id
        """
        tx = Transaction

        # Вклад для "обычных" операций (income/expense) по account_id
        base_amount = case(
            (tx.type == TransactionType.INCOME.value, tx.amount_cents),
            (tx.type == TransactionType.EXPENSE.value, -tx.amount_cents),
            else_=0,
        )

        base_q = (
            select(
                tx.account_id.label("acc_id"),
                func.coalesce(func.sum(base_amount), 0).label("sum_cents"),
            )
            .where(tx.account_id.is_not(None))
            .group_by(tx.account_id)
            .subquery()
        )

        # Переводы: исходящий (минус)
        out_q = (
            select(
                tx.from_account_id.label("acc_id"),
                func.coalesce(func.sum(-tx.amount_cents), 0).label("sum_cents"),
            )
            .where(tx.type == TransactionType.TRANSFER.value, tx.from_account_id.is_not(None))
            .group_by(tx.from_account_id)
            .subquery()
        )

        # Переводы: входящий (плюс)
        in_q = (
            select(
                tx.to_account_id.label("acc_id"),
                func.coalesce(func.sum(tx.amount_cents), 0).label("sum_cents"),
            )
            .where(tx.type == TransactionType.TRANSFER.value, tx.to_account_id.is_not(None))
            .group_by(tx.to_account_id)
            .subquery()
        )

        # Склеиваем суммы по acc_id через join к accounts
        stmt = (
            select(
                Account.id,
                Account.name,
                (
                    func.coalesce(base_q.c.sum_cents, 0)
                    + func.coalesce(out_q.c.sum_cents, 0)
                    + func.coalesce(in_q.c.sum_cents, 0)
                ).label("balance_cents"),
            )
            .select_from(Account)
            .outerjoin(base_q, base_q.c.acc_id == Account.id)
            .outerjoin(out_q, out_q.c.acc_id == Account.id)
            .outerjoin(in_q, in_q.c.acc_id == Account.id)
            .where(Account.is_active == True)
            .order_by(Account.name)
        )

        rows = self.session.execute(stmt).all()
        return [
            AccountBalanceRow(account_id=r[0], account_name=r[1], balance_cents=int(r[2] or 0))
            for r in rows
        ]

    def period_summary(self, start: date, end: date) -> PeriodSummary:
        tx = Transaction

        income_sum = func.coalesce(
            func.sum(case((tx.type == TransactionType.INCOME.value, tx.amount_cents), else_=0)),
            0,
        )
        expense_sum = func.coalesce(
            func.sum(case((tx.type == TransactionType.EXPENSE.value, tx.amount_cents), else_=0)),
            0,
        )

        stmt = select(income_sum.label("income"), expense_sum.label("expense")).where(
            tx.occurred_at >= start,
            tx.occurred_at <= end,
        )

        income, expense = self.session.execute(stmt).one()
        income = int(income or 0)
        expense = int(expense or 0)
        return PeriodSummary(income_cents=income, expense_cents=expense, net_cents=income - expense)

    def top_expense_categories(self, start: date, end: date, limit: int = 10) -> list[CategoryTotalRow]:
        tx = Transaction
        stmt = (
            select(
                Category.id,
                Category.name,
                func.sum(tx.amount_cents).label("total_cents"),
            )
            .select_from(tx)
            .join(Category, Category.id == tx.category_id)
            .where(
                tx.type == TransactionType.EXPENSE.value,
                tx.occurred_at >= start,
                tx.occurred_at <= end,
                tx.category_id.is_not(None),
            )
            .group_by(Category.id, Category.name)
            .order_by(func.sum(tx.amount_cents).desc())
            .limit(limit)
        )

        rows = self.session.execute(stmt).all()
        return [
            CategoryTotalRow(category_id=r[0], category_name=r[1], total_cents=int(r[2] or 0))
            for r in rows
        ]
