"""SQLAlchemy 2.x Entity Models for Fleet Rental Automation."""

from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class ImportRun(Base):
    """Tracks each execution of the Excel data import pipeline."""

    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="running")  # running, success, failed
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metrics
    customers_count: Mapped[int] = mapped_column(Integer, default=0)
    contracts_count: Mapped[int] = mapped_column(Integer, default=0)
    vehicles_count: Mapped[int] = mapped_column(Integer, default=0)
    pcns_count: Mapped[int] = mapped_column(Integer, default=0)
    issues_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    issues: Mapped[list["DataQualityIssueRecord"]] = relationship(
        "DataQualityIssueRecord", back_populates="import_run", cascade="all, delete-orphan"
    )


class Customer(Base):
    """Master Customer Directory."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # Derived from Excel 'sr'
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    driving_license: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    source_sheet: Mapped[str] = mapped_column(String(64), default="Customer details")
    source_row: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    contracts: Mapped[list["Contract"]] = relationship("Contract", back_populates="customer")
    pcns: Mapped[list["PCN"]] = relationship("PCN", back_populates="customer")


class Vehicle(Base):
    """Fleet Vehicle Directory."""

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registration: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_registration: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    make_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    current_mileage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assigned_driver: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active_contract_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    source_sheet: Mapped[str] = mapped_column(String(64), default="Current Contracts")
    source_row: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    contracts: Mapped[list["Contract"]] = relationship("Contract", back_populates="vehicle")
    pcns: Mapped[list["PCN"]] = relationship("PCN", back_populates="vehicle")


class Contract(Base):
    """Rental Contracts and Agreements."""

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_ref: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vehicle_registration: Mapped[str] = mapped_column(String(32), nullable=False)
    normalized_registration: Mapped[str] = mapped_column(
        String(32), ForeignKey("vehicles.normalized_registration"), nullable=False, index=True
    )
    customer_name_raw: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    matched_customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"), nullable=True)

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    payment_period: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    raw_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    normalized_status: Mapped[str] = mapped_column(String(32), index=True, default="unknown")
    vehicle_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    hire_duration: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    source_sheet: Mapped[str] = mapped_column(String(64), default="Current Contracts")
    source_row: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="contracts")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="contracts")


class PCN(Base):
    """PCN / Parking Infringement Notices."""

    __tablename__ = "pcns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    raw_ticket_number: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_registration: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    normalized_registration: Mapped[Optional[str]] = mapped_column(
        String(32), ForeignKey("vehicles.normalized_registration"), nullable=True, index=True
    )
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fine_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_status: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    normalized_status: Mapped[str] = mapped_column(String(32), index=True, default="unknown")
    customer_name_raw: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    matched_customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"), nullable=True)
    payment_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_sheet: Mapped[str] = mapped_column(String(64), nullable=False)
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    has_conflict: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    conflict_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    vehicle: Mapped[Optional["Vehicle"]] = relationship("Vehicle", back_populates="pcns")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="pcns")


class DataQualityIssueRecord(Base):
    """Audit Log of Data Quality Issues and Conflicts."""

    __tablename__ = "data_quality_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    import_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_runs.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    issue_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)  # critical, warning, info
    record_identifier: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_sheet: Mapped[str] = mapped_column(String(64), nullable=False)
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    field_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    raw_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    import_run: Mapped[Optional["ImportRun"]] = relationship("ImportRun", back_populates="issues")
