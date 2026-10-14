
"""
Database configuration and session management.

Provides the SQLAlchemy base class, engine, session factory,
database initialization, and FastAPI-compatible session dependency.
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings


logger = logging.getLogger(__name__)


# ============================================================
# Database Base
# ============================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


# ============================================================
# Database Engine
# ============================================================

def _build_engine() -> Engine:
    """Create the SQLAlchemy engine using application settings."""

    database_url = settings.DATABASE_URL

    if not database_url:
        raise ValueError("DATABASE_URL must not be empty.")

    connect_args: dict[str, object] = {}

    # Allow SQLite connections across application threads.
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    try:
        database_engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    except Exception:
        logger.exception("Failed to create the database engine.")
        raise

    logger.info("Database engine created successfully.")
    return database_engine


engine = _build_engine()


# ============================================================
# Session Factory
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ============================================================
# Database Initialization
# ============================================================

def init_db() -> None:
    """
    Create database tables registered with Base.metadata.

    Import models before create_all() so their tables are
    registered with SQLAlchemy.
    """

    try:
        from database import models  # noqa: F401

        Base.metadata.create_all(bind=engine)

        logger.info("Database initialized successfully.")

    except Exception:
        logger.exception("Database initialization failed.")
        raise


# ============================================================
# Database Session Dependency
# ============================================================

def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and close it after the request.

    Roll back the current transaction if an exception occurs.
    Transaction commits remain the responsibility of the caller.
    """

    db = SessionLocal()

    try:
        yield db

    except Exception:
        try:
            db.rollback()
        except Exception:
            logger.exception("Database session rollback failed.")

        raise

    finally:
        try:
            db.close()
        except Exception:
            logger.exception("Failed to close database session.")
            raise
