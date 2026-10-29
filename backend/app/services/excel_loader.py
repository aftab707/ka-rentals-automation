"""Excel workbook loader and parser.

Reads sheets from KA rentals DB.xlsx and applies canonical cleaning rules
to produce a structured, validated CleaningResult without modifying original files.
"""

from pathlib import Path
from typing import List, Optional
import openpyxl
import pandas as pd

from backend.app.schemas.canonical import (
    CleaningResult,
    ContractRecord,
    CustomerRecord,
    DataQualityIssue,
    IssueCategory,
    IssueSeverity,
    PCNRecord,
    PCNStatus,
    VehicleRecord,
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


def load_and_clean_workbook(file_path: Path) -> CleaningResult:
    """Safely loads an Excel workbook in read-only mode and executes data cleaning rules."""
    if not file_path.exists():
        raise FileNotFoundError(f"Workbook not found at {file_path}")

    issues: List[DataQualityIssue] = []
    customers: List[CustomerRecord] = []
    pcn_candidates: List[PCNRecord] = []
    contracts: List[ContractRecord] = []
    vehicles_map = {}

    excel_file = pd.ExcelFile(file_path)

    # 1. Process 'Customer details'
    if "Customer details" in excel_file.sheet_names:
        df_cust = pd.read_excel(excel_file, sheet_name="Customer details")
        for idx, row in df_cust.iterrows():
            source_row = int(idx) + 2  # Excel 1-based index (header is row 1)
            # Skip ghost/completely empty rows
            if row.dropna().empty:
                continue

            cust = clean_customer_row(
                sr=row.get("sr"),
                name=row.get("Name"),
                email=row.get("Email"),
                phone=row.get("Phone number"),
                license_num=row.get("Driving License Number "),
                source_row=source_row,
                issues=issues,
            )
            if cust:
                customers.append(cust)

    # 2. Process 'Current Contracts'
    if "Current Contracts" in excel_file.sheet_names:
        df_contracts = pd.read_excel(excel_file, sheet_name="Current Contracts")
        for idx, row in df_contracts.iterrows():
            source_row = int(idx) + 2
            if row.dropna().empty:
                continue

            raw_reg, norm_reg = normalize_registration(row.get("Reg number"))
            if not norm_reg:
                issues.append(
                    DataQualityIssue(
                        category=IssueCategory.CONTRACT,
                        issue_type="MISSING_REGISTRATION",
                        severity=IssueSeverity.CRITICAL,
                        record_identifier=str(row.get("Sr")),
                        source_sheet="Current Contracts",
                        source_row=source_row,
                        field_name="Reg number",
                        raw_value=str(row.get("Reg number")),
                        description="Contract record is missing valid vehicle registration.",
                    )
                )
                continue

            raw_name = str(row.get("Name")).strip() if row.get("Name") and not pd.isna(row.get("Name")) else None
            start_date = parse_date_safe(
                row.get("Start date"),
                source_sheet="Current Contracts",
                source_row=source_row,
                field_name="Start date",
                record_identifier=norm_reg,
                issues=issues,
            )
            end_date = parse_date_safe(
                row.get("End date"),
                source_sheet="Current Contracts",
                source_row=source_row,
                field_name="End date",
                record_identifier=norm_reg,
                issues=issues,
            )
            rate = parse_currency_amount(row.get("Rate"))
            raw_c_status, norm_c_status = normalize_contract_status(row.get("Status contract"))

            contract = ContractRecord(
                contract_id=int(row.get("Sr")) if str(row.get("Sr", "")).isdigit() else idx + 1,
                vehicle_registration=raw_reg or norm_reg,
                normalized_registration=norm_reg,
                customer_name_raw=raw_name,
                start_date=start_date,
                end_date=end_date,
                rate=rate,
                payment_period=str(row.get("Payment Period")).strip() if row.get("Payment Period") and not pd.isna(row.get("Payment Period")) else None,
                raw_status=raw_c_status,
                normalized_status=norm_c_status,
                source_sheet="Current Contracts",
                source_row=source_row,
            )
            contracts.append(contract)
            vehicles_map[norm_reg] = VehicleRecord(
                vehicle_registration=raw_reg or norm_reg,
                normalized_registration=norm_reg,
                assigned_driver_raw=raw_name,
                active_contract_status=norm_c_status.value,
                source_sheet="Current Contracts",
                source_row=source_row,
            )

    # 3. Process 'pay day' to enrich vehicles and contracts
    if "pay day" in excel_file.sheet_names:
        df_payday = pd.read_excel(excel_file, sheet_name="pay day")
        for idx, row in df_payday.iterrows():
            source_row = int(idx) + 2
            if row.dropna().empty:
                continue

            raw_reg, norm_reg = normalize_registration(row.get("Registration"))
            if not norm_reg:
                continue

            v_model = str(row.get("Vehicle")).strip() if row.get("Vehicle") and not pd.isna(row.get("Vehicle")) else None
            h_duration = str(row.get("hire duration")).strip() if row.get("hire duration") and not pd.isna(row.get("hire duration")) else None

            # Enrich corresponding contract
            for c in contracts:
                if c.normalized_registration == norm_reg:
                    c.vehicle_model = v_model
                    c.hire_duration_raw = h_duration

            # Enrich vehicle
            if norm_reg in vehicles_map:
                vehicles_map[norm_reg].make_model = v_model

    # 4. Process 'Sheet12' (Current Mileage snapshot)
    if "Sheet12" in excel_file.sheet_names:
        df_s12 = pd.read_excel(excel_file, sheet_name="Sheet12")
        for idx, row in df_s12.iterrows():
            source_row = int(idx) + 2
            if row.dropna().empty:
                continue
            raw_reg, norm_reg = normalize_registration(row.get("Car Reg"))
            if not norm_reg:
                continue
            mileage_val = parse_currency_amount(row.get("Milage"))
            if norm_reg in vehicles_map:
                vehicles_map[norm_reg].current_mileage = mileage_val

    # 5. Process 'Outstanding PCN'
    if "Outstanding PCN" in excel_file.sheet_names:
        df_opcn = pd.read_excel(excel_file, sheet_name="Outstanding PCN")
        for idx, row in df_opcn.iterrows():
            source_row = int(idx) + 2
            if row.dropna().empty:
                continue

            raw_ticket, norm_ticket = normalize_ticket_number(row.get("PCN number"))
            if not norm_ticket:
                issues.append(
                    DataQualityIssue(
                        category=IssueCategory.PCN,
                        issue_type="MISSING_PCN_NUMBER",
                        severity=IssueSeverity.CRITICAL,
                        record_identifier=str(row.get("SR")),
                        source_sheet="Outstanding PCN",
                        source_row=source_row,
                        field_name="PCN number",
                        raw_value=str(row.get("PCN number")),
                        description="Outstanding PCN row is missing valid ticket number.",
                    )
                )
                continue

            raw_reg, norm_reg = normalize_registration(row.get("Reg Number"))
            pcn_date = parse_date_safe(
                row.get("Date of PCN"),
                source_sheet="Outstanding PCN",
                source_row=source_row,
                field_name="Date of PCN",
                record_identifier=norm_ticket,
                issues=issues,
            )
            raw_stat, norm_stat = normalize_pcn_status(row.get("Status"))
            cust_name = str(row.get("Customer name")).strip() if row.get("Customer name") and not pd.isna(row.get("Customer name")) else None
            portal_url = str(row.get("Column 1")).strip() if row.get("Column 1") and not pd.isna(row.get("Column 1")) else None

            pcn_candidates.append(
                PCNRecord(
                    ticket_number=norm_ticket,
                    raw_ticket_number=raw_ticket or norm_ticket,
                    vehicle_registration=raw_reg,
                    normalized_registration=norm_reg,
                    issue_date=pcn_date,
                    raw_status=raw_stat,
                    normalized_status=norm_stat,
                    customer_name_raw=cust_name,
                    payment_url=portal_url,
                    source_sheet="Outstanding PCN",
                    source_row=source_row,
                )
            )

    # 6. Process 'paying needed'
    if "paying needed" in excel_file.sheet_names:
        df_pn = pd.read_excel(excel_file, sheet_name="paying needed")
        for idx, row in df_pn.iterrows():
            source_row = int(idx) + 2
            if row.dropna().empty:
                continue
            raw_ticket, norm_ticket = normalize_ticket_number(row.get("Ticket Reference"))
            if not norm_ticket:
                continue
            raw_reg, norm_reg = normalize_registration(row.get("Vehicle Reg"))
            amount = parse_currency_amount(row.get("Amount"))

            pcn_candidates.append(
                PCNRecord(
                    ticket_number=norm_ticket,
                    raw_ticket_number=raw_ticket or norm_ticket,
                    vehicle_registration=raw_reg,
                    normalized_registration=norm_reg,
                    fine_amount=amount,
                    raw_status="paying needed",
                    normalized_status=PCNStatus.ACTION_NEEDED,
                    source_sheet="paying needed",
                    source_row=source_row,
                )
            )

    # 7. Process 'Sheet15'
    if "Sheet15" in excel_file.sheet_names:
        df_s15 = pd.read_excel(excel_file, sheet_name="Sheet15")
        for idx, row in df_s15.iterrows():
            source_row = int(idx) + 2
            if row.dropna().empty:
                continue
            raw_ticket, norm_ticket = normalize_ticket_number(row.get("Number"))
            if not norm_ticket:
                continue
            raw_stat, norm_stat = normalize_pcn_status(row.get("Status"))
            t_date = parse_date_safe(
                row.get("Ticket Date"),
                source_sheet="Sheet15",
                source_row=source_row,
                field_name="Ticket Date",
                record_identifier=norm_ticket,
                issues=issues,
            )
            s_name = str(row.get("Surname")).strip() if row.get("Surname") and not pd.isna(row.get("Surname")) else None

            pcn_candidates.append(
                PCNRecord(
                    ticket_number=norm_ticket,
                    raw_ticket_number=raw_ticket or norm_ticket,
                    issue_date=t_date,
                    raw_status=raw_stat,
                    normalized_status=norm_stat,
                    customer_name_raw=s_name,
                    source_sheet="Sheet15",
                    source_row=source_row,
                )
            )

    # 8. Process Driver PCN Sheets (including Ashley without header)
    driver_sheets = [
        "kashif ",
        "Mohammed PCN",
        "Mohammed COW PCN",
        "Adangoh ",
        "Ashley ",
        "Edwards PCN",
    ]

    for d_sheet in driver_sheets:
        if d_sheet not in excel_file.sheet_names:
            continue

        if d_sheet == "Ashley ":
            # Special handling: Ashley has no header row!
            # Load raw rows via openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            ws = wb["Ashley "]
            issues.append(
                DataQualityIssue(
                    category=IssueCategory.EXCEL_STRUCTURE,
                    issue_type="MISSING_HEADER_ROW",
                    severity=IssueSeverity.WARNING,
                    record_identifier="Ashley ",
                    source_sheet="Ashley ",
                    source_row=1,
                    description="Sheet 'Ashley ' has no header row; parsed using synthetic column mapping (ticket, fine, reg).",
                )
            )
            for r_idx, row_cells in enumerate(ws.iter_rows(values_only=True), start=1):
                if not any(row_cells):
                    continue
                # col 0: ticket, col 1: fine, col 2: reg
                raw_t = row_cells[0] if len(row_cells) > 0 else None
                raw_f = row_cells[1] if len(row_cells) > 1 else None
                raw_r = row_cells[2] if len(row_cells) > 2 else None

                raw_ticket, norm_ticket = normalize_ticket_number(raw_t)
                if not norm_ticket:
                    continue
                raw_reg, norm_reg = normalize_registration(raw_r)
                amount = parse_currency_amount(raw_f)

                pcn_candidates.append(
                    PCNRecord(
                        ticket_number=norm_ticket,
                        raw_ticket_number=raw_ticket or norm_ticket,
                        vehicle_registration=raw_reg,
                        normalized_registration=norm_reg,
                        fine_amount=amount,
                        raw_status=f"Driver sheet: {d_sheet.strip()}",
                        normalized_status=PCNStatus.NEEDS_REVIEW,
                        customer_name_raw="Ashley",
                        source_sheet=d_sheet,
                        source_row=r_idx,
                    )
                )
        else:
            df_ds = pd.read_excel(excel_file, sheet_name=d_sheet)
            for idx, row in df_ds.iterrows():
                source_row = int(idx) + 2
                if row.dropna().empty:
                    continue
                raw_ticket, norm_ticket = normalize_ticket_number(row.get("PCN number"))
                if not norm_ticket:
                    continue
                raw_reg, norm_reg = normalize_registration(row.get("Reg number"))
                offence_date = parse_date_safe(
                    row.get("Date of offence"),
                    source_sheet=d_sheet,
                    source_row=source_row,
                    field_name="Date of offence",
                    record_identifier=norm_ticket,
                    issues=issues,
                )
                fine_amount = parse_currency_amount(row.get("Fine"))
                driver_name = d_sheet.replace("PCN", "").replace("COW", "").strip()

                pcn_candidates.append(
                    PCNRecord(
                        ticket_number=norm_ticket,
                        raw_ticket_number=raw_ticket or norm_ticket,
                        vehicle_registration=raw_reg,
                        normalized_registration=norm_reg,
                        issue_date=offence_date,
                        fine_amount=fine_amount,
                        raw_status=f"Driver sheet: {d_sheet.strip()}",
                        normalized_status=PCNStatus.NEEDS_REVIEW,
                        customer_name_raw=driver_name,
                        source_sheet=d_sheet,
                        source_row=source_row,
                    )
                )

    # 9. Deduplicate and harmonize PCNs across sheets
    harmonized_pcns = resolve_pcn_duplicates(pcn_candidates, issues)

    total_records = len(customers) + len(harmonized_pcns) + len(contracts) + len(vehicles_map)

    return CleaningResult(
        customers=customers,
        pcns=harmonized_pcns,
        contracts=contracts,
        vehicles=list(vehicles_map.values()),
        issues=issues,
        total_records_processed=total_records,
    )
