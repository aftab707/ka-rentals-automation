"""Contracts and Vehicles listing endpoints."""

import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import Contract, Vehicle
from backend.app.schemas.api import ContractResponse, PaginatedResponse, VehicleResponse

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
    query = query.order_by(Contract.id).offset(offset).limit(size)
    items = db.scalars(query).all()

    return PaginatedResponse[ContractResponse](
        items=[ContractResponse.model_validate(c) for c in items],
        total=total_count,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/vehicles", response_model=List[VehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    """Retrieves all fleet vehicles with mileage and contract status."""
    stmt = select(Vehicle).order_by(Vehicle.normalized_registration)
    return db.scalars(stmt).all()
