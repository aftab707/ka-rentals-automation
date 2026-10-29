"""Integration tests for FastAPI REST endpoints."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.base import Base


@pytest.fixture(scope="module")
def api_test_client():
    """Sets up an in-memory SQLite DB and TestClient for API integration tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_api_health(api_test_client):
    """Verify /api/health endpoint responds with 200 OK."""
    response = api_test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_api_import_excel_validation_bad_extension(api_test_client):
    """Verify uploading a non-excel file is rejected with 400 Bad Request."""
    files = {"file": ("malicious.txt", b"not an excel file", "text/plain")}
    response = api_test_client.post("/api/import/excel", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_api_import_excel_valid(api_test_client):
    """Verify uploading valid workbook imports successfully and returns 201 Created."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    file_path = base_dir / "data" / "source" / "KA rentals DB.xlsx"

    with open(file_path, "rb") as f:
        files = {"file": ("KA rentals DB.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = api_test_client.post("/api/import/excel", files=files)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["customers_count"] == 52
    assert data["contracts_count"] == 13
    assert data["pcns_count"] == 78
    assert data["issues_count"] > 0


def test_api_dashboard_summary(api_test_client):
    """Verify /api/dashboard/summary computes accurate KPIs."""
    response = api_test_client.get("/api/dashboard/summary")
    assert response.status_code == 200
    summary = response.json()

    assert summary["total_vehicles"] == 14
    assert summary["total_pcns"] == 78
    assert summary["unpaid_pcns"] > 0
    assert summary["conflict_pcns"] >= 1
    assert summary["critical_issues"] >= 1
    assert summary["latest_import"] is not None
    assert summary["latest_import"]["status"] == "success"


def test_api_pcns_filtering_and_pagination(api_test_client):
    """Verify /api/pcns pagination and filters."""
    # 1. Default pagination
    resp = api_test_client.get("/api/pcns?page=1&size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 10
    assert data["total"] == 78
    assert data["pages"] == 8

    # 2. Filter by status 'unpaid'
    resp_unpaid = api_test_client.get("/api/pcns?status=unpaid")
    assert resp_unpaid.status_code == 200
    for item in resp_unpaid.json()["items"]:
        assert item["normalized_status"] == "unpaid"

    # 3. Filter by has_conflict
    resp_conflict = api_test_client.get("/api/pcns?has_conflict=true")
    assert resp_conflict.status_code == 200
    items = resp_conflict.json()["items"]
    assert len(items) >= 1
    for item in items:
        assert item["has_conflict"] is True


def test_api_contracts_and_vehicles(api_test_client):
    """Verify contracts and vehicles endpoints."""
    # Contracts
    resp_cnt = api_test_client.get("/api/contracts")
    assert resp_cnt.status_code == 200
    cnt_data = resp_cnt.json()
    assert cnt_data["total"] == 13

    # Vehicles
    resp_veh = api_test_client.get("/api/vehicles")
    assert resp_veh.status_code == 200
    vehicles = resp_veh.json()
    assert len(vehicles) == 14


def test_api_data_quality_issues(api_test_client):
    """Verify data quality issues endpoint with severity filtering."""
    resp = api_test_client.get("/api/data-quality/issues?severity=critical")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    for item in data["items"]:
        assert item["severity"] == "critical"


def test_api_imports_history(api_test_client):
    """Verify /api/imports returns import history."""
    resp = api_test_client.get("/api/imports")
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) >= 1
    assert runs[0]["status"] == "success"


def test_api_reports_preview(api_test_client):
    """Verify POST /api/reports/preview generates operational report preview."""
    resp = api_test_client.post("/api/reports/preview")
    assert resp.status_code == 200
    report = resp.json()

    assert "generated_at" in report
    assert "summary" in report
    assert len(report["conflicts"]) >= 1
    assert len(report["urgent_pcns"]) > 0
    assert len(report["critical_issues"]) >= 1
