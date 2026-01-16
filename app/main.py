from datetime import date

from app.application.services.seed import seed_demo
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.transactions import TransactionsRepo
from app.infrastructure.repositories.reports import ReportsRepo


def main():
    print("Seeding demo data...")
    seed_demo()

    with SessionLocal() as session:
        tx_repo = TransactionsRepo(session)
        rep_repo = ReportsRepo(session)

        items = tx_repo.list_recent(10)

        print("\nRecent transactions:")
        for t in items:
            print(f"- {t.occurred_at} | {t.type} | {t.amount_cents} | note={t.note}")

        print("\nAccount balances:")
        for row in rep_repo.account_balances():
            print(f"- {row.account_name}: {row.balance_cents} cents")

        start = date(date.today().year, date.today().month, 1)
        end = date.today()

        summary = rep_repo.period_summary(start, end)
        print("\nPeriod summary (from month start):")
        print(f"  income={summary.income_cents} expense={summary.expense_cents} net={summary.net_cents}")

        print("\nTop expense categories:")
        for row in rep_repo.top_expense_categories(start, end, limit=10):
            print(f"- {row.category_name}: {row.total_cents} cents")


if __name__ == "__main__":
    main()
