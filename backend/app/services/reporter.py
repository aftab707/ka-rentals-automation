"""Operational Daily Report Generator and Email Template Service.

Categorizes fleet operations issues (conflicts, unpaid fines, unsigned contracts,
and data quality issues), attaches source traceability (sheet & row), formulates
recommended staff actions without inventing overdue deadlines, and renders
clean HTML/Markdown email previews in safe mock mode.
"""

from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    Contract,
    Customer,
    DataQualityIssueRecord,
    ImportRun,
    PCN,
    Vehicle,
)
from backend.app.schemas.report import ActionItem, OperationalReport


def generate_daily_operational_report(db: Session) -> OperationalReport:
    """Compiles the full operational review report from persistent SQLite DB."""
    # 1. High-level Metrics
    total_vehicles = db.scalar(select(func.count(Vehicle.id))) or 0
    signed_contracts = db.scalar(
        select(func.count(Contract.id)).where(Contract.normalized_status == "signed")
    ) or 0
    unsigned_contracts = db.scalar(
        select(func.count(Contract.id)).where(Contract.normalized_status != "signed")
    ) or 0

    open_pcns_stmt = select(PCN).where(
        PCN.normalized_status.in_(["unpaid", "action_needed", "conflict", "needs_review"])
    )
    all_open_pcns = db.scalars(open_pcns_stmt).all()
    total_open_pcns = len(all_open_pcns)
    total_unpaid_amount = sum(p.fine_amount for p in all_open_pcns if p.fine_amount is not None)

    # 2. Category 1: Status Conflicts (Priority 1 Critical)
    conflict_pcns_list: List[ActionItem] = []
    conflict_db_records = [p for p in all_open_pcns if p.has_conflict or p.normalized_status == "conflict"]
    for p in conflict_db_records:
        conflict_pcns_list.append(
            ActionItem(
                category="PCN",
                subcategory="STATUS_CONFLICT",
                identifier=p.ticket_number,
                description=p.conflict_notes or f"Ticket {p.ticket_number} has contradictory statuses across sheets.",
                amount=p.fine_amount,
                status=p.normalized_status,
                source_sheet=p.source_sheet,
                source_row=p.source_row,
                recommended_action="Do not double-pay or mark unpaid. Check parking authority portal to confirm legal payment state.",
            )
        )

    # 3. Category 2: Immediate Action Needed PCNs
    action_needed_list: List[ActionItem] = []
    action_records = [p for p in all_open_pcns if p.normalized_status == "action_needed" and not p.has_conflict]
    for p in action_records:
        action_needed_list.append(
            ActionItem(
                category="PCN",
                subcategory="ACTION_NEEDED",
                identifier=p.ticket_number,
                description=f"Actionable fine recorded for vehicle {p.normalized_registration or 'Unknown'}.",
                amount=p.fine_amount,
                status=p.normalized_status,
                source_sheet=p.source_sheet,
                source_row=p.source_row,
                recommended_action="Settle fine on portal or transfer liability to driver in accordance with contract terms.",
            )
        )

    # 4. Category 3: Unpaid PCNs
    unpaid_list: List[ActionItem] = []
    unpaid_records = [p for p in all_open_pcns if p.normalized_status == "unpaid" and not p.has_conflict]
    for p in unpaid_records:
        unpaid_list.append(
            ActionItem(
                category="PCN",
                subcategory="UNPAID_FINE",
                identifier=p.ticket_number,
                description=f"Unpaid parking violation on vehicle {p.normalized_registration or 'Unknown'}.",
                amount=p.fine_amount,
                status=p.normalized_status,
                source_sheet=p.source_sheet,
                source_row=p.source_row,
                recommended_action="Review driver agreement and process recharge or payment settlement.",
            )
        )

    # 5. Category 4: Needs Review / Ambiguous PCNs
    needs_review_list: List[ActionItem] = []
    review_records = [p for p in all_open_pcns if p.normalized_status == "needs_review" and not p.has_conflict]
    for p in review_records:
        needs_review_list.append(
            ActionItem(
                category="PCN",
                subcategory="AMBIGUOUS_STATUS",
                identifier=p.ticket_number,
                description=f"Incomplete info or fine not assignable (Raw: '{p.raw_status or ''}').",
                amount=p.fine_amount,
                status=p.normalized_status,
                source_sheet=p.source_sheet,
                source_row=p.source_row,
                recommended_action="Request ticket clarification from issuing authority or driver.",
            )
        )

    # 6. Category 5: Contracts Requiring Action
    contracts_action_list: List[ActionItem] = []
    contract_stmt = select(Contract).where(
        (Contract.normalized_status != "signed") | (Contract.start_date.is_(None)) | (Contract.end_date.is_(None))
    )
    contracts_to_review = db.scalars(contract_stmt).all()
    for c in contracts_to_review:
        notes = []
        if c.normalized_status != "signed":
            notes.append(f"Agreement is {c.normalized_status.replace('_', ' ')}")
        if c.start_date is None or c.end_date is None:
            notes.append("Start/end dates contain invalid spreadsheet placeholders (e.g. '00/00/00')")

        contracts_action_list.append(
            ActionItem(
                category="CONTRACT",
                subcategory="CONTRACT_RISK",
                identifier=c.normalized_registration,
                description=f"Vehicle {c.normalized_registration} ({c.vehicle_model or 'Model unspecified'}): {'; '.join(notes)}.",
                amount=c.rate,
                status=c.normalized_status,
                source_sheet=c.source_sheet,
                source_row=c.source_row,
                recommended_action="Issue formal hire contract for digital signature and verify valid hire period.",
            )
        )

    # 7. Category 6: Incomplete Customer Profiles (Regulatory/GDPR)
    customer_action_list: List[ActionItem] = []
    cust_stmt = select(Customer).where(
        (Customer.email.is_(None)) | (Customer.phone.is_(None)) | (Customer.driving_license.is_(None))
    )
    incomplete_customers = db.scalars(cust_stmt).all()
    for cust in incomplete_customers:
        missing = []
        if not cust.email:
            missing.append("Email")
        if not cust.phone:
            missing.append("Phone")
        if not cust.driving_license:
            missing.append("Driving License")

        customer_action_list.append(
            ActionItem(
                category="CUSTOMER",
                subcategory="INCOMPLETE_PROFILE",
                identifier=f"Cust #{cust.id}: {cust.full_name}",
                description=f"Driver profile is missing mandatory contact/verification fields: {', '.join(missing)}.",
                status="incomplete",
                source_sheet=cust.source_sheet,
                source_row=cust.source_row,
                recommended_action="Contact customer to complete vehicle hire compliance documentation.",
            )
        )

    report_id = f"REP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    return OperationalReport(
        report_id=report_id,
        generated_at=datetime.now(timezone.utc),
        is_mock_preview=True,
        total_fleet_vehicles=total_vehicles,
        signed_contracts=signed_contracts,
        unsigned_contracts=unsigned_contracts,
        total_open_pcns=total_open_pcns,
        total_unpaid_amount=round(total_unpaid_amount, 2),
        status_conflicts_count=len(conflict_pcns_list),
        conflicting_pcns=conflict_pcns_list,
        action_needed_pcns=action_needed_list,
        unpaid_pcns=unpaid_list,
        needs_review_pcns=needs_review_list,
        contracts_requiring_action=contracts_action_list,
        incomplete_customers=customer_action_list,
    )


