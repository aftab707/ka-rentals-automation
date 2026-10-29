"""Database connection engine and session factory."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.models.base import Base

db_url = settings.DATABASE_URL
# Render PostgreSQL URLs start with postgres://, SQLAlchemy requires postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Ensure the database directory exists if using a file path
if db_url.startswith("sqlite:///"):
    db_file_path = db_url.replace("sqlite:///", "")
    from pathlib import Path
    db_dir = Path(db_file_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine_to_use=None):
    """Initializes tables in database and applies lightweight column migrations."""
    target_engine = engine_to_use or engine
    Base.metadata.create_all(bind=target_engine)

    # Lightweight check to ensure newly added DocuSign columns exist in contracts table
    with target_engine.connect() as conn:
        try:
            from sqlalchemy import text
            result = conn.execute(text("PRAGMA table_info(contracts)"))
            existing_cols = {row[1] for row in result.fetchall()}
            if existing_cols:
                if "docusign_envelope_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE contracts ADD COLUMN docusign_envelope_id VARCHAR(128)"))
                if "docusign_status" not in existing_cols:
                    conn.execute(text("ALTER TABLE contracts ADD COLUMN docusign_status VARCHAR(64)"))
                if "signed_at" not in existing_cols:
                    conn.execute(text("ALTER TABLE contracts ADD COLUMN signed_at DATETIME"))
                conn.commit()
        except Exception:
            pass


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
