"""Tests for SQLite database schema, atomic transactions, and idempotent import pipeline."""

from datetime import datetime
from pathlib import Path
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from backend.app.models.base import Base
from backend.app.models.entities import (
    Contract,
    Customer,
    DataQualityIssueRecord,
    ImportRun,
    PCN,
    Vehicle,
)
from backend.app.services.importer import run_import_pipeline


@pytest.fixture
def test_db_session():
    """Provides a fresh, isolated in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session


def test_schema_initialization(test_db_session):
    """Verify that all entity tables are initialized properly."""
    session = test_db_session
    # Check table existence by inserting a test customer and querying
    cust = Customer(
        id=999,
        full_name="Test Customer",
        email="test@example.com",
        source_sheet="Customer details",
        source_row=2,
    )
    session.add(cust)
    session.commit()

    queried = session.get(Customer, 999)
    assert queried is not None
    assert queried.full_name == "Test Customer"


def test_valid_and_idempotent_import(test_db_session):
    """Verify that a valid import creates records and re-importing does not double counts."""
    session = test_db_session
    base_dir = Path(__file__).resolve().parent.parent.parent
    file_path = base_dir / "data" / "source" / "KA rentals DB.xlsx"

    # 1. First import
    run1 = run_import_pipeline(file_path, session)
    assert run1.status == "success"
    assert run1.customers_count == 52
    assert run1.contracts_count == 13
    assert run1.pcns_count == 78

    c_count1 = session.scalar(select(func.count(Customer.id)))
    v_count1 = session.scalar(select(func.count(Vehicle.id)))
    cnt_count1 = session.scalar(select(func.count(Contract.id)))
    p_count1 = session.scalar(select(func.count(PCN.id)))

    assert c_count1 == 52
    assert cnt_count1 == 13
    assert p_count1 == 78

    # 2. Second import (Idempotency test)
    run2 = run_import_pipeline(file_path, session)
    assert run2.status == "success"

    c_count2 = session.scalar(select(func.count(Customer.id)))
    v_count2 = session.scalar(select(func.count(Vehicle.id)))
    cnt_count2 = session.scalar(select(func.count(Contract.id)))
    p_count2 = session.scalar(select(func.count(PCN.id)))

    # Counts must NOT double!
    assert c_count2 == c_count1
    assert v_count2 == v_count1
    assert cnt_count2 == cnt_count1
    assert p_count2 == p_count1

    # But we should have 2 distinct import run audit records
    runs_count = session.scalar(select(func.count(ImportRun.id)))
    assert runs_count == 2


def test_duplicate_pcn_and_status_conflict_in_db(test_db_session):
    """Verify that cross-sheet PCN conflict is persisted with has_conflict=True."""
    session = test_db_session
    base_dir = Path(__file__).resolve().parent.parent.parent
    file_path = base_dir / "data" / "source" / "KA rentals DB.xlsx"

    run_import_pipeline(file_path, session)

    # Check for conflict PCN
    conflicts = session.scalars(select(PCN).where(PCN.has_conflict.is_(True))).all()
    assert len(conflicts) >= 1
    assert any(c.normalized_status == "conflict" for c in conflicts)

    # Check that critical data quality issue was logged in DB
    crit_issues = session.scalars(
        select(DataQualityIssueRecord).where(DataQualityIssueRecord.severity == "critical")
    ).all()
    assert len(crit_issues) >= 1
    assert any(i.issue_type == "STATUS_CONFLICT" for i in crit_issues)


def test_atomic_rollback_on_failure(test_db_session, monkeypatch):
    """Verify that an exception mid-pipeline rolls back changes and records failure."""
    session = test_db_session
    base_dir = Path(__file__).resolve().parent.parent.parent
    file_path = base_dir / "data" / "source" / "KA rentals DB.xlsx"

    # Simulate an error during PCN insertion
    from backend.app.services import importer

    orig_clean = importer.load_and_clean_workbook

    def mock_clean_fail(path):
        res = orig_clean(path)
        # Force an invalid PCN record that fails DB constraints
        res.pcns[0].ticket_number = None  # Non-nullable field in DB
        return res

    monkeypatch.setattr(importer, "load_and_clean_workbook", mock_clean_fail)

    with pytest.raises(Exception):
        run_import_pipeline(file_path, session)

    # Assert that no customers, contracts or PCNs were persisted (full atomic rollback)
    assert session.scalar(select(func.count(Customer.id))) == 0
    assert session.scalar(select(func.count(Contract.id))) == 0
    assert session.scalar(select(func.count(PCN.id))) == 0

    # But the ImportRun record exists with status 'failed'
    failed_run = session.scalar(select(ImportRun).where(ImportRun.status == "failed"))
    assert failed_run is not None
    assert failed_run.error_message is not None
