"""Synthetic unit tests for data cleaning rules and canonical models.

Uses purely synthetic/dummy test data to verify all normalization, parsing,
and conflict detection rules without using any real client data.
"""

from datetime import date
from backend.app.schemas.canonical import (
    IssueCategory,
    IssueSeverity,
    PCNRecord,
    PCNStatus,
    ContractStatus,
)
from backend.app.services.cleaner import (
    clean_customer_row,
    normalize_contract_status,
    normalize_pcn_status,
    normalize_registration,
    normalize_ticket_number,
    parse_currency_amount,
    parse_date_safe,
    resolve_pcn_duplicates,
)


def test_registration_normalization():
    """Verify registration normalization removes whitespace and uppercases."""
    assert normalize_registration("la19 wpd") == ("la19 wpd", "LA19WPD")
    assert normalize_registration("  LP21FYB  ") == ("  LP21FYB  ", "LP21FYB")
    assert normalize_registration("fg72 utx ") == ("fg72 utx ", "FG72UTX")
    assert normalize_registration("bk-69 vvj") == ("bk-69 vvj", "BK69VVJ")
    assert normalize_registration(None) == (None, None)
    assert normalize_registration("") == (None, None)
    assert normalize_registration("nan") == (None, None)


def test_ticket_number_normalization():
    """Verify PCN ticket references are cleaned and stripped of float artifacts."""
    assert normalize_ticket_number("  we6873594a ") == ("we6873594a", "WE6873594A")
    assert normalize_ticket_number("1646108152.0") == ("1646108152", "1646108152")
    assert normalize_ticket_number(None) == (None, None)


def test_pcn_status_normalization():
    """Verify PCN statuses map accurately to canonical taxonomy."""
    # Paid
    assert normalize_pcn_status("Payed")[1] == PCNStatus.PAID
    assert normalize_pcn_status("paid")[1] == PCNStatus.PAID

    # Unpaid
    assert normalize_pcn_status("Not Payed")[1] == PCNStatus.UNPAID
    assert normalize_pcn_status("awaiting payment")[1] == PCNStatus.UNPAID

    # Action needed
    assert normalize_pcn_status("Action Needed")[1] == PCNStatus.ACTION_NEEDED

    # Needs review
    assert normalize_pcn_status("Cant get info ")[1] == PCNStatus.NEEDS_REVIEW
    assert normalize_pcn_status("Fine Not Assignable")[1] == PCNStatus.NEEDS_REVIEW

    # Unknown
    assert normalize_pcn_status(None)[1] == PCNStatus.UNKNOWN
    assert normalize_pcn_status("")[1] == PCNStatus.UNKNOWN


def test_contract_status_normalization():
    """Verify contract statuses map accurately."""
    assert normalize_contract_status("Signed")[1] == ContractStatus.SIGNED
    assert normalize_contract_status("Not signed")[1] == ContractStatus.NOT_SIGNED
    assert normalize_contract_status("No Contract")[1] == ContractStatus.NO_CONTRACT
    assert normalize_contract_status(None)[1] == ContractStatus.UNKNOWN


def test_currency_amount_parsing():
    """Verify parsing of clean and text-formatted currency strings."""
    assert parse_currency_amount(160) == 160.0
    assert parse_currency_amount("160.0") == 160.0
    assert parse_currency_amount("£1,300 PM") == 1300.0
    assert parse_currency_amount("£180 per week") == 180.0
    assert parse_currency_amount("£500pm") == 500.0
    assert parse_currency_amount("670") == 670.0
    assert parse_currency_amount(None) is None
    assert parse_currency_amount("invalid") is None


def test_placeholder_date_interception():
    """Verify dummy placeholder strings are converted to None and emit DataQualityIssue."""
    issues = []
    parsed = parse_date_safe(
        val="-----------------------",
        source_sheet="Test Contracts",
        source_row=5,
        field_name="Start date",
        record_identifier="TESTREG",
        issues=issues,
    )
    assert parsed is None
    assert len(issues) == 1
    assert issues[0].issue_type == "INVALID_DATE_FORMAT"
    assert issues[0].severity == IssueSeverity.WARNING
    assert issues[0].field_name == "Start date"

    # Also test '00/00/00'
    parsed2 = parse_date_safe(
        val="00/00/00",
        source_sheet="Test Contracts",
        source_row=6,
        field_name="End date",
        record_identifier="TESTREG",
        issues=issues,
    )
    assert parsed2 is None
    assert len(issues) == 2


