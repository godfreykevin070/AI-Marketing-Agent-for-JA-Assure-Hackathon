"""SQLAlchemy engine, session factory and declarative base."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_url = settings.database_url
_connect_args: dict = {}
if _url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    _url,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
)

if _url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Fine for a prototype; use Alembic in production."""
    from app import models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=engine)