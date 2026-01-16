from __future__ import annotations

from datetime import date

from app.infrastructure.db.models import Budget
from app.infrastructure.repositories.budgets import BudgetsRepo


def upsert_budget(repo: BudgetsRepo, month_start: date, category_id: int, limit_cents: int) -> Budget:
    """
    Создаёт или обновляет бюджет на месяц по категории.
    Уникальность: (month_start, category_id)
    """
    existing = repo.get_by_month_and_category(month_start, category_id)
    if existing is not None:
        existing.limit_cents = limit_cents
        repo.commit()
        return existing

    b = Budget(month_start=month_start, category_id=category_id, limit_cents=limit_cents)
    repo.add(b)
    repo.commit()
    return b
