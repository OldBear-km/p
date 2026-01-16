from enum import StrEnum


class AccountType(StrEnum):
    CASH = "cash"
    BANK = "bank"
    SAVINGS = "savings"


class CategoryKind(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    SAVINGS = "savings"  


class TransactionType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"
