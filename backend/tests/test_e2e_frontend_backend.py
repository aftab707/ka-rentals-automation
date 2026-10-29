"""End-to-end integration tests validating React frontend data flow against live backend."""

from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_e2e_dashboard_summary_matches_db():
    """Verify OverviewPage API call receives exact operational KPI numbers."""
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    summary = resp.json()

    # Exact numbers calculated from KA rentals DB.xlsx
    assert summary["total_vehicles"] == 14
    assert summary["total_pcns"] == 78
    assert summary["action_needed_pcns"] == 38
    assert summary["unpaid_pcns"] == 23
    assert summary["conflict_pcns"] == 1
    assert summary["paid_pcns"] == 8
    assert summary["total_issues"] == 75
    assert summary["critical_issues"] == 1

    # Verify latest import metadata
    assert summary["latest_import"] is not None
    assert summary["latest_import"]["status"] == "success"
    assert "started_at" in summary["latest_import"]


def test_e2e_pcn_conflict_traceability():
    """Verify PCNsPage conflict filter returns conflict ticket with complete source traceability."""
    resp = client.get("/api/pcns?has_conflict=true")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 1
    conflict_ticket = data["items"][0]
    assert conflict_ticket["ticket_number"] == "2577262100014"
    assert conflict_ticket["normalized_status"] == "conflict"
    assert conflict_ticket["has_conflict"] is True
    assert "Outstanding PCN" in conflict_ticket["conflict_notes"]
    assert "paying needed" in conflict_ticket["conflict_notes"]
    assert conflict_ticket["source_sheet"] != ""
    assert conflict_ticket["source_row"] > 0


def test_e2e_pcn_search_and_empty_state():
    """Verify PCNsPage search functionality and empty state for unknown queries."""
    # Search for an existing vehicle
    resp_found = client.get("/api/pcns?search=LA19WPD")
    assert resp_found.status_code == 200
    assert resp_found.json()["total"] > 0

    # Search for a non-existent plate (testing empty state)
    resp_empty = client.get("/api/pcns?search=ZZ99ZZZ_NONEXISTENT")
    assert resp_empty.status_code == 200
    data_empty = resp_empty.json()
    assert data_empty["total"] == 0
    assert len(data_empty["items"]) == 0


def test_e2e_contracts_and_vehicles():
    """Verify ContractsPage receives contracts and vehicle make/models."""
    resp = client.get("/api/contracts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 13

    # Check vehicle list
    resp_v = client.get("/api/vehicles")
    assert resp_v.status_code == 200
    vehicles = resp_v.json()
    assert len(vehicles) == 14
    # Models from pay day enriched into vehicles
    models = {v["make_model"] for v in vehicles if v["make_model"]}
    assert "Tesla Model 3" in models or "Kia Niro" in models


def test_e2e_data_quality_severity_filter():
    """Verify DataQualityPage critical issue audit returns the multi-sheet conflict alert."""
    resp = client.get("/api/data-quality/issues?severity=critical")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(item["severity"] == "critical" for item in data["items"])
    assert any(item["issue_type"] == "STATUS_CONFLICT" for item in data["items"])


def test_e2e_excel_upload_and_idempotency_flow():
    """Verify ImportsPage upload flow: re-uploading file succeeds idempotently and updates history."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    file_path = base_dir / "data" / "source" / "KA rentals DB.xlsx"

    with open(file_path, "rb") as f:
        files = {"file": ("KA rentals DB.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = client.post("/api/import/excel", files=files)

    assert resp.status_code == 201
    run_result = resp.json()
    assert run_result["status"] == "success"
    assert run_result["customers_count"] == 52
    assert run_result["contracts_count"] == 13
    assert run_result["pcns_count"] == 78

    # Verify counts in summary did not duplicate
    resp_sum = client.get("/api/dashboard/summary")
    summary = resp_sum.json()
    assert summary["total_vehicles"] == 14
    assert summary["total_pcns"] == 78

    # Verify import history has the new run
    resp_hist = client.get("/api/imports")
    assert resp_hist.status_code == 200
    runs = resp_hist.json()
    assert len(runs) >= 2


def test_e2e_report_preview_structure():
    """Verify ReportPreviewPage API returns all operational sections."""
    resp = client.post("/api/reports/preview")
    assert resp.status_code == 200
    report = resp.json()

    assert "generated_at" in report
    assert "summary" in report
    assert len(report["conflicts"]) == 1
    assert len(report["urgent_pcns"]) > 0
    assert len(report["contracts_requiring_action"]) > 0
    assert len(report["critical_issues"]) == 1
