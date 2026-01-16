from datetime import date

from app.infrastructure.db.models import Transaction
from app.infrastructure.repositories.transactions import TransactionsRepo
from app.domain.enums import TransactionType


def add_expense(
    repo: TransactionsRepo,
    occurred_at: date,
    account_id: int,
    category_id: int,
    amount_cents: int,
    note: str | None = None,
) -> Transaction:
    tx = Transaction(
        occurred_at=occurred_at,
        type=TransactionType.EXPENSE.value,
        account_id=account_id,
        category_id=category_id,
        amount_cents=amount_cents,
        note=note,
    )
    repo.add(tx)
    repo.session.commit()
    return tx


def add_income(
    repo: TransactionsRepo,
    occurred_at: date,
    account_id: int,
    category_id: int,
    amount_cents: int,
    note: str | None = None,
) -> Transaction:
    tx = Transaction(
        occurred_at=occurred_at,
        type=TransactionType.INCOME.value,
        account_id=account_id,
        category_id=category_id,
        amount_cents=amount_cents,
        note=note,
    )
    repo.add(tx)
    repo.session.commit()
    return tx


def add_transfer(
    repo: TransactionsRepo,
    occurred_at: date,
    from_account_id: int,
    to_account_id: int,
    amount_cents: int,
    note: str | None = None,
    category_id: int | None = None,  # ✅ для накоплений/маркировки
) -> Transaction:
    tx = Transaction(
        occurred_at=occurred_at,
        type=TransactionType.TRANSFER.value,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount_cents=amount_cents,
        note=note,
        category_id=category_id,
    )
    repo.add(tx)
    repo.session.commit()
    return tx
