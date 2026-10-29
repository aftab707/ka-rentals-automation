"""Core application configuration settings."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory is project root D:\KARental
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Load .env file if present
env_path = BASE_DIR / "backend" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class Settings:
    """Application runtime settings using standard environment variables."""

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "127.0.0.1")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    # SQLite Database Default Path: data/processed/fleet_rental.db
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'data' / 'processed' / 'fleet_rental.db'}",
    )

    SOURCE_DATA_PATH: Path = Path(os.getenv("SOURCE_DATA_PATH", str(BASE_DIR / "data" / "source")))
    PROCESSED_DATA_PATH: Path = Path(os.getenv("PROCESSED_DATA_PATH", str(BASE_DIR / "data" / "processed")))


settings = Settings()
