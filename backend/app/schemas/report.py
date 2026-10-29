"""Schemas for Operational Daily Report Generation and Mock Email Delivery."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ActionItem(BaseModel):
    """An actionable item requiring fleet staff review."""

    model_config = ConfigDict(from_attributes=True)

    category: str  # PCN, CONTRACT, CUSTOMER
    subcategory: str  # CONFLICT, UNPAID, UNSIGNED_CONTRACT, INCOMPLETE_CUSTOMER
    identifier: str  # Ticket number, Reg number, Customer Name
    description: str
    amount: Optional[float] = None
    status: str
    source_sheet: str
    source_row: int
    recommended_action: str


class OperationalReport(BaseModel):
    """Compiled daily operational report for KA Rentals."""

    model_config = ConfigDict(from_attributes=True)

    report_id: str
    generated_at: datetime
    is_mock_preview: bool = True

    # High-level Metrics
    total_fleet_vehicles: int
    signed_contracts: int
    unsigned_contracts: int
    total_open_pcns: int
    total_unpaid_amount: float
    status_conflicts_count: int

    # Categorized Action Groups
    conflicting_pcns: List[ActionItem]
    action_needed_pcns: List[ActionItem]
    unpaid_pcns: List[ActionItem]
    needs_review_pcns: List[ActionItem]
    contracts_requiring_action: List[ActionItem]
    incomplete_customers: List[ActionItem]


class MockEmailRequest(BaseModel):
    recipient_email: str = "operations-team@mock.karentals.internal"
    subject_override: Optional[str] = None


class MockEmailResponse(BaseModel):
    status: str
    recipient: str
    subject: str
    sent_at: datetime
    mock_mode: bool = True
    message_preview_snippet: str
