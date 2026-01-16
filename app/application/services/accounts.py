from app.infrastructure.db.models import Account
from app.infrastructure.repositories.accounts import AccountsRepo
from app.domain.enums import AccountType


def create_account(repo: AccountsRepo, name: str, account_type: str = AccountType.BANK.value) -> Account:
    existing = repo.get_by_name(name)
    if existing:
        return existing

    acc = Account(name=name, type=account_type, is_active=True)
    repo.add(acc)
    repo.session.commit()
    return acc


def deactivate(self, account_id: int) -> bool:
    acc = self.get_by_id(account_id)
    if not acc:
        return False
    acc.is_active = False
    self.session.commit()
    return True