def test_valid_date_parsing():
    """Verify standard ISO and UK date formats are parsed into Python date objects."""
    issues = []
    d1 = parse_date_safe("2026-06-24 00:00:00", "Sheet", 2, "date", "ID", issues)
    assert d1 == date(2026, 6, 24)

    d2 = parse_date_safe("19 / 03 / 2026", "Sheet", 3, "date", "ID", issues)
    assert d2 == date(2026, 3, 19)
    assert len(issues) == 0


def test_clean_customer_row_synthetic():
    """Verify customer cleaning and data quality alerts on dummy customer data."""
    issues = []
    # Fully valid synthetic customer
    c1 = clean_customer_row(
        sr=1,
        name="Synthetic Customer One",
        email="synthetic.one@example.com",
        phone="07123456789",
        license_num="SYNTH123456AB9CD",
        source_row=2,
        issues=issues,
    )
    assert c1 is not None
    assert c1.full_name == "Synthetic Customer One"
    assert c1.email == "synthetic.one@example.com"
    assert len(issues) == 0

    # Synthetic customer with missing email and phone
    c2 = clean_customer_row(
        sr=2,
        name="Synthetic Customer Two",
        email=None,
        phone=None,
        license_num="SYNTH654321XY1ZW",
        source_row=3,
        issues=issues,
    )
    assert c2 is not None
    assert c2.email is None
    # Expect warnings/info for missing email and phone
    issue_types = {i.issue_type for i in issues}
    assert "MISSING_CUSTOMER_EMAIL" in issue_types
    assert "MISSING_CUSTOMER_PHONE" in issue_types


def test_cross_sheet_duplicate_and_conflict_resolution():
    """Verify duplicate detection and status conflict identification on synthetic tickets."""
    issues = []

    # Case 1: Same ticket in two sheets with complementary fields and matching status
    p1 = PCNRecord(
        ticket_number="SYNTH-TICKET-01",
        raw_ticket_number="SYNTH-TICKET-01",
        vehicle_registration="AB12 CDE",
        normalized_registration="AB12CDE",
        issue_date=date(2026, 5, 1),
        raw_status="Not Payed",
        normalized_status=PCNStatus.UNPAID,
        source_sheet="Outstanding PCN",
        source_row=10,
    )
    p2 = PCNRecord(
        ticket_number="SYNTH-TICKET-01",
        raw_ticket_number="SYNTH-TICKET-01",
        vehicle_registration="AB12 CDE",
        normalized_registration="AB12CDE",
        fine_amount=130.0,
        raw_status="paying needed",
        normalized_status=PCNStatus.ACTION_NEEDED,
        source_sheet="paying needed",
        source_row=5,
    )

    harmonized_list = resolve_pcn_duplicates([p1, p2], issues)
    assert len(harmonized_list) == 1
    h = harmonized_list[0]
    assert h.ticket_number == "SYNTH-TICKET-01"
    assert h.fine_amount == 130.0  # Merged from p2
    assert h.issue_date == date(2026, 5, 1)  # Merged from p1
    assert h.has_conflict is False
    assert any(i.issue_type == "DUPLICATE_TICKET_ACROSS_SHEETS" for i in issues)

    # Case 2: Ticket with CONFLICT (PAID in one sheet, UNPAID in another)
    issues_conflict = []
    p_paid = PCNRecord(
        ticket_number="SYNTH-CONFLICT-99",
        raw_ticket_number="SYNTH-CONFLICT-99",
        raw_status="Payed",
        normalized_status=PCNStatus.PAID,
        source_sheet="Outstanding PCN",
        source_row=20,
    )
    p_unpaid = PCNRecord(
        ticket_number="SYNTH-CONFLICT-99",
        raw_ticket_number="SYNTH-CONFLICT-99",
        raw_status="Not Payed",
        normalized_status=PCNStatus.UNPAID,
        source_sheet="paying needed",
        source_row=12,
    )

    conflict_res = resolve_pcn_duplicates([p_paid, p_unpaid], issues_conflict)
    assert len(conflict_res) == 1
    c_rec = conflict_res[0]
    assert c_rec.has_conflict is True
    assert c_rec.normalized_status == PCNStatus.CONFLICT
    assert any(i.issue_type == "STATUS_CONFLICT" and i.severity == IssueSeverity.CRITICAL for i in issues_conflict)
