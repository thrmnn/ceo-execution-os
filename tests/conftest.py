"""
Pytest configuration and fixtures.
"""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.models import Base


@pytest.fixture(scope="function")
def test_db_session() -> Session:
    """Create an in-memory test database session."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def mock_env(tmp_path: Path, monkeypatch):
    """Mock environment variables for testing."""
    # Use temp directory for database
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("CEO_DB_PATH", str(db_path))

    yield {
        "db_path": db_path,
        "tmp_path": tmp_path,
    }
