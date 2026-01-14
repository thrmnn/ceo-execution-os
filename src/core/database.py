"""
Database connection and session management.

Simple SQLite with WAL mode for better concurrency.
"""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from src.core.models import Base


def get_db_path() -> Path:
    """Get database path from env or default to ~/.ceo-os/data.db."""
    db_path_str = os.getenv("CEO_DB_PATH")

    if db_path_str:
        db_path = Path(db_path_str)
    else:
        db_path = Path.home() / ".ceo-os" / "data.db"

    # Create parent directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL mode and other optimizations for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_engine_instance() -> Engine:
    """Create SQLAlchemy engine with proper configuration."""
    db_path = get_db_path()

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"timeout": 30},
        poolclass=NullPool,  # Simple connection management
        echo=False,  # Set to True for SQL debugging
    )

    return engine


def init_database() -> None:
    """Initialize database tables if they don't exist."""
    engine = create_engine_instance()
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Get a database session.

    Usage:
        session = get_session()
        try:
            # ... do work ...
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    """
    engine = create_engine_instance()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SessionLocal()


def get_session_context() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup (context manager).

    Usage:
        with get_session_context() as session:
            # ... do work ...
            # Automatically commits on success, rolls back on error
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
