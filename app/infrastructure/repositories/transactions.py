from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.infrastructure.db.models import Transaction


class TransactionsRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, tx: Transaction) -> Transaction:
        self.session.add(tx)
        return tx

    def get_by_id(self, tx_id: int) -> Transaction | None:
        return self.session.get(Transaction, tx_id)

    def delete(self, tx_id: int) -> bool:
        tx = self.get_by_id(tx_id)
        if not tx:
            return False
        self.session.delete(tx)
        self.session.commit()
        return True

    def commit(self) -> None:
        self.session.commit()

    def list_recent(self, limit: int = 200) -> list[Transaction]:
        stmt = select(Transaction).order_by(desc(Transaction.occurred_at), desc(Transaction.id)).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def list_filtered(
        self,
        start: date | None = None,
        end: date | None = None,
        tx_type: str | None = None,
        account_id: int | None = None,
        category_id: int | None = None,
        limit: int = 500,
    ) -> list[Transaction]:
        """
        account_id:
          - для income/expense фильтрует по Transaction.account_id
          - для transfer фильтрует по from_account_id OR to_account_id
        """
        stmt = select(Transaction)

        if start is not None:
            stmt = stmt.where(Transaction.occurred_at >= start)
        if end is not None:
            stmt = stmt.where(Transaction.occurred_at <= end)
        if tx_type:
            stmt = stmt.where(Transaction.type == tx_type)

        if category_id is not None:
            stmt = stmt.where(Transaction.category_id == category_id)

        if account_id is not None:
            stmt = stmt.where(
                (Transaction.account_id == account_id)
                | (Transaction.from_account_id == account_id)
                | (Transaction.to_account_id == account_id)
            )

        stmt = stmt.order_by(desc(Transaction.occurred_at), desc(Transaction.id)).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
