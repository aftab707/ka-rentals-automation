"""Auto-seed engine to ensure cloud deployments always have initial fleet and PCN data."""

import json
import logging
from pathlib import Path
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.entities import (
    Customer,
    Vehicle,
    Contract,
    PCN,
    DataQualityIssueRecord,
    ImportRun,
)

logger = logging.getLogger(__name__)

SEED_FILE = Path(__file__).parent / "seed_data.json"


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return None


def _parse_d(val: Optional[str]) -> Optional[date]:
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except Exception:
        return None


def seed_database_if_empty(db: Session) -> bool:
    """Checks if the database is empty; if so, populates initial fleet, contracts, and PCNs."""
    vehicle_count = db.query(Vehicle).count()
    if vehicle_count > 0:
        logger.debug("Database already contains %d vehicles; skipping auto-seed.", vehicle_count)
        return False

    if not SEED_FILE.exists():
        logger.warning("Seed data file %s does not exist; skipping auto-seed.", SEED_FILE)
        return False

    logger.info("Database is empty. Initiating automatic seed from %s...", SEED_FILE.name)

    try:
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Import Run
        for item in data.get("imports", []):
            item["started_at"] = _parse_dt(item.get("started_at"))
            item["completed_at"] = _parse_dt(item.get("completed_at"))
            db.merge(ImportRun(**item))
        db.commit()

        # 2. Customers
        for item in data.get("customers", []):
            item["created_at"] = _parse_dt(item.get("created_at"))
            item["updated_at"] = _parse_dt(item.get("updated_at"))
            db.merge(Customer(**item))
        db.commit()

        # 3. Vehicles
        for item in data.get("vehicles", []):
            item["created_at"] = _parse_dt(item.get("created_at"))
            item["updated_at"] = _parse_dt(item.get("updated_at"))
            db.merge(Vehicle(**item))
        db.commit()

        # 4. Contracts
        for item in data.get("contracts", []):
            item["start_date"] = _parse_d(item.get("start_date"))
            item["end_date"] = _parse_d(item.get("end_date"))
            item["signed_at"] = _parse_dt(item.get("signed_at"))
            item["created_at"] = _parse_dt(item.get("created_at"))
            item["updated_at"] = _parse_dt(item.get("updated_at"))
            db.merge(Contract(**item))
        db.commit()

        # 5. PCNs
        for item in data.get("pcns", []):
            item["issue_date"] = _parse_d(item.get("issue_date"))
            item["created_at"] = _parse_dt(item.get("created_at"))
            item["updated_at"] = _parse_dt(item.get("updated_at"))
            db.merge(PCN(**item))
        db.commit()

        # 6. Data Quality Issues (load first 100 for fast startup)
        for item in data.get("issues", [])[:100]:
            item["created_at"] = _parse_dt(item.get("created_at"))
            db.merge(DataQualityIssueRecord(**item))
        db.commit()

        logger.info(
            "Auto-seeded database successfully: %d vehicles, %d contracts, %d PCNs.",
            len(data.get("vehicles", [])),
            len(data.get("contracts", [])),
            len(data.get("pcns", [])),
        )
        return True
    except Exception as e:
        logger.error("Failed to auto-seed database: %s", str(e))
        db.rollback()
        return False