def render_html_email_report(report: OperationalReport) -> str:
    """Renders a responsive, clean HTML email template for daily review preview."""
    conflicts_rows = ""
    for item in report.conflicting_pcns:
        conflicts_rows += f"""
        <tr style="background-color: #fef2f2; border-bottom: 1px solid #fee2e2;">
            <td style="padding: 10px 14px; font-weight: bold; color: #991b1b;">{item.identifier}</td>
            <td style="padding: 10px 14px; color: #b91c1c; font-size: 13px;">{item.description}</td>
            <td style="padding: 10px 14px; font-size: 12px; color: #64748b;">{item.source_sheet} (row {item.source_row})</td>
            <td style="padding: 10px 14px; font-size: 12px; font-weight: 500; color: #991b1b;">{item.recommended_action}</td>
        </tr>
        """

    urgent_rows = ""
    for item in report.action_needed_pcns[:10]:
        amount_str = f"£{item.amount:.2f}" if item.amount else "—"
        urgent_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px 14px; font-weight: bold;">{item.identifier}</td>
            <td style="padding: 10px 14px; font-weight: 600; color: #d97706;">{amount_str}</td>
            <td style="padding: 10px 14px; font-size: 13px;">{item.description}</td>
            <td style="padding: 10px 14px; font-size: 12px; color: #64748b;">{item.source_sheet} (row {item.source_row})</td>
            <td style="padding: 10px 14px; font-size: 12px;">{item.recommended_action}</td>
        </tr>
        """

    contracts_rows = ""
    for item in report.contracts_requiring_action:
        contracts_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px 14px; font-weight: bold; font-family: monospace;">{item.identifier}</td>
            <td style="padding: 10px 14px; font-size: 13px;">{item.description}</td>
            <td style="padding: 10px 14px; font-size: 12px; color: #64748b;">{item.source_sheet} (row {item.source_row})</td>
            <td style="padding: 10px 14px; font-size: 12px;">{item.recommended_action}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>KA Rentals - Daily Operational Review Report</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #0f172a;">
    <div style="max-width: 780px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
        
        <!-- Header Banner -->
        <div style="background-color: #0f172a; color: #ffffff; padding: 24px 28px;">
            <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #38bdf8; font-weight: 700;">KA Rentals • Daily Fleet Operations</div>
            <h1 style="margin: 6px 0 0; font-size: 22px; font-weight: 700;">Daily Operational Review Report</h1>
            <div style="margin-top: 6px; font-size: 13px; color: #94a3b8;">
                Report ID: {report.report_id} • Generated: {report.generated_at.strftime('%d %b %Y, %H:%M UTC')}
            </div>
        </div>

        <!-- Safe Mode Notice -->
        <div style="background-color: #eff6ff; border-left: 4px solid #2563eb; padding: 12px 20px; font-size: 13px; color: #1e40af;">
            <strong>MOCK EMAIL PREVIEW:</strong> This report is running in preview mode. No live emails are sent to customers or external parties.
        </div>

        <!-- KPI Metric Summary -->
        <div style="padding: 24px 28px; border-bottom: 1px solid #e2e8f0;">
            <h2 style="font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-top: 0; margin-bottom: 16px;">Executive Operations Summary</h2>
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 140px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px;">
                    <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">Total Fleet</div>
                    <div style="font-size: 24px; font-weight: 700; color: #0f172a; margin-top: 4px;">{report.total_fleet_vehicles}</div>
                    <div style="font-size: 11px; color: #16a34a; margin-top: 2px;">{report.signed_contracts} signed contracts</div>
                </div>
                <div style="flex: 1; min-width: 140px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px;">
                    <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">Open PCNs</div>
                    <div style="font-size: 24px; font-weight: 700; color: #d97706; margin-top: 4px;">{report.total_open_pcns}</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Total: £{report.total_unpaid_amount:.2f}</div>
                </div>
                <div style="flex: 1; min-width: 140px; background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 14px;">
                    <div style="font-size: 11px; font-weight: 600; color: #991b1b; text-transform: uppercase;">Status Conflicts</div>
                    <div style="font-size: 24px; font-weight: 700; color: #dc2626; margin-top: 4px;">{report.status_conflicts_count}</div>
                    <div style="font-size: 11px; color: #991b1b; margin-top: 2px;">Cross-sheet discrepancies</div>
                </div>
                <div style="flex: 1; min-width: 140px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px;">
                    <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">Unsigned Contracts</div>
                    <div style="font-size: 24px; font-weight: 700; color: #475569; margin-top: 4px;">{report.unsigned_contracts}</div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Require signature action</div>
                </div>
            </div>
        </div>

        <!-- Section 1: Critical Conflicts -->
        <div style="padding: 24px 28px; border-bottom: 1px solid #e2e8f0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <h3 style="margin: 0; font-size: 16px; color: #991b1b; font-weight: 700;">🚨 Priority 1: Multi-Sheet Status Conflicts ({len(report.conflicting_pcns)})</h3>
                <span style="font-size: 11px; background-color: #fee2e2; color: #dc2626; padding: 3px 8px; border-radius: 999px; font-weight: 700;">CRITICAL AUDIT</span>
            </div>
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                <thead>
                    <tr style="background-color: #f1f5f9; color: #475569;">
                        <th style="padding: 10px 14px;">Ticket Ref</th>
                        <th style="padding: 10px 14px;">Conflict Note</th>
                        <th style="padding: 10px 14px;">Source Trace</th>
                        <th style="padding: 10px 14px;">Action Required</th>
                    </tr>
                </thead>
                <tbody>
                    {conflicts_rows or '<tr><td colspan="4" style="padding: 16px; text-align: center; color: #64748b;">No conflicting records found.</td></tr>'}
                </tbody>
            </table>
        </div>

        <!-- Section 2: Action Needed PCNs -->
        <div style="padding: 24px 28px; border-bottom: 1px solid #e2e8f0;">
            <h3 style="margin: 0 0 12px; font-size: 16px; color: #0f172a; font-weight: 700;">⚠️ Urgent Action Needed PCNs ({len(report.action_needed_pcns)})</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                <thead>
                    <tr style="background-color: #f1f5f9; color: #475569;">
                        <th style="padding: 10px 14px;">Ticket Ref</th>
                        <th style="padding: 10px 14px;">Fine</th>
                        <th style="padding: 10px 14px;">Description</th>
                        <th style="padding: 10px 14px;">Source Trace</th>
                        <th style="padding: 10px 14px;">Action Required</th>
                    </tr>
                </thead>
                <tbody>
                    {urgent_rows or '<tr><td colspan="5" style="padding: 16px; text-align: center; color: #64748b;">No urgent action needed PCNs found.</td></tr>'}
                </tbody>
            </table>
        </div>

        <!-- Section 3: Unsigned Contracts -->
        <div style="padding: 24px 28px;">
            <h3 style="margin: 0 0 12px; font-size: 16px; color: #0f172a; font-weight: 700;">📄 Fleet Contracts Requiring Action ({len(report.contracts_requiring_action)})</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                <thead>
                    <tr style="background-color: #f1f5f9; color: #475569;">
                        <th style="padding: 10px 14px;">Registration</th>
                        <th style="padding: 10px 14px;">Issue Detail</th>
                        <th style="padding: 10px 14px;">Source Trace</th>
                        <th style="padding: 10px 14px;">Action Required</th>
                    </tr>
                </thead>
                <tbody>
                    {contracts_rows or '<tr><td colspan="4" style="padding: 16px; text-align: center; color: #64748b;">All fleet contracts signed and valid.</td></tr>'}
                </tbody>
            </table>
        </div>

        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 18px 28px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
            KA Rentals Fleet Automation Prototype • Confidential Business Data • Mock Delivery Mode
        </div>
    </div>
</body>
</html>
    """
    return html


