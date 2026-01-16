from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.infrastructure.db.models import Category


class CategoriesRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, cat: Category) -> Category:
        self.session.add(cat)
        return cat

    def get_by_id(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.id.desc())
        return list(self.session.execute(stmt).scalars().all())

    def list_by_kind(self, kind: str) -> list[Category]:
        stmt = select(Category).where(Category.kind == kind).order_by(Category.id.desc())
        return list(self.session.execute(stmt).scalars().all())

    def commit(self) -> None:
        self.session.commit()
