"""Core application configuration settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application runtime settings."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    CORS_ORIGINS: str = "http://localhost:5173"

    # SQLite Database Default Path: data/processed/fleet_rental.db
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'processed' / 'fleet_rental.db'}"

    SOURCE_DATA_PATH: Path = BASE_DIR / "data" / "source"
    PROCESSED_DATA_PATH: Path = BASE_DIR / "data" / "processed"


settings = Settings()
