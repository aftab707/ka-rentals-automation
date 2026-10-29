"""PCN listing and filtering endpoints."""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import PCN
from backend.app.schemas.api import PaginatedResponse, PCNResponse

router = APIRouter()


@router.get("/pcns", response_model=PaginatedResponse[PCNResponse])
def get_pcns(
    status: Optional[str] = Query(None, description="Filter by normalized status (e.g. unpaid, action_needed, conflict, paid)"),
    registration: Optional[str] = Query(None, description="Filter by vehicle registration"),
    has_conflict: Optional[bool] = Query(None, description="Filter only conflicting tickets"),
    search: Optional[str] = Query(None, description="Search ticket number, reg, or driver name"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieves paginated list of PCN records with status, registration, and conflict filters."""
    query = select(PCN)

    if status:
        query = query.where(PCN.normalized_status == status.strip().lower())

    if registration:
        clean_reg = registration.replace(" ", "").upper()
        query = query.where(PCN.normalized_registration == clean_reg)

    if has_conflict is not None:
        query = query.where(PCN.has_conflict == has_conflict)

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                PCN.ticket_number.ilike(s),
                PCN.raw_ticket_number.ilike(s),
                PCN.normalized_registration.ilike(s),
                PCN.vehicle_registration.ilike(s),
                PCN.customer_name_raw.ilike(s),
            )
        )

    # Count total
    total_count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    pages = math.ceil(total_count / size) if total_count > 0 else 0

    # Paginated results
    offset = (page - 1) * size
    query = query.order_by(desc(PCN.has_conflict), desc(PCN.id)).offset(offset).limit(size)
    items = db.scalars(query).all()

    return PaginatedResponse[PCNResponse](
        items=[PCNResponse.model_validate(p) for p in items],
        total=total_count,
        page=page,
        size=size,
        pages=pages,
    )
