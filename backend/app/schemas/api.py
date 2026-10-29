"""Pydantic schemas for FastAPI endpoints."""

from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class ImportRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_hash: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    customers_count: int = 0
    contracts_count: int = 0
    vehicles_count: int = 0
    pcns_count: int = 0
    issues_count: int = 0
    error_message: Optional[str] = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    driving_license: Optional[str] = None
    source_sheet: str
    source_row: int


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registration: str
    normalized_registration: str
    make_model: Optional[str] = None
    current_mileage: Optional[float] = None
    assigned_driver: Optional[str] = None
    active_contract_status: Optional[str] = None


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_ref: Optional[int] = None
    vehicle_registration: str
    normalized_registration: str
    customer_name_raw: Optional[str] = None
    matched_customer_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rate: Optional[float] = None
    payment_period: Optional[str] = None
    raw_status: Optional[str] = None
    normalized_status: str
    vehicle_model: Optional[str] = None
    hire_duration: Optional[str] = None
    source_sheet: str
    source_row: int


class PCNResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    raw_ticket_number: str
    vehicle_registration: Optional[str] = None
    normalized_registration: Optional[str] = None
    issue_date: Optional[date] = None
    fine_amount: Optional[float] = None
    raw_status: Optional[str] = None
    normalized_status: str
    customer_name_raw: Optional[str] = None
    matched_customer_id: Optional[int] = None
    payment_url: Optional[str] = None
    source_sheet: str
    source_row: int
    has_conflict: bool
    conflict_notes: Optional[str] = None


class DataQualityIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    import_run_id: Optional[int] = None
    category: str
    issue_type: str
    severity: str
    record_identifier: Optional[str] = None
    source_sheet: str
    source_row: int
    field_name: Optional[str] = None
    raw_value: Optional[str] = None
    description: str
    created_at: datetime


class DashboardSummary(BaseModel):
    total_vehicles: int
    active_contracts: int
    unsigned_contracts: int
    total_pcns: int
    unpaid_pcns: int
    action_needed_pcns: int
    conflict_pcns: int
    paid_pcns: int
    needs_review_pcns: int
    total_issues: int
    critical_issues: int
    warning_issues: int
    latest_import: Optional[ImportRunResponse] = None


class ReportPreviewItem(BaseModel):
    type: str  # PCN, Contract, DataQuality
    identifier: str
    description: str
    status: str
    source_location: str
    recommended_action: str


class ReportPreviewResponse(BaseModel):
    generated_at: datetime
    summary: DashboardSummary
    urgent_pcns: List[PCNResponse]
    conflicts: List[PCNResponse]
    contracts_requiring_action: List[ContractResponse]
    critical_issues: List[DataQualityIssueResponse]
