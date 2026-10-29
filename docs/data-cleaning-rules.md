# Data Cleaning Rules & Canonical Model Specification

Yeh document car rental operations ke data cleaning rules, field transformations, canonical data models, aur cross-sheet conflict resolution ka mukammal reference hai.

---

## 1. Architectural Principles

1. **Non-Destructive Processing:** Original source workbook `KA rentals DB.xlsx` ko kabhi overwrite ya alter nahi kiya jata.
2. **Audit Traceability (Raw Preservation):** Har record ke sath uska `source_sheet`, `source_row`, aur original un-normalized raw string preserve kiya jata hai.
3. **No Guessing (Explicit Unknowns):** Agar koi date corrupt ho ya status ambiguous ho, to system guess karne ke bajaye `DataQualityIssue` alert create karta hai aur status ko `unknown` ya `needs_review` assign karta hai.
4. **Deterministic Conflict Resolution:** Agar ek PCN ticket do mukhtalif sheets mein conflicting statuses rakhta ho (e.g. ek sheet mein 'Paid' aur doosri mein 'paying needed'), to system silently overwrite nahi karta balki record ko `conflict` status de kar critical alert raise karta hai.

---

## 2. Canonical Data Models (Pydantic)

### 2.1 `CustomerRecord`
Master client directory:
- `customer_id`: Unique integer (derived from `sr` or sequential counter)
- `full_name`: Customer ka poora legal name (Mandatory)
- `email`: Cleaned lowercase email address (Optional)
- `phone`: Cleaned phone string (Optional)
- `driving_license`: Cleaned license identifier (Optional)
- `source_sheet`: Source sheet name (`Customer details`)
- `source_row`: Source Excel row index

### 2.2 `PCNRecord`
Penalty Charge Notice entity:
- `ticket_number`: Normalized uppercase alphanumeric string
- `raw_ticket_number`: Raw source string
- `vehicle_registration`: Raw registration string
- `normalized_registration`: Cleaned uppercase alphanumeric registration
- `issue_date`: Valid Python `date` object ya `None`
- `fine_amount`: Numeric fine amount (`float` ya `None`)
- `raw_status`: Original status string from source
- `normalized_status`: Canonical status (`paid`, `unpaid`, `action_needed`, `needs_review`, `unknown`, `conflict`)
- `customer_name_raw`: Driver name or handle from source
- `payment_url`: Direct link to council/operator payment portal
- `source_sheet`: Sheet jahan se record mila
- `source_row`: Exact row index
- `has_conflict`: Boolean flag for cross-sheet status discrepancies
- `conflict_notes`: Detailed conflict audit log

### 2.3 `ContractRecord`
Rental agreement entity:
- `contract_id`: Identifier
- `vehicle_registration`: Raw registration
- `normalized_registration`: Cleaned uppercase registration
- `customer_name_raw`: Associated customer/driver name
- `start_date`: Valid `date` object ya `None`
- `end_date`: Valid `date` object ya `None`
- `rate`: Numeric rental fee
- `payment_period`: String frequency (e.g., `'Per Month'`, `'Per Week'`)
- `raw_status`: Original agreement status
- `normalized_status`: Canonical status (`signed`, `not_signed`, `no_contract`, `unknown`)
- `vehicle_model`: Vehicle make/model (e.g., `'Tesla Model 3'`, `'Kia Niro'`)
- `hire_duration_raw`: Rental duration descriptor (e.g., `'1 Month'`, `'5 years'`)
- `source_sheet`: Source sheet name
- `source_row`: Source row index

### 2.4 `VehicleRecord`
Fleet vehicle register:
- `vehicle_registration`: Raw registration
- `normalized_registration`: Standardized registration
- `make_model`: Vehicle model
- `current_mileage`: Latest recorded mileage
- `assigned_driver_raw`: Current driver name
- `active_contract_status`: Status of current contract
- `source_sheet`: Source sheet
- `source_row`: Source row

