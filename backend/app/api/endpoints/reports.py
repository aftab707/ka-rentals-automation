"""Operational Daily Report and Mock Email Preview Endpoints."""

from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
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
from backend.app.schemas.report import (
    MockEmailRequest,
    MockEmailResponse,
    OperationalReport,
)
from backend.app.services.reporter import (
    generate_daily_operational_report,
    render_html_email_report,
)

logger = logging.getLogger(__name__)

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


@router.get("/reports/daily/json", response_model=OperationalReport)
def get_daily_operational_report_endpoint(db: Session = Depends(get_db)):
    """Returns the structured daily operational report with categorized action items."""
    return generate_daily_operational_report(db)


@router.get("/reports/daily/html", response_class=HTMLResponse)
def get_daily_operational_report_html_endpoint(db: Session = Depends(get_db)):
    """Renders the HTML email preview of the daily operational report."""
    report = generate_daily_operational_report(db)
    return HTMLResponse(content=render_html_email_report(report), status_code=200)


@router.post("/reports/email/mock-send", response_model=MockEmailResponse)
def send_mock_email_endpoint(
    payload: MockEmailRequest = MockEmailRequest(),
    db: Session = Depends(get_db),
):
    """Mocks sending a daily operational report email in a safe sandbox mode.

    No live external SMTP or API call is made. Trace record is returned.
    """
    report = generate_daily_operational_report(db)
    subject = (
        payload.subject_override
        or f"KA Rentals Daily Operational Review [{report.report_id}] - {datetime.now(timezone.utc).strftime('%d %b %Y')}"
    )

    snippet = (
        f"Operational Report {report.report_id}: {report.total_open_pcns} open PCNs "
        f"(£{report.total_unpaid_amount:.2f}), {report.status_conflicts_count} status conflicts, "
        f"{report.unsigned_contracts} unsigned contracts. Sandbox preview delivered to {payload.recipient_email}."
    )

    logger.info(
        "MOCK EMAIL DISPATCHED: to=%s, subject=%s, report_id=%s",
        payload.recipient_email,
        subject,
        report.report_id,
    )

    return MockEmailResponse(
        status="MOCK_SENT_SUCCESS",
        recipient=payload.recipient_email,
        subject=subject,
        sent_at=datetime.now(timezone.utc),
        mock_mode=True,
        message_preview_snippet=snippet,
    )
