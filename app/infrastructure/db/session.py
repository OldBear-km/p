import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_URL = "sqlite:///budget_tracker.sqlite3"


def get_database_url() -> str:
    """
    По умолчанию используем sqlite файл в корне проекта.
    Можно переопределить через переменную окружения BUDGET_DB_URL.
    """
    return os.getenv("BUDGET_DB_URL", DEFAULT_DB_URL)


def create_db_engine(echo: bool = False):
    db_url = get_database_url()

    # SQLite: немного настроек для стабильности
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

    return create_engine(
        db_url,
        echo=echo,
        future=True,
        connect_args=connect_args,
    )


engine = create_db_engine(echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