### 2.5 `DataQualityIssue`
Central anomaly tracking entity:
- `category`: `pcn`, `contract`, `customer`, `vehicle`, `excel_structure`
- `issue_type`: Standard issue code (e.g., `STATUS_CONFLICT`, `INVALID_DATE_FORMAT`)
- `severity`: `critical`, `warning`, `info`
- `record_identifier`: Ticket number, registration, or customer name
- `source_sheet`: Sheet location
- `source_row`: Excel row index
- `field_name`: Affected column name
- `raw_value`: Original faulty value
- `description`: Plain explanation of the anomaly

---

## 3. Specific Cleaning & Normalization Rules

### 3.1 Vehicle Registration Normalization
- **Rule:** UK vehicle registration strings mein se all spaces, hyphens aur punctuation remove ki jati hain aur characters uppercase mein convert kiye jatay hain.
- **Example:**
  - `'LA19 WPD'` -> `'LA19WPD'`
  - `'lp21fyb'` -> `'LP21FYB'`
  - `'FG72 UTX '` -> `'FG72UTX'`

### 3.2 PCN Status Normalization Taxonomy
| Raw Status Values in Workbook | Canonical Normalized Status | Meaning & Business Action |
| :--- | :--- | :--- |
| `'Payed'`, `'paid'` | `paid` | Penalty settled |
| `'Not Payed'`, `'awaiting payment'` | `unpaid` | Outstanding fine requiring settlement |
| `'paying needed'` (from sheet name/context), `'Action Needed'` | `action_needed` | Immediate operational action required |
| `'Cant get info '`, `'Fine Not Assignable'` | `needs_review` | Verification required with council/authority |
| `None`, `""`, `'nan'` | `unknown` | Status not recorded |
| Multiple sheets with contradicting status | `conflict` | Critical discrepancy requiring manual intervention |

### 3.3 Contract Status Normalization
| Raw Status String | Canonical Normalized Status |
| :--- | :--- |
| `'Signed'` | `signed` |
| `'Not signed'`, `'unsigned'` | `not_signed` |
| `'No Contract'` | `no_contract` |
| Empty / null / invalid | `unknown` |

### 3.4 Corrupt & Placeholder Date Interception
- **Rule:** Spreadsheets mein manually enter kiye gaye dummy placeholders jaise `'-----------------------'`, `'----------------------'`, aur `'00/00/00'` ko date parsing fail hone se bachaya jata hai.
- **Action:**
  - Date field ko `None` set kiya jata hai.
  - Ek `DataQualityIssue` record emit hota hai: `issue_type="INVALID_DATE_FORMAT"`, `severity=WARNING`.

### 3.5 Currency & Rate Formatting
- **Rule:** Mixed strings jaise `'£1,300 PM'`, `'£180 per week'`, `'£500pm'`, aur numeric floats ko clean float number mein extract kiya jata hai (e.g., `1300.0`, `180.0`, `500.0`).

### 3.6 Headerless Sheet Handling (`Ashley `)
- **Rule:** `Ashley ` sheet mein koi column header row mojood nahi hai. Pehli row par hi ticket number (`LJ40313788`), fine amount (`160.0`), aur car registration (`LA19WPD`) mojud hain.
- **Action:**
  - Synthetic mapping apply hoti hai: Column 0 = Ticket Number, Column 1 = Fine Amount, Column 2 = Vehicle Reg.
  - Ek `DataQualityIssue` record emit hota hai: `issue_type="MISSING_HEADER_ROW"`, `severity=WARNING`.

### 3.7 Ghost / Empty Rows Removal
- **Rule:** Excel workbooks mein default grid formatting ki wajah se 900+ completely blank rows hoti hain (e.g. in `paying needed` and `pay day`).
- **Action:** In rows ko processing pipeline drop kar deti hai taake invalid records generate na hon.

### 3.8 Cross-Sheet PCN Deduplication & Conflict Resolution
- **Rule:** Jab koi ticket multiple sheets (`Outstanding PCN`, `paying needed`, `Sheet15`, Driver tabs) mein paya jaye:
  1. System tamam occurrences ka record preserve karta hai.
  2. Agar ek sheet status `'paid'` kahe aur doosri `'unpaid'` ya `'action_needed'`, to record ko `conflict` mark kiya jata hai aur `CRITICAL` severity alert emit hota hai.
  3. Agar statuses compatible hon, to missing complementary fields (fine amount, portal URL, offence date) merge kar diye jatay hain.
