"""Contracts, Vehicles, Direct Hire Onboarding, and DocuSign endpoints."""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Contract, Customer, Vehicle
from backend.app.schemas.api import (
    ContractResponse,
    DocuSignActionResponse,
    NewHireRequest,
    PaginatedResponse,
    SendDocuSignRequest,
    VehicleResponse,
)
from backend.app.services.cleaner import normalize_registration
from backend.app.services.docusign_service import (
    get_envelope_status,
    process_docusign_webhook_event,
    send_contract_envelope,
)

router = APIRouter()


@router.get("/contracts", response_model=PaginatedResponse[ContractResponse])
def get_contracts(
    status: Optional[str] = Query(None, description="Filter by status (signed, not_signed, no_contract)"),
    search: Optional[str] = Query(None, description="Search vehicle registration or driver name"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieves paginated list of fleet rental contracts."""
    query = select(Contract)

    if status:
        query = query.where(Contract.normalized_status == status.strip().lower())

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                Contract.vehicle_registration.ilike(s),
                Contract.normalized_registration.ilike(s),
                Contract.customer_name_raw.ilike(s),
                Contract.vehicle_model.ilike(s),
            )
        )

    total_count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    pages = math.ceil(total_count / size) if total_count > 0 else 0

    offset = (page - 1) * size
    query = query.order_by(Contract.id.desc()).offset(offset).limit(size)
    items = db.scalars(query).all()

    return PaginatedResponse[ContractResponse](
        items=[ContractResponse.model_validate(c) for c in items],
        total=total_count,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def get_single_contract(contract_id: int, db: Session = Depends(get_db)):
    """Retrieves a single contract by ID."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract #{contract_id} not found.")
    return ContractResponse.model_validate(contract)


@router.post("/contracts", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_new_hire_agreement(payload: NewHireRequest, db: Session = Depends(get_db)):
    """Onboards a new driver and creates a hire agreement directly without Excel.

    Optionally dispatches DocuSign digital agreement immediately.
    """
    raw_reg, norm_reg = normalize_registration(payload.vehicle_registration)
    if not norm_reg:
        raise HTTPException(status_code=400, detail="Invalid UK vehicle registration number.")

    # 1. Find or create Vehicle
    veh_stmt = select(Vehicle).where(Vehicle.normalized_registration == norm_reg)
    vehicle = db.scalars(veh_stmt).first()
    if not vehicle:
        vehicle = Vehicle(
            registration=raw_reg or payload.vehicle_registration,
            normalized_registration=norm_reg,
            make_model=payload.vehicle_model,
            assigned_driver=payload.customer_name,
            active_contract_status="not_signed",
            source_sheet="Direct Dashboard",
            source_row=0,
        )
        db.add(vehicle)
        db.flush()
    else:
        vehicle.assigned_driver = payload.customer_name

    # 2. Find or create Customer
    cust_stmt = select(Customer).where(
        or_(
            Customer.email == payload.customer_email.strip().lower(),
            Customer.full_name.ilike(payload.customer_name.strip()),
        )
    )
    customer = db.scalars(cust_stmt).first()
    if not customer:
        customer = Customer(
            full_name=payload.customer_name.strip(),
            email=payload.customer_email.strip().lower(),
            phone=payload.customer_phone.strip() if payload.customer_phone else None,
            driving_license=payload.customer_license.strip() if payload.customer_license else None,
            source_sheet="Direct Dashboard",
            source_row=0,
        )
        db.add(customer)
        db.flush()
    else:
        # Update contact info if provided
        if payload.customer_phone:
            customer.phone = payload.customer_phone.strip()
        if payload.customer_license:
            customer.driving_license = payload.customer_license.strip()

    # 3. Create Contract
    contract = Contract(
        vehicle_registration=vehicle.registration,
        normalized_registration=norm_reg,
        customer_name_raw=payload.customer_name.strip(),
        matched_customer_id=customer.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        rate=payload.rate,
        vehicle_model=payload.vehicle_model or vehicle.make_model,
        hire_duration=payload.hire_duration,
        raw_status="not signed",
        normalized_status="not_signed",
        source_sheet="Direct Dashboard",
        source_row=0,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    # 4. Optional Immediate DocuSign Dispatch
    if payload.send_docusign:
        try:
            send_contract_envelope(
                contract.id,
                db,
                recipient_email_override=payload.customer_email,
                recipient_name_override=payload.customer_name,
            )
            db.refresh(contract)
        except Exception as e:
            # We preserve the created contract even if external DocuSign API fails
            contract.docusign_status = f"error: {str(e)[:100]}"
            db.commit()
            db.refresh(contract)

    return ContractResponse.model_validate(contract)


@router.post("/contracts/{contract_id}/send-docusign", response_model=DocuSignActionResponse)
def dispatch_docusign_agreement(
    contract_id: int,
    payload: SendDocuSignRequest = SendDocuSignRequest(),
    db: Session = Depends(get_db),
):
    """Sends a DocuSign rental agreement envelope for an existing contract."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract #{contract_id} not found.")

    try:
        result = send_contract_envelope(
            contract_id=contract_id,
            db=db,
            recipient_email_override=payload.signer_email,
            recipient_name_override=payload.signer_name,
        )
        return DocuSignActionResponse(
            success=True,
            envelope_id=result["envelope_id"],
            status=result["status"],
            message=f"DocuSign agreement dispatched successfully to {result['recipient_email']}.",
            contract_id=contract_id,
            recipient_email=result["recipient_email"],
            sent_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DocuSign dispatch error: {str(e)}")


@router.get("/contracts/{contract_id}/docusign-status", response_model=DocuSignActionResponse)
def check_docusign_status(contract_id: int, db: Session = Depends(get_db)):
    """Fetches real-time signature status from DocuSign and updates contract in database."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract #{contract_id} not found.")

    if not contract.docusign_envelope_id:
        return DocuSignActionResponse(
            success=False,
            status="not_sent",
            message="No DocuSign envelope has been dispatched for this contract yet.",
            contract_id=contract_id,
            sent_at=datetime.now(timezone.utc),
        )

    try:
        env_data = get_envelope_status(contract.docusign_envelope_id)
        current_status = env_data.get("status", "unknown")
        contract.docusign_status = current_status

        if current_status == "completed":
            contract.normalized_status = "signed"
            contract.raw_status = "Signed via DocuSign"
            contract.signed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(contract)

        return DocuSignActionResponse(
            success=True,
            envelope_id=contract.docusign_envelope_id,
            status=current_status,
            message=f"DocuSign envelope status is '{current_status}'.",
            contract_id=contract_id,
            sent_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check DocuSign status: {str(e)}")


@router.post("/webhooks/docusign")
def docusign_webhook_listener(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Listens for DocuSign Connect webhook events and automatically completes signed agreements."""
    res = process_docusign_webhook_event(payload, db)
    return res


@router.get("/vehicles", response_model=List[VehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    """Retrieves all fleet vehicles with mileage and contract status."""
    stmt = select(Vehicle).order_by(Vehicle.normalized_registration)
    vehicles = db.scalars(stmt).all()
    return [VehicleResponse.model_validate(v) for v in vehicles]
