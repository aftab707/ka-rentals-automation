"""Data quality issues audit endpoints."""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import DataQualityIssueRecord
from backend.app.schemas.api import DataQualityIssueResponse, PaginatedResponse

router = APIRouter()


@router.get("/data-quality/issues", response_model=PaginatedResponse[DataQualityIssueResponse])
def get_data_quality_issues(
    severity: Optional[str] = Query(None, description="Filter by severity (critical, warning, info)"),
    category: Optional[str] = Query(None, description="Filter by category (pcn, contract, customer, vehicle)"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieves paginated audit log of detected data quality issues."""
    query = select(DataQualityIssueRecord)

    if severity:
        query = query.where(DataQualityIssueRecord.severity == severity.strip().lower())

    if category:
        query = query.where(DataQualityIssueRecord.category == category.strip().lower())

    total_count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    pages = math.ceil(total_count / size) if total_count > 0 else 0

    offset = (page - 1) * size
    query = query.order_by(
        # Order by severity: critical first, then warning, then info
        desc(DataQualityIssueRecord.severity == "critical"),
        desc(DataQualityIssueRecord.severity == "warning"),
        desc(DataQualityIssueRecord.id),
    ).offset(offset).limit(size)
    items = db.scalars(query).all()

    return PaginatedResponse[DataQualityIssueResponse](
        items=[DataQualityIssueResponse.model_validate(i) for i in items],
        total=total_count,
        page=page,
        size=size,
        pages=pages,
    )
