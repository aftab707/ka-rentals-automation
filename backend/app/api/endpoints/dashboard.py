"""Dashboard KPI summary endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.entities import (
    Contract,
    DataQualityIssueRecord,
    ImportRun,
    PCN,
    Vehicle,
)
from backend.app.schemas.api import DashboardSummary, ImportRunResponse

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Computes operational KPIs for the car rental fleet, contracts, and PCNs."""
    # Vehicles & Contracts
    total_vehicles = db.scalar(select(func.count(Vehicle.id))) or 0
    active_contracts = db.scalar(
        select(func.count(Contract.id)).where(Contract.normalized_status == "signed")
    ) or 0
    unsigned_contracts = db.scalar(
        select(func.count(Contract.id)).where(Contract.normalized_status != "signed")
    ) or 0

    # PCNs
    total_pcns = db.scalar(select(func.count(PCN.id))) or 0
    unpaid_pcns = db.scalar(
        select(func.count(PCN.id)).where(PCN.normalized_status == "unpaid")
    ) or 0
    action_needed_pcns = db.scalar(
        select(func.count(PCN.id)).where(PCN.normalized_status == "action_needed")
    ) or 0
    conflict_pcns = db.scalar(
        select(func.count(PCN.id)).where((PCN.has_conflict.is_(True)) | (PCN.normalized_status == "conflict"))
    ) or 0
    paid_pcns = db.scalar(
        select(func.count(PCN.id)).where(PCN.normalized_status == "paid")
    ) or 0
    needs_review_pcns = db.scalar(
        select(func.count(PCN.id)).where(PCN.normalized_status == "needs_review")
    ) or 0

    # Latest Import
    latest_import_model = db.scalars(select(ImportRun).order_by(desc(ImportRun.id)).limit(1)).first()
    latest_import = ImportRunResponse.model_validate(latest_import_model) if latest_import_model else None

    # Data Quality Issues (scoped to latest import run for accurate snapshot)
    if latest_import_model:
        total_issues = db.scalar(
            select(func.count(DataQualityIssueRecord.id)).where(
                DataQualityIssueRecord.import_run_id == latest_import_model.id
            )
        ) or 0
        critical_issues = db.scalar(
            select(func.count(DataQualityIssueRecord.id)).where(
                DataQualityIssueRecord.import_run_id == latest_import_model.id,
                DataQualityIssueRecord.severity == "critical",
            )
        ) or 0
        warning_issues = db.scalar(
            select(func.count(DataQualityIssueRecord.id)).where(
                DataQualityIssueRecord.import_run_id == latest_import_model.id,
                DataQualityIssueRecord.severity == "warning",
            )
        ) or 0
    else:
        total_issues = db.scalar(select(func.count(DataQualityIssueRecord.id))) or 0
        critical_issues = db.scalar(
            select(func.count(DataQualityIssueRecord.id)).where(DataQualityIssueRecord.severity == "critical")
        ) or 0
        warning_issues = db.scalar(
            select(func.count(DataQualityIssueRecord.id)).where(DataQualityIssueRecord.severity == "warning")
        ) or 0

    return DashboardSummary(
        total_vehicles=total_vehicles,
        active_contracts=active_contracts,
        unsigned_contracts=unsigned_contracts,
        total_pcns=total_pcns,
        unpaid_pcns=unpaid_pcns,
        action_needed_pcns=action_needed_pcns,
        conflict_pcns=conflict_pcns,
        paid_pcns=paid_pcns,
        needs_review_pcns=needs_review_pcns,
        total_issues=total_issues,
        critical_issues=critical_issues,
        warning_issues=warning_issues,
        latest_import=latest_import,
    )
