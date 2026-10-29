"""Unit and integration tests for Step 7: Report Generation & Mock Delivery."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.schemas.report import ActionItem, OperationalReport
from backend.app.services.importer import run_import_pipeline
from backend.app.services.reporter import (
    generate_daily_operational_report,
    render_html_email_report,
    render_markdown_email_report,
)


@pytest.fixture(scope="module")
def report_test_env():
    """Sets up an in-memory database populated with real workbook data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    # Import data from source workbook
    base_dir = Path(__file__).resolve().parent.parent.parent
    file_path = base_dir / "data" / "source" / "KA rentals DB.xlsx"

    with Session(engine) as session:
        run_import_pipeline(file_path, session)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield {"engine": engine, "client": client}

    app.dependency_overrides.clear()


def test_reporter_service_daily_report_generation(report_test_env):
    """Verify generate_daily_operational_report generates accurate categorized items."""
    with Session(report_test_env["engine"]) as session:
        report = generate_daily_operational_report(session)

    assert isinstance(report, OperationalReport)
    assert report.is_mock_preview is True
    assert report.report_id.startswith("REP-")
    assert report.total_fleet_vehicles == 14
    assert report.signed_contracts == 10
    assert report.unsigned_contracts == 3
    assert report.total_open_pcns > 0
    assert report.total_unpaid_amount > 0

    # Verify status conflict categorization (Priority 1)
    assert report.status_conflicts_count >= 1
    conflict_tickets = [item.identifier for item in report.conflicting_pcns]
    assert "2577262100014" in conflict_tickets

    conflict_item = next(item for item in report.conflicting_pcns if item.identifier == "2577262100014")
    assert conflict_item.category == "PCN"
    assert conflict_item.subcategory == "STATUS_CONFLICT"
    assert conflict_item.source_sheet in ["Outstanding PCN", "paying needed", "kashif "]
    assert conflict_item.source_row > 0
    assert "portal" in conflict_item.recommended_action.lower()

    # Verify Action Needed PCNs
    assert len(report.action_needed_pcns) > 0
    for item in report.action_needed_pcns:
        assert item.category == "PCN"
        assert item.subcategory == "ACTION_NEEDED"
        assert item.source_sheet != ""
        assert item.source_row > 0
        assert len(item.recommended_action) > 10

    # Verify Contracts Requiring Action
    assert len(report.contracts_requiring_action) > 0
    for contract_item in report.contracts_requiring_action:
        assert contract_item.category == "CONTRACT"
        assert contract_item.source_sheet != ""
        assert contract_item.source_row > 0
        assert len(contract_item.recommended_action) > 5

    # Verify Incomplete Customers
    assert len(report.incomplete_customers) > 0
    for cust_item in report.incomplete_customers:
        assert cust_item.category == "CUSTOMER"
        assert cust_item.source_sheet == "Customer details"
        assert cust_item.source_row > 0
        assert "documentation" in cust_item.recommended_action.lower() or "compliance" in cust_item.recommended_action.lower()


def test_reporter_render_html_preview(report_test_env):
    """Verify HTML email rendering produces structured HTML with mock banners."""
    with Session(report_test_env["engine"]) as session:
        report = generate_daily_operational_report(session)
        html = render_html_email_report(report)

    assert "<!DOCTYPE html>" in html
    assert "Daily Operational Review Report" in html
    assert report.report_id in html
    assert "MOCK EMAIL PREVIEW:" in html
    assert "Priority 1: Multi-Sheet Status Conflicts" in html
    assert "2577262100014" in html
    assert "Executive Operations Summary" in html


def test_reporter_render_markdown_preview(report_test_env):
    """Verify Markdown summary produces text digest with mock disclaimer."""
    with Session(report_test_env["engine"]) as session:
        report = generate_daily_operational_report(session)
        md = render_markdown_email_report(report)

    assert "# KA Rentals - Daily Operational Review Report" in md
    assert "[PROTOTYPE MOCK PREVIEW - NO LIVE EMAIL SENT]" in md
    assert "2577262100014" in md
    assert "Priority 1: Multi-Sheet Status Conflicts" in md


def test_api_reports_daily_json(report_test_env):
    """Verify GET /api/reports/daily/json returns validated OperationalReport."""
    client = report_test_env["client"]
    response = client.get("/api/reports/daily/json")

    assert response.status_code == 200
    data = response.json()
    assert data["is_mock_preview"] is True
    assert data["total_fleet_vehicles"] == 14
    assert data["status_conflicts_count"] >= 1
    assert len(data["conflicting_pcns"]) >= 1
    assert any(c["identifier"] == "2577262100014" for c in data["conflicting_pcns"])


def test_api_reports_daily_html(report_test_env):
    """Verify GET /api/reports/daily/html returns 200 with HTML content-type."""
    client = report_test_env["client"]
    response = client.get("/api/reports/daily/html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!DOCTYPE html>" in response.text
    assert "MOCK EMAIL PREVIEW" in response.text


def test_api_reports_mock_email_send(report_test_env):
    """Verify POST /api/reports/email/mock-send simulates dispatch safely."""
    client = report_test_env["client"]
    payload = {
        "recipient_email": "fleet-audit@internal.karentals.mock",
        "subject_override": "Custom Test Operational Dispatch",
    }
    response = client.post("/api/reports/email/mock-send", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MOCK_SENT_SUCCESS"
    assert data["recipient"] == "fleet-audit@internal.karentals.mock"
    assert data["subject"] == "Custom Test Operational Dispatch"
    assert data["mock_mode"] is True
    assert "fleet-audit@internal.karentals.mock" in data["message_preview_snippet"]


def test_api_reports_mock_email_send_defaults(report_test_env):
    """Verify POST /api/reports/email/mock-send works with default body."""
    client = report_test_env["client"]
    response = client.post("/api/reports/email/mock-send", json={})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "MOCK_SENT_SUCCESS"
    assert data["recipient"] == "operations-team@mock.karentals.internal"
    assert "KA Rentals Daily Operational Review" in data["subject"]
    assert data["mock_mode"] is True
