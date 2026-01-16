from __future__ import annotations

from datetime import date

from app.infrastructure.repositories.reports import ReportsRepo, AccountBalanceRow, PeriodSummary, CategoryTotalRow


def get_account_balances(repo: ReportsRepo) -> list[AccountBalanceRow]:
    return repo.account_balances()


def get_period_summary(repo: ReportsRepo, start: date, end: date) -> PeriodSummary:
    return repo.period_summary(start, end)


def get_top_expense_categories(repo: ReportsRepo, start: date, end: date, limit: int = 10) -> list[CategoryTotalRow]:
    return repo.top_expense_categories(start, end, limit=limit)
