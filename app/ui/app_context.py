from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.reports import ReportsRepo


class AppSignals(QObject):
    """
    Глобальные сигналы приложения.
    ui_data_changed — когда изменились данные (операции/категории/счета и т.п.)
    """
    ui_data_changed = Signal()


@dataclass
class AppContext:
    def __post_init__(self):
        self.signals = AppSignals()

    def open_session(self):
        return SessionLocal()

    def reports_repo(self, session):
        return ReportsRepo(session)
