"""Idempotent Excel Import Pipeline.

Coordinates file hashing, data loading, atomic transactions, customer matching,
idempotent record upserts, and import execution logging.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    Contract,
    Customer,
    DataQualityIssueRecord,
    ImportRun,
    PCN,
    Vehicle,
)
from backend.app.services.excel_loader import load_and_clean_workbook


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def calculate_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of workbook file for run verification."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_matching_customer_id(
    name_raw: Optional[str],
    customers_by_name: Dict[str, int],
) -> Optional[int]:
    """Attempts to match an informal driver name/handle against master customers."""
    if not name_raw:
        return None

    clean = name_raw.strip().lower()

    # 1. Exact match
    if clean in customers_by_name:
        return customers_by_name[clean]

    # 2. First name match (if exactly one customer shares this first name)
    first_name_candidates = [
        cust_id
        for full_name, cust_id in customers_by_name.items()
        if full_name.startswith(clean + " ") or full_name == clean
    ]
    if len(first_name_candidates) == 1:
        return first_name_candidates[0]

    return None


def run_import_pipeline(file_path: Path, db: Session) -> ImportRun:
    """Executes the complete idempotent import workflow inside an atomic transaction.

    Guarantees:
    - Atomicity: If any step fails, all database modifications are rolled back.
    - Idempotency: Repeated imports update existing records in place without duplicating.
    - Auditability: An ImportRun record is created with timestamps and metrics.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    file_hash = calculate_file_hash(file_path)
    start_time = utc_now()

    # Create initial run record (committed independently so failures can still be logged)
    import_run = ImportRun(
        filename=file_path.name,
        file_hash=file_hash,
        status="running",
        started_at=start_time,
    )
    db.add(import_run)
    db.commit()
    db.refresh(import_run)

    try:
        # Step 1: In-memory loading and cleaning
        clean_result = load_and_clean_workbook(file_path)

        # Step 2: Atomic transactional DB upsert
        # 2.1 Upsert Customers
        customers_by_name: Dict[str, int] = {}
        for c_rec in clean_result.customers:
            existing_c = db.get(Customer, c_rec.customer_id)
            if existing_c:
                existing_c.full_name = c_rec.full_name
                existing_c.email = c_rec.email
                existing_c.phone = c_rec.phone
                existing_c.driving_license = c_rec.driving_license
                existing_c.source_row = c_rec.source_row
                existing_c.updated_at = utc_now()
            else:
                new_c = Customer(
                    id=c_rec.customer_id,
                    full_name=c_rec.full_name,
                    email=c_rec.email,
                    phone=c_rec.phone,
                    driving_license=c_rec.driving_license,
                    source_sheet=c_rec.source_sheet,
                    source_row=c_rec.source_row,
                )
                db.add(new_c)

            customers_by_name[c_rec.full_name.strip().lower()] = c_rec.customer_id

        # Flush customers so foreign keys are available
        db.flush()

        # 2.2 Upsert Vehicles
        for v_rec in clean_result.vehicles:
            stmt = select(Vehicle).where(Vehicle.normalized_registration == v_rec.normalized_registration)
            existing_v = db.scalars(stmt).first()
            if existing_v:
                existing_v.registration = v_rec.vehicle_registration
                existing_v.make_model = v_rec.make_model or existing_v.make_model
                existing_v.current_mileage = v_rec.current_mileage or existing_v.current_mileage
                existing_v.assigned_driver = v_rec.assigned_driver_raw or existing_v.assigned_driver
                existing_v.active_contract_status = v_rec.active_contract_status or existing_v.active_contract_status
                existing_v.updated_at = utc_now()
            else:
                new_v = Vehicle(
                    registration=v_rec.vehicle_registration,
                    normalized_registration=v_rec.normalized_registration,
                    make_model=v_rec.make_model,
                    current_mileage=v_rec.current_mileage,
                    assigned_driver=v_rec.assigned_driver_raw,
                    active_contract_status=v_rec.active_contract_status,
                    source_sheet=v_rec.source_sheet,
                    source_row=v_rec.source_row,
                )
                db.add(new_v)

        db.flush()

        # 2.3 Upsert Contracts
        for c_rec in clean_result.contracts:
            stmt = select(Contract).where(Contract.normalized_registration == c_rec.normalized_registration)
            existing_cnt = db.scalars(stmt).first()

            matched_cust = find_matching_customer_id(c_rec.customer_name_raw, customers_by_name)

            if existing_cnt:
                existing_cnt.vehicle_registration = c_rec.vehicle_registration
                existing_cnt.customer_name_raw = c_rec.customer_name_raw
                existing_cnt.matched_customer_id = matched_cust
                existing_cnt.start_date = c_rec.start_date
                existing_cnt.end_date = c_rec.end_date
                existing_cnt.rate = c_rec.rate
                existing_cnt.payment_period = c_rec.payment_period
                existing_cnt.raw_status = c_rec.raw_status
                existing_cnt.normalized_status = c_rec.normalized_status.value
                existing_cnt.vehicle_model = c_rec.vehicle_model or existing_cnt.vehicle_model
                existing_cnt.hire_duration = c_rec.hire_duration_raw or existing_cnt.hire_duration
                existing_cnt.updated_at = utc_now()
            else:
                new_cnt = Contract(
                    contract_ref=c_rec.contract_id,
                    vehicle_registration=c_rec.vehicle_registration,
                    normalized_registration=c_rec.normalized_registration,
                    customer_name_raw=c_rec.customer_name_raw,
                    matched_customer_id=matched_cust,
                    start_date=c_rec.start_date,
                    end_date=c_rec.end_date,
                    rate=c_rec.rate,
                    payment_period=c_rec.payment_period,
                    raw_status=c_rec.raw_status,
                    normalized_status=c_rec.normalized_status.value,
                    vehicle_model=c_rec.vehicle_model,
                    hire_duration=c_rec.hire_duration_raw,
                    source_sheet=c_rec.source_sheet,
                    source_row=c_rec.source_row,
                )
                db.add(new_cnt)

        # 2.4 Upsert PCNs
        for p_rec in clean_result.pcns:
            stmt = select(PCN).where(PCN.ticket_number == p_rec.ticket_number)
            existing_pcn = db.scalars(stmt).first()

            matched_cust = find_matching_customer_id(p_rec.customer_name_raw, customers_by_name)

            # Ensure vehicle exists for foreign key if normalized_registration provided
            if p_rec.normalized_registration:
                stmt_v = select(Vehicle).where(Vehicle.normalized_registration == p_rec.normalized_registration)
                if not db.scalars(stmt_v).first():
                    # Create placeholder vehicle if PCN references a vehicle not in contracts
                    temp_v = Vehicle(
                        registration=p_rec.vehicle_registration or p_rec.normalized_registration,
                        normalized_registration=p_rec.normalized_registration,
                        source_sheet=p_rec.source_sheet,
                        source_row=p_rec.source_row,
                    )
                    db.add(temp_v)
                    db.flush()

            if existing_pcn:
                existing_pcn.vehicle_registration = p_rec.vehicle_registration or existing_pcn.vehicle_registration
                existing_pcn.normalized_registration = (
                    p_rec.normalized_registration or existing_pcn.normalized_registration
                )
                existing_pcn.issue_date = p_rec.issue_date or existing_pcn.issue_date
                existing_pcn.fine_amount = (
                    p_rec.fine_amount if p_rec.fine_amount is not None else existing_pcn.fine_amount
                )
                existing_pcn.raw_status = p_rec.raw_status or existing_pcn.raw_status
                existing_pcn.normalized_status = p_rec.normalized_status.value
                existing_pcn.customer_name_raw = p_rec.customer_name_raw or existing_pcn.customer_name_raw
                existing_pcn.matched_customer_id = matched_cust or existing_pcn.matched_customer_id
                existing_pcn.payment_url = p_rec.payment_url or existing_pcn.payment_url
                existing_pcn.has_conflict = p_rec.has_conflict
                existing_pcn.conflict_notes = p_rec.conflict_notes or existing_pcn.conflict_notes
                existing_pcn.updated_at = utc_now()
            else:
                new_pcn = PCN(
                    ticket_number=p_rec.ticket_number,
                    raw_ticket_number=p_rec.raw_ticket_number,
                    vehicle_registration=p_rec.vehicle_registration,
                    normalized_registration=p_rec.normalized_registration,
                    issue_date=p_rec.issue_date,
                    fine_amount=p_rec.fine_amount,
                    raw_status=p_rec.raw_status,
                    normalized_status=p_rec.normalized_status.value,
                    customer_name_raw=p_rec.customer_name_raw,
                    matched_customer_id=matched_cust,
                    payment_url=p_rec.payment_url,
                    source_sheet=p_rec.source_sheet,
                    source_row=p_rec.source_row,
                    has_conflict=p_rec.has_conflict,
                    conflict_notes=p_rec.conflict_notes,
                )
                db.add(new_pcn)

        # 2.5 Record Data Quality Issues
        for issue in clean_result.issues:
            issue_record = DataQualityIssueRecord(
                import_run_id=import_run.id,
                category=issue.category.value,
                issue_type=issue.issue_type,
                severity=issue.severity.value,
                record_identifier=issue.record_identifier,
                source_sheet=issue.source_sheet,
                source_row=issue.source_row,
                field_name=issue.field_name,
                raw_value=issue.raw_value,
                description=issue.description,
            )
            db.add(issue_record)

        # Update import run metrics
        import_run.status = "success"
        import_run.completed_at = utc_now()
        import_run.customers_count = len(clean_result.customers)
        import_run.contracts_count = len(clean_result.contracts)
        import_run.vehicles_count = len(clean_result.vehicles)
        import_run.pcns_count = len(clean_result.pcns)
        import_run.issues_count = len(clean_result.issues)

        # Commit entire atomic transaction
        db.commit()
        db.refresh(import_run)
        return import_run

    except Exception as exc:
        db.rollback()
        # Log failure in import_run
        import_run.status = "failed"
        import_run.completed_at = utc_now()
        import_run.error_message = str(exc)
        db.add(import_run)
        db.commit()
        raise exc
