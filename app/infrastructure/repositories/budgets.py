from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.infrastructure.db.models import Budget


class BudgetsRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, b: Budget) -> Budget:
        self.session.add(b)
        return b

    def get_by_id(self, budget_id: int) -> Budget | None:
        return self.session.get(Budget, budget_id)

    def get_by_month_and_category(self, month_start: date, category_id: int) -> Budget | None:
        stmt = select(Budget).where(Budget.month_start == month_start, Budget.category_id == category_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_month(self, month_start: date) -> list[Budget]:
        stmt = select(Budget).where(Budget.month_start == month_start).order_by(Budget.id.desc())
        return list(self.session.execute(stmt).scalars().all())

    def delete(self, budget_id: int) -> bool:
        b = self.get_by_id(budget_id)
        if not b:
            return False
        self.session.delete(b)
        self.session.commit()
        return True

    def commit(self) -> None:
        self.session.commit()
