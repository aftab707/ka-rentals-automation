"""Canonical Pydantic models for Fleet Rental Automation.

Defines the normalized entities and data quality issue tracking schemas.
Source values and location metadata (source_sheet, source_row) are always preserved.
"""

from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PCNStatus(str, Enum):
    PAID = "paid"
    UNPAID = "unpaid"
    ACTION_NEEDED = "action_needed"
    NEEDS_REVIEW = "needs_review"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"


class ContractStatus(str, Enum):
    SIGNED = "signed"
    NOT_SIGNED = "not_signed"
    NO_CONTRACT = "no_contract"
    UNKNOWN = "unknown"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    PCN = "pcn"
    CONTRACT = "contract"
    CUSTOMER = "customer"
    VEHICLE = "vehicle"
    EXCEL_STRUCTURE = "excel_structure"


class DataQualityIssue(BaseModel):
    """Tracks anomalies, missing fields, or conflicts detected during cleaning."""

    model_config = ConfigDict(frozen=True)

    category: IssueCategory
    issue_type: str
    severity: IssueSeverity
    record_identifier: Optional[str] = None
    source_sheet: str
    source_row: int
    field_name: Optional[str] = None
    raw_value: Optional[str] = None
    description: str


class CustomerRecord(BaseModel):
    """Normalized master customer profile."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    driving_license: Optional[str] = None
    source_sheet: str = "Customer details"
    source_row: int


class PCNRecord(BaseModel):
    """Normalized PCN violation ticket with raw preservation and traceability."""

    model_config = ConfigDict(from_attributes=True)

    ticket_number: str
    raw_ticket_number: str
    vehicle_registration: Optional[str] = None
    normalized_registration: Optional[str] = None
    issue_date: Optional[date] = None
    fine_amount: Optional[float] = None
    raw_status: Optional[str] = None
    normalized_status: PCNStatus
    customer_name_raw: Optional[str] = None
    matched_customer_id: Optional[int] = None
    payment_url: Optional[str] = None
    source_sheet: str
    source_row: int
    has_conflict: bool = False
    conflict_notes: Optional[str] = None


class ContractRecord(BaseModel):
    """Normalized fleet vehicle rental agreement."""

    model_config = ConfigDict(from_attributes=True)

    contract_id: Optional[int] = None
    vehicle_registration: str
    normalized_registration: str
    customer_name_raw: Optional[str] = None
    matched_customer_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rate: Optional[float] = None
    payment_period: Optional[str] = None  # e.g., 'month', 'week'
    raw_status: Optional[str] = None
    normalized_status: ContractStatus
    vehicle_model: Optional[str] = None
    hire_duration_raw: Optional[str] = None
    source_sheet: str
    source_row: int


class VehicleRecord(BaseModel):
    """Normalized vehicle fleet entity."""

    model_config = ConfigDict(from_attributes=True)

    vehicle_registration: str
    normalized_registration: str
    make_model: Optional[str] = None
    current_mileage: Optional[float] = None
    assigned_driver_raw: Optional[str] = None
    active_contract_status: Optional[str] = None
    source_sheet: str
    source_row: int


class CleaningResult(BaseModel):
    """Encapsulates the output of a data cleaning run."""

    customers: List[CustomerRecord] = Field(default_factory=list)
    pcns: List[PCNRecord] = Field(default_factory=list)
    contracts: List[ContractRecord] = Field(default_factory=list)
    vehicles: List[VehicleRecord] = Field(default_factory=list)
    issues: List[DataQualityIssue] = Field(default_factory=list)
    total_records_processed: int = 0
