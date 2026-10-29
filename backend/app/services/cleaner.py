"""Data cleaning, normalization, and canonical transformation service.

Provides deterministic cleaning functions for vehicle registrations, dates,
currency values, PCN statuses, contract statuses, and duplicate conflict resolution.
"""

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from backend.app.schemas.canonical import (
    ContractRecord,
    ContractStatus,
    CustomerRecord,
    DataQualityIssue,
    IssueCategory,
    IssueSeverity,
    PCNRecord,
    PCNStatus,
    VehicleRecord,
)

# Known placeholder strings used in manual spreadsheets for invalid/missing dates
INVALID_DATE_MARKERS = {
    "-----------------------",
    "----------------------",
    "-----------------",
    "00/00/00",
    "00/00/0000",
    "0",
    "-",
    "n/a",
    "na",
    "none",
    "null",
}


def normalize_registration(val: Any) -> Tuple[Optional[str], Optional[str]]:
    """Clean and normalize UK vehicle registration.

    Returns:
        (raw_value, normalized_uppercase_alphanumeric)
    """
    if val is None or pd.isna(val):
        return None, None
    raw = str(val)
    if not raw.strip() or raw.strip().lower() in {"nan", "none", "null", "-"}:
        return None, None
    # Remove all spaces and special punctuation for normalized representation
    normalized = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    return raw, normalized if normalized else None


def normalize_ticket_number(val: Any) -> Tuple[Optional[str], Optional[str]]:
    """Normalize PCN / Parking infringement ticket reference.

    Returns:
        (raw_value, normalized_ticket_string)
    """
    if val is None or pd.isna(val):
        return None, None
    raw = str(val).strip()
    if not raw or raw.lower() in {"nan", "none", "null", "-"}:
        return None, None
    # If Excel parsed an integer/float ticket number, e.g. 1646108152.0
    if raw.endswith(".0") and raw[:-2].isdigit():
        raw = raw[:-2]
    # Retain standard ticket characters (alphanumeric, forward slashes, hyphens)
    normalized = raw.strip().upper()
    return raw, normalized


def normalize_pcn_status(val: Any) -> Tuple[Optional[str], PCNStatus]:
    """Map raw PCN status string to canonical PCNStatus enum."""
    if val is None or pd.isna(val):
        return None, PCNStatus.UNKNOWN

    raw = str(val).strip()
    norm = raw.lower()

    if not norm or norm in {"nan", "none", "null", "-"}:
        return raw, PCNStatus.UNKNOWN

    if "payed" in norm or "paid" in norm:
        if "not" in norm or "unpaid" in norm:
            return raw, PCNStatus.UNPAID
        return raw, PCNStatus.PAID

    if "awaiting payment" in norm:
        return raw, PCNStatus.UNPAID

    if "action needed" in norm:
        return raw, PCNStatus.ACTION_NEEDED

    if "cant get info" in norm or "cannot get info" in norm or "not assignable" in norm:
        return raw, PCNStatus.NEEDS_REVIEW

    return raw, PCNStatus.NEEDS_REVIEW


def normalize_contract_status(val: Any) -> Tuple[Optional[str], ContractStatus]:
    """Map raw contract status string to canonical ContractStatus enum."""
    if val is None or pd.isna(val):
        return None, ContractStatus.UNKNOWN

    raw = str(val).strip()
    norm = raw.lower()

    if not norm or norm in {"nan", "none", "null", "-"}:
        return raw, ContractStatus.UNKNOWN

    if norm == "signed":
        return raw, ContractStatus.SIGNED
    if "not signed" in norm or "unsigned" in norm:
        return raw, ContractStatus.NOT_SIGNED
    if "no contract" in norm:
        return raw, ContractStatus.NO_CONTRACT

    return raw, ContractStatus.UNKNOWN