def render_markdown_email_report(report: OperationalReport) -> str:
    """Renders plain text / Markdown summary suitable for chat digests or text logs."""
    md = f"""# KA Rentals - Daily Operational Review Report

**Report ID:** {report.report_id}
**Generated At:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Status:** [PROTOTYPE MOCK PREVIEW - NO LIVE EMAIL SENT]

---

## 1. Executive Operations Summary
- **Total Fleet Vehicles:** {report.total_fleet_vehicles} ({report.signed_contracts} signed contracts, {report.unsigned_contracts} unsigned)
- **Total Open PCNs:** {report.total_open_pcns} (Total outstanding fine sum: £{report.total_unpaid_amount:.2f})
- **Status Conflicts:** {report.status_conflicts_count} (Requires immediate audit)
- **Incomplete Compliance Profiles:** {len(report.incomplete_customers)}

---

## 2. Priority 1: Multi-Sheet Status Conflicts ({len(report.conflicting_pcns)})
"""
    for c in report.conflicting_pcns:
        md += f"- **Ticket:** `{c.identifier}` | **Source:** `{c.source_sheet}` (row {c.source_row})\n"
        md += f"  - **Issue:** {c.description}\n"
        md += f"  - **Action:** {c.recommended_action}\n"

    md += f"\n## 3. Urgent Action Needed PCNs ({len(report.action_needed_pcns)})\n"
    for item in report.action_needed_pcns[:10]:
        amount_str = f"£{item.amount:.2f}" if item.amount else "Amount unspecified"
        md += f"- **Ticket:** `{item.identifier}` ({amount_str}) | **Source:** `{item.source_sheet}` (row {item.source_row})\n"
        md += f"  - **Action:** {item.recommended_action}\n"

    md += f"\n## 4. Contracts Requiring Action ({len(report.contracts_requiring_action)})\n"
    for cnt in report.contracts_requiring_action:
        md += f"- **Registration:** `{cnt.identifier}` | **Source:** `{cnt.source_sheet}` (row {cnt.source_row})\n"
        md += f"  - **Issue:** {cnt.description}\n"
        md += f"  - **Action:** {cnt.recommended_action}\n"

    return md
