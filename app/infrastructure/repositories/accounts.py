from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.infrastructure.db.models import Account


class AccountsRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, acc: Account) -> Account:
        self.session.add(acc)
        return acc

    def get_by_id(self, account_id: int) -> Account | None:
        return self.session.get(Account, account_id)

    def list_all(self) -> list[Account]:
        stmt = select(Account).order_by(Account.id.desc())
        return list(self.session.execute(stmt).scalars().all())

    def list_active(self) -> list[Account]:
        stmt = select(Account).where(Account.is_active.is_(True)).order_by(Account.id.desc())
        return list(self.session.execute(stmt).scalars().all())

    def deactivate(self, account_id: int) -> bool:
        acc = self.get_by_id(account_id)
        if not acc:
            return False
        acc.is_active = False
        self.session.commit()
        return True

    def activate(self, account_id: int) -> bool:
        acc = self.get_by_id(account_id)
        if not acc:
            return False
        acc.is_active = True
        self.session.commit()
        return True

    def commit(self) -> None:
        self.session.commit()