def parse_currency_amount(val: Any) -> Optional[float]:
    """Extract clean float amount from numeric or formatted currency strings."""
    if val is None or pd.isna(val):
        return None

    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s or s.lower() in {"nan", "none", "null", "-"}:
        return None

    # Remove currency symbols and comma separators
    cleaned = re.sub(r"[£$€,\s]", "", s)

    # Match the first floating point or integer number
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def parse_date_safe(
    val: Any,
    source_sheet: str,
    source_row: int,
    field_name: str,
    record_identifier: Optional[str],
    issues: List[DataQualityIssue],
) -> Optional[date]:
    """Safely parse dates, intercepting invalid placeholder markers.

    Emits a DataQualityIssue when encountering invalid or corrupt date values.
    """
    if val is None or pd.isna(val):
        return None

    # If it is already a datetime/Timestamp
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.date()
    if isinstance(val, date):
        return val

    s = str(val).strip()
    if not s:
        return None

    # Check for manual spreadsheet placeholder markers
    if s.lower() in INVALID_DATE_MARKERS:
        issues.append(
            DataQualityIssue(
                category=IssueCategory.CONTRACT if "contract" in source_sheet.lower() else IssueCategory.PCN,
                issue_type="INVALID_DATE_FORMAT",
                severity=IssueSeverity.WARNING,
                record_identifier=record_identifier,
                source_sheet=source_sheet,
                source_row=source_row,
                field_name=field_name,
                raw_value=s,
                description=f"Invalid date placeholder '{s}' found in {field_name}. Converted to null.",
            )
        )
        return None

    # Attempt to parse common UK and ISO formats
    # Common formats: 'YYYY-MM-DD', 'DD/MM/YYYY', 'DD / MM / YYYY', 'YYYY-MM-DD HH:MM:SS'
    clean_date_str = re.sub(r"\s+", " ", s).strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d / %m / %Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d / %m / %y",
    ):
        try:
            return datetime.strptime(clean_date_str, fmt).date()
        except ValueError:
            continue

    # If parsing failed, flag an issue
    issues.append(
        DataQualityIssue(
            category=IssueCategory.CONTRACT if "contract" in source_sheet.lower() else IssueCategory.PCN,
            issue_type="CORRUPT_DATE_VALUE",
            severity=IssueSeverity.WARNING,
            record_identifier=record_identifier,
            source_sheet=source_sheet,
            source_row=source_row,
            field_name=field_name,
            raw_value=s,
            description=f"Unparseable date value '{s}' in {field_name}.",
        )
    )
    return None


def clean_customer_row(
    sr: Any,
    name: Any,
    email: Any,
    phone: Any,
    license_num: Any,
    source_row: int,
    issues: List[DataQualityIssue],
) -> Optional[CustomerRecord]:
    """Clean a row from 'Customer details'."""
    raw_name = str(name).strip() if name and not pd.isna(name) else None
    if not raw_name or raw_name.lower() in {"nan", "none"}:
        issues.append(
            DataQualityIssue(
                category=IssueCategory.CUSTOMER,
                issue_type="MISSING_CUSTOMER_NAME",
                severity=IssueSeverity.CRITICAL,
                record_identifier=str(sr),
                source_sheet="Customer details",
                source_row=source_row,
                field_name="Name",
                raw_value=str(name),
                description="Customer record is missing mandatory Name.",
            )
        )
        return None

    # Clean Email
    raw_email = str(email).strip() if email and not pd.isna(email) else None
    clean_email = None
    if raw_email and raw_email.lower() not in {"nan", "none"}:
        if "@" in raw_email:
            clean_email = raw_email.lower()
        else:
            issues.append(
                DataQualityIssue(
                    category=IssueCategory.CUSTOMER,
                    issue_type="INVALID_EMAIL_FORMAT",
                    severity=IssueSeverity.WARNING,
                    record_identifier=raw_name,
                    source_sheet="Customer details",
                    source_row=source_row,
                    field_name="Email",
                    raw_value=raw_email,
                    description=f"Email '{raw_email}' lacks valid syntax.",
                )
            )
    else:
        issues.append(
            DataQualityIssue(
                category=IssueCategory.CUSTOMER,
                issue_type="MISSING_CUSTOMER_EMAIL",
                severity=IssueSeverity.INFO,
                record_identifier=raw_name,
                source_sheet="Customer details",
                source_row=source_row,
                field_name="Email",
                raw_value=None,
                description=f"Customer '{raw_name}' has no registered email.",
            )
        )

    # Clean Phone
    raw_phone = None
    if phone and not pd.isna(phone):
        p_str = str(phone).strip()
        if p_str.endswith(".0"):
            p_str = p_str[:-2]
        if p_str.lower() not in {"nan", "none"}:
            raw_phone = p_str
    if not raw_phone:
        issues.append(
            DataQualityIssue(
                category=IssueCategory.CUSTOMER,
                issue_type="MISSING_CUSTOMER_PHONE",
                severity=IssueSeverity.INFO,
                record_identifier=raw_name,
                source_sheet="Customer details",
                source_row=source_row,
                field_name="Phone number",
                raw_value=None,
                description=f"Customer '{raw_name}' has no phone number.",
            )
        )

    # Clean Driving License
    raw_license = str(license_num).strip() if license_num and not pd.isna(license_num) else None
    if raw_license and raw_license.lower() in {"nan", "none"}:
        raw_license = None
    if not raw_license:
        issues.append(
            DataQualityIssue(
                category=IssueCategory.CUSTOMER,
                issue_type="MISSING_DRIVING_LICENSE",
                severity=IssueSeverity.INFO,
                record_identifier=raw_name,
                source_sheet="Customer details",
                source_row=source_row,
                field_name="Driving License Number",
                raw_value=None,
                description=f"Customer '{raw_name}' has no driving license number recorded.",
            )
        )

    try:
        cust_id = int(sr)
    except (ValueError, TypeError):
        cust_id = source_row

    return CustomerRecord(
        customer_id=cust_id,
        full_name=raw_name,
        email=clean_email,
        phone=raw_phone,
        driving_license=raw_license,
        source_sheet="Customer details",
        source_row=source_row,
    )


