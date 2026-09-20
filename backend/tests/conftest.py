from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal, init_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    init_db()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()