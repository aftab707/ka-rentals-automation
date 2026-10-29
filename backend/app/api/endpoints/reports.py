"""Operational Report Preview Endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.api.endpoints.dashboard import get_dashboard_summary
from backend.app.db.session import get_db
from backend.app.models.entities import Contract, DataQualityIssueRecord, PCN
from backend.app.schemas.api import (
    ContractResponse,
    DataQualityIssueResponse,
    PCNResponse,
    ReportPreviewResponse,
)

router = APIRouter()


@router.post("/reports/preview", response_model=ReportPreviewResponse)
def preview_operational_report(db: Session = Depends(get_db)):
    """Generates an operational review preview of urgent PCNs, conflicts, and contract risks."""
    summary = get_dashboard_summary(db)

    # 1. Urgent PCNs (unpaid or action needed)
    urgent_stmt = (
        select(PCN)
        .where(PCN.normalized_status.in_(["unpaid", "action_needed"]))
        .order_by(desc(PCN.fine_amount))
        .limit(50)
    )
    urgent_pcns = [PCNResponse.model_validate(p) for p in db.scalars(urgent_stmt).all()]

    # 2. Conflicting PCNs
    conflict_stmt = (
        select(PCN)
        .where((PCN.has_conflict.is_(True)) | (PCN.normalized_status == "conflict"))
        .order_by(desc(PCN.id))
    )
    conflicts = [PCNResponse.model_validate(p) for p in db.scalars(conflict_stmt).all()]

    # 3. Contracts Requiring Action
    contract_stmt = (
        select(Contract)
        .where(Contract.normalized_status.in_(["not_signed", "no_contract", "unknown"]))
        .order_by(Contract.id)
    )
    contracts_action = [ContractResponse.model_validate(c) for c in db.scalars(contract_stmt).all()]

    # 4. Critical Data Quality Issues (scoped to latest import run)
    issues_stmt = select(DataQualityIssueRecord).where(DataQualityIssueRecord.severity == "critical")
    if summary.latest_import:
        issues_stmt = issues_stmt.where(DataQualityIssueRecord.import_run_id == summary.latest_import.id)
    issues_stmt = issues_stmt.order_by(desc(DataQualityIssueRecord.id))
    critical_issues = [DataQualityIssueResponse.model_validate(i) for i in db.scalars(issues_stmt).all()]

    return ReportPreviewResponse(
        generated_at=datetime.now(timezone.utc),
        summary=summary,
        urgent_pcns=urgent_pcns,
        conflicts=conflicts,
        contracts_requiring_action=contracts_action,
        critical_issues=critical_issues,
    )