def resolve_pcn_duplicates(
    pcn_records: List[PCNRecord],
    issues: List[DataQualityIssue],
) -> List[PCNRecord]:
    """Harmonize PCN records across multiple sheets.

    - Resolves duplicates by ticket_number.
    - Preserves all occurrences and source metadata.
    - Detects status conflicts (e.g., PAID vs UNPAID) and flags CONFLICT status.
    - Merges missing complementary fields (fine_amount, registration, issue_date).
    """
    by_ticket: Dict[str, List[PCNRecord]] = {}
    for pcn in pcn_records:
        by_ticket.setdefault(pcn.ticket_number, []).append(pcn)

    harmonized: List[PCNRecord] = []

    for ticket_num, occurrences in by_ticket.items():
        if len(occurrences) == 1:
            harmonized.append(occurrences[0])
            continue

        # Multiple occurrences across sheets
        sheets = [f"{o.source_sheet} (row {o.source_row})" for o in occurrences]
        statuses = {o.normalized_status for o in occurrences if o.normalized_status != PCNStatus.UNKNOWN}

        # Check for conflict: e.g. PAID and UNPAID
        has_conflict = False
        conflict_notes = None
        if PCNStatus.PAID in statuses and (
            PCNStatus.UNPAID in statuses or PCNStatus.ACTION_NEEDED in statuses
        ):
            has_conflict = True
            conflict_notes = f"Conflict detected across sheets: {', '.join(sheets)}. Distinct statuses: {[s.value for s in statuses]}"
            issues.append(
                DataQualityIssue(
                    category=IssueCategory.PCN,
                    issue_type="STATUS_CONFLICT",
                    severity=IssueSeverity.CRITICAL,
                    record_identifier=ticket_num,
                    source_sheet=occurrences[0].source_sheet,
                    source_row=occurrences[0].source_row,
                    field_name="Status",
                    raw_value=str([o.raw_status for o in occurrences]),
                    description=conflict_notes,
                )
            )
        else:
            issues.append(
                DataQualityIssue(
                    category=IssueCategory.PCN,
                    issue_type="DUPLICATE_TICKET_ACROSS_SHEETS",
                    severity=IssueSeverity.INFO,
                    record_identifier=ticket_num,
                    source_sheet=occurrences[0].source_sheet,
                    source_row=occurrences[0].source_row,
                    field_name="ticket_number",
                    raw_value=ticket_num,
                    description=f"Ticket {ticket_num} appears in {len(occurrences)} sheets: {', '.join(sheets)}.",
                )
            )

        # Merge fields intelligently
        base = occurrences[0]
        merged_reg = base.vehicle_registration
        merged_norm_reg = base.normalized_registration
        merged_date = base.issue_date
        merged_fine = base.fine_amount
        merged_name = base.customer_name_raw
        merged_url = base.payment_url

        # Select most specific status:
        if has_conflict:
            final_status = PCNStatus.CONFLICT
        elif PCNStatus.ACTION_NEEDED in statuses:
            final_status = PCNStatus.ACTION_NEEDED
        elif PCNStatus.UNPAID in statuses:
            final_status = PCNStatus.UNPAID
        elif PCNStatus.PAID in statuses:
            final_status = PCNStatus.PAID
        elif PCNStatus.NEEDS_REVIEW in statuses:
            final_status = PCNStatus.NEEDS_REVIEW
        else:
            final_status = PCNStatus.UNKNOWN

        for o in occurrences[1:]:
            if not merged_reg and o.vehicle_registration:
                merged_reg = o.vehicle_registration
                merged_norm_reg = o.normalized_registration
            if not merged_date and o.issue_date:
                merged_date = o.issue_date
            if merged_fine is None and o.fine_amount is not None:
                merged_fine = o.fine_amount
            if not merged_name and o.customer_name_raw:
                merged_name = o.customer_name_raw
            if not merged_url and o.payment_url:
                merged_url = o.payment_url

        harmonized_record = PCNRecord(
            ticket_number=ticket_num,
            raw_ticket_number=base.raw_ticket_number,
            vehicle_registration=merged_reg,
            normalized_registration=merged_norm_reg,
            issue_date=merged_date,
            fine_amount=merged_fine,
            raw_status=" | ".join([f"{o.source_sheet}:{o.raw_status}" for o in occurrences if o.raw_status]),
            normalized_status=final_status,
            customer_name_raw=merged_name,
            payment_url=merged_url,
            source_sheet=base.source_sheet,
            source_row=base.source_row,
            has_conflict=has_conflict,
            conflict_notes=conflict_notes,
        )
        harmonized.append(harmonized_record)

    return harmonized
