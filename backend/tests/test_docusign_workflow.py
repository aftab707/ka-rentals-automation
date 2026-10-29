"""Automated tests for Step 8: DocuSign Integration, Direct Driver Onboarding, and Webhook."""

from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.session import get_db, init_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.entities import Contract, Customer, Vehicle
from backend.app.services.docusign_service import (
    generate_contract_html,
    get_docusign_access_token,
    process_docusign_webhook_event,
)


@pytest.fixture(scope="module")
def docusign_test_client():
    """Sets up an in-memory SQLite DB and TestClient."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield {"engine": engine, "client": client}

    app.dependency_overrides.clear()


def test_docusign_jwt_token_generation():
    """Verify live JWT bearer token exchange with DocuSign Developer Portal."""
    token = get_docusign_access_token()
    assert token is not None
    assert len(token) > 50
    # Second call should use cached token
    cached = get_docusign_access_token()
    assert cached == token


def test_contract_html_generation_has_statement_of_liability():
    """Verify generated agreement HTML includes UK Road Traffic Acts and PCN liability."""
    contract = Contract(
        id=999,
        vehicle_registration="LP21 FYB",
        normalized_registration="LP21FYB",
        customer_name_raw="Test Driver",
        start_date=date(2026, 6, 18),
        end_date=date(2026, 7, 16),
        rate=325.0,
        vehicle_model="Toyota Corolla Hybrid",
    )
    customer = Customer(
        id=101,
        full_name="Test Driver",
        email="driver@test.co.uk",
        phone="07123456789",
        driving_license="TESTD123456AB9CD",
    )
    vehicle = Vehicle(
        registration="LP21 FYB",
        normalized_registration="LP21FYB",
        make_model="Toyota Corolla Hybrid",
    )

    html = generate_contract_html(contract, customer, vehicle, customer_address="123 Test Street, London")

    assert "K.A RENTALS LTD" in html
    assert "LP21 FYB" in html
    assert "Test Driver" in html
    assert "Section 66 of the Road Traffic Offenders Act 1988" in html
    assert "Protection of Freedoms Act 2012" in html
    assert "/sn1/" in html


def test_create_new_hire_agreement_endpoint(docusign_test_client):
    """Verify POST /api/contracts onboards driver and creates contract without Excel."""
    client = docusign_test_client["client"]
    payload = {
        "vehicle_registration": "WG20 VZP",
        "vehicle_model": "MG ZS EV",
        "customer_name": "Samuel Davies",
        "customer_email": "samuel.davies@example.co.uk",
        "customer_phone": "07987654321",
        "customer_license": "DAVIE987654SD12",
        "customer_address": "45 High Street, Croydon",
        "start_date": "2026-10-30",
        "rate": 280.0,
        "hire_duration": "28 days",
        "send_docusign": False,
    }

    response = client.post("/api/contracts", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["normalized_registration"] == "WG20VZP"
    assert data["customer_name_raw"] == "Samuel Davies"
    assert data["rate"] == 280.0
    assert data["normalized_status"] == "not_signed"
    assert data["source_sheet"] == "Direct Dashboard"

    # Verify database persistence
    with Session(docusign_test_client["engine"]) as session:
        cust = session.scalar(select(Customer).where(Customer.email == "samuel.davies@example.co.uk"))
        assert cust is not None
        assert cust.driving_license == "DAVIE987654SD12"

        veh = session.scalar(select(Vehicle).where(Vehicle.normalized_registration == "WG20VZP"))
        assert veh is not None
        assert veh.assigned_driver == "Samuel Davies"


def test_docusign_webhook_event_processing(docusign_test_client):
    """Verify DocuSign webhook event automatically completes agreement and marks it signed."""
    client = docusign_test_client["client"]
    engine = docusign_test_client["engine"]

    # 1. Seed a contract with a mock envelope ID
    test_envelope_id = "test-env-docusign-uuid-9999"
    with Session(engine) as session:
        contract = Contract(
            vehicle_registration="NA19 ZKW",
            normalized_registration="NA19ZKW",
            customer_name_raw="Clinton Osuhon",
            rate=260.0,
            normalized_status="not_signed",
            raw_status="sent_for_signature",
            docusign_envelope_id=test_envelope_id,
            docusign_status="sent",
            source_sheet="Direct Dashboard",
        )
        session.add(contract)
        session.commit()
        contract_id = contract.id

    # 2. Post webhook event indicating driver has signed
    webhook_payload = {
        "envelopeId": test_envelope_id,
        "event": "envelope-completed",
        "status": "completed",
    }
    response = client.post("/api/webhooks/docusign", json=webhook_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "processed"
    assert res_data["contract_status"] == "signed"
    assert res_data["docusign_status"] == "completed"

    # 3. Verify database state updated automatically
    with Session(engine) as session:
        updated = session.get(Contract, contract_id)
        assert updated.normalized_status == "signed"
        assert updated.docusign_status == "completed"
        assert updated.signed_at is not None


def test_check_docusign_status_not_sent(docusign_test_client):
    """Verify checking status for an unsent contract returns clear message."""
    client = docusign_test_client["client"]
    engine = docusign_test_client["engine"]

    with Session(engine) as session:
        c = Contract(
            vehicle_registration="EK70 DGZ",
            normalized_registration="EK70DGZ",
            customer_name_raw="No Envelope Driver",
            normalized_status="not_signed",
            source_sheet="Direct Dashboard",
        )
        session.add(c)
        session.commit()
        cid = c.id

    res = client.get(f"/api/contracts/{cid}/docusign-status")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["status"] == "not_sent"
