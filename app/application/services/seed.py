from datetime import date

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.accounts import AccountsRepo
from app.infrastructure.repositories.categories import CategoriesRepo
from app.infrastructure.repositories.transactions import TransactionsRepo

from app.domain.enums import AccountType, CategoryKind
from app.application.services.accounts import create_account
from app.application.services.categories import create_category
from app.application.services.transactions import add_expense, add_income


def seed_demo():
    with SessionLocal() as session:
        acc_repo = AccountsRepo(session)
        cat_repo = CategoriesRepo(session)
        tx_repo = TransactionsRepo(session)

        cash = create_account(acc_repo, "Наличные", AccountType.CASH.value)
        card = create_account(acc_repo, "Карта", AccountType.BANK.value)

        salary = create_category(cat_repo, CategoryKind.INCOME.value, "Salary", "salary")
        food = create_category(cat_repo, CategoryKind.EXPENSE.value, "Food", "food")

        today = date.today()

        add_income(tx_repo, today, card.id, salary.id, 250_000, "ЗП")
        add_expense(tx_repo, today, card.id, food.id, 1_250, "Кофе и булка")

        session.commit()
        return {
            "accounts": [cash, card],
            "categories": [salary, food],
        }
