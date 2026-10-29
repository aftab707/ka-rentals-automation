"""Database connection engine and session factory."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.models.base import Base

# Ensure the database directory exists if using a file path
if settings.DATABASE_URL.startswith("sqlite:///"):
    db_file_path = settings.DATABASE_URL.replace("sqlite:///", "")
    import os
    from pathlib import Path
    db_dir = Path(db_file_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine_to_use=None):
    """Initializes tables in database."""
    target_engine = engine_to_use or engine
    Base.metadata.create_all(bind=target_engine)


def reset_db(engine_to_use=None):
    """Drops and recreates all tables."""
    target_engine = engine_to_use or engine
    Base.metadata.drop_all(bind=target_engine)
    Base.metadata.create_all(bind=target_engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield an isolated db session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
