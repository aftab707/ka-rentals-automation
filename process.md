# Fleet Rental Automation - Process Log (Development Diary)

Yeh document project ke har approved step ka mukammal record aur diary hai. Har step ke mukammal hone par isay update kiya jata hai.

---

## Step 0: Inspect and Prepare Project Structure

- **Date / Time:** 2026-10-29 11:42 PKT
- **Status:** Completed

### 1. Objective (Hum kya banana chahte thay)
Project workspace ko inspect karna, uploaded workbook `KA rentals DB.xlsx` ko safe tareeqay se verify aur preserve karna, Git repository initialize karna, privacy aur confidentiality ke liye `.gitignore` aur environment configurations banana, aur clean, modular backend/frontend skeleton structure tayar karna bina kisi data modification ke.

### 2. Files Created / Changed
- `D:\KARental\.gitignore`: Confidential data (`*.xlsx`, `*.db`, `.env`, virtualenvs, build outputs) ko Git se exclude karne ke liye.
- `D:\KARental\.env.example`: Root level environment variables example.
- `D:\KARental\backend\requirements.txt`: Python backend dependencies (FastAPI, uvicorn, SQLAlchemy, pandas, openpyxl, pytest, httpx, etc.).
- `D:\KARental\backend\.env.example`: Backend specific environment configurations.
- `D:\KARental\backend\app\main.py`: FastAPI application skeleton entrypoint (health endpoint ke saath).
- `D:\KARental\backend\app\__init__.py` aur submodules ke `__init__.py` files (`api`, `core`, `db`, `models`, `schemas`, `services`).
- `D:\KARental\frontend\package.json`: Vite + React frontend configuration.
- `D:\KARental\frontend\vite.config.js`: Vite server and proxy configuration.
- `D:\KARental\backend\tests\test_skeleton.py`: Automated verification tests for Step 0.
- `D:\KARental\data\source\.gitkeep` aur `D:\KARental\data\processed\.gitkeep`: Trackable directories with safe git exclusion.
- `D:\KARental\README.md`: Project setup aur architecture overview.
- `D:\KARental\process.md`: Development diary aur step tracking record.

### 3. What Was Implemented
- Root folder `D:\KARental` mein standard recommended modular structure banaya gaya.
- `KA rentals DB.xlsx` ko locate karke uski ek safe copy `data/source/KA rentals DB.xlsx` mein rakhi gayi, jabke original root file ko bina touch kiye preserve rakha gaya.
- Git repository initialize ki gayi (`git init`).
- Strict `.gitignore` rules apply kiye gaye taake Excel workbooks, database files aur secrets kabhi Git tracking mein na aayen.
- FastAPI basic skeleton create kiya gaya jisme `/api/health` route mojood hai.
- Automated tests likhe gaye jo verify karte hain ke skeleton dirs mojood hain, source copy intact hai, `.gitignore` theek kaam kar raha hai aur health endpoint functional hai.

### 4. Why We Chose This Approach
- **Data Safety:** Client ki actual workbook confidential hai; usay modify karne ke bajaye safe raw copy banayi gayi aur `.gitignore` kiya gaya taake sensitive customer data accidentally leak ya commit na ho.
- **Separation of Concerns:** Backend, frontend, data aur docs ko alag alag directories mein rakha gaya taake testing aur modularity asaan ho.
- **Test-Driven Step Validation:** Step 0 se hi automated tests include kiye gaye taake baseline setup ki health ensure ki ja sake.

### 5. How It Works (Explained Simply)
- Project do hisson mein divided hai: `backend` (Python + FastAPI) aur `frontend` (Vite + React).
- Data files `data/source` mein rahengi jo direct processing pipeline use karegi.
- Jab tests run hote hain, `pytest` FastAPI TestClient ke zariye health route check karta hai aur verify karta hai ke tamam directories aur security exclusions theek se set hain.

### 6. Commands Run
```powershell
# Directory creation & safe file copy
Copy-Item -Path "KA rentals DB.xlsx" -Destination "data/source/KA rentals DB.xlsx" -Force

# Git initialization
git init

# Verification tests execution
$env:PYTHONPATH="."
python -m pytest backend/tests/test_skeleton.py -v
```

### 7. Tests and Results
- **Command:** `python -m pytest backend/tests/test_skeleton.py -v`
- **Result:** **4 passed in 0.79s**
  - `test_health_check`: PASSED (FastAPI health route returns 200 OK)
  - `test_project_structure_exists`: PASSED (All required folders present)
  - `test_source_workbook_preserved`: PASSED (Both source copy and original root file intact)
  - `test_gitignore_covers_sensitive_files`: PASSED (.gitignore excludes *.xlsx, *.db, .env, etc.)

### 8. Decisions and Assumptions
- Workspace root `D:\KARental` ko hi main project root ke taur par use kiya gaya hai taake user ke existing files (`KA rentals DB.xlsx` aur instructions) seamlessly integrate ho sakein.
- Step 0 mein koi heavy npm package installation nahi ki gayi aur na hi Excel file clean ya read ki gayi, jaisa ke rule mein tay hua tha.

### 9. Security and Data-Handling Notes
- Koi bhi personal customer details (names, contact info, driving licence) terminal ya code files mein expose nahi kiye gaye.
- Git status se verify kiya gaya ke `data/source/KA rentals DB.xlsx` aur root `KA rentals DB.xlsx` dono untracked/ignored hain.

### 10. Known Limitations and Remaining Work
- Excel data abhi tak profile aur parse nahi hua hai (Step 1 ka scope).
- Database models aur data cleaning logic abhi implement nahi hui (Step 2 aur Step 3 ka scope).

### 11. Next Step (Without Implementing It)
- **Step 1: Excel workbook inspect and profile** (Completed - see below)

---

## Step 1: Excel Workbook Inspect and Profile

- **Date / Time:** 2026-10-29 12:35 PKT
- **Status:** Completed

### 1. Objective (Hum kya banana chahte thay)
Uploaded Excel workbook `data/source/KA rentals DB.xlsx` ko read-only mode mein inspect karna, tamam 14 sheets ka structural aur categorical profile tayar karna, row/column counts, data types, missing/null values, aur data anomalies identify karna bina kisi customer personal data ko expose kiye, aur comprehensive profiling document `docs/excel-data-profile.md` create karna.

### 2. Files Created / Changed
- `D:\KARental\docs\excel-data-profile.md`: Detailed structural profiling report (in Roman Urdu with technical metrics).
- `D:\KARental\backend\tests\test_excel_profile.py`: Automated tests for sheet count, schema presence, cross-sheet vehicle normalization, and privacy assertion.
- `D:\KARental\process.md`: Updated development log with Step 1 findings and decisions.

### 3. What Was Implemented
- Tamam 14 sheets ka automated exploratory scan kiya gaya.
- Sheets ko 4 key business entities mein categorize kiya gaya:
  1. **Customer Master:** `Customer details` (52 records).
  2. **Contracts & Fleet:** `Current Contracts` (13 vehicles/contracts) aur `pay day` (13 vehicle hire terms).
  3. **PCN & Violations:** `Outstanding PCN` (45 PCNs), `paying needed` (36 actionable PCNs), `Sheet15` (9 review PCNs), aur 6 individual driver sheets (`kashif `, `Mohammed PCN`, `Mohammed COW PCN`, `Adangoh `, `Ashley `, `Edwards PCN`).
  4. **Mileage & Tracking:** `Sheet12` (13 vehicles mileage snapshot) aur `Milegae` (monthly odometer matrix with 35 columns).
- Inconsistencies uncover huin:
  - `Ashley ` sheet mein koi header row nahi hai (Row 0 par direct PCN data hai).
  - `Milegae` sheet mein Row 0 blank hai aur headers Row 1 par hain.
  - Several sheets mein trailing spaces hain (e.g. `'kashif '`, `'Adangoh '`, `'Driving License Number '`).
  - Vehicle registrations mein whitespace mismatch hai (e.g. `LP21FYB` vs `LP21 FYB`, `FG72 UTX `). Normalize karne par 13 vehicles exact match hote hain.
  - Contracts mein invalid date strings hain: `'-----------------------'` aur `'00/00/00'`.
  - Operational sheets (`Outstanding PCN` aur driver sheets) mein customer names legal full names ke bajaye informal first names/handles hain.
- Complete documentation `docs/excel-data-profile.md` generate ki gayi.

### 4. Why We Chose This Approach
- **Privacy Assurance:** Original personal data (names, emails, phone numbers, license numbers) ko expose kiye baghair sirf aggregated structural metrics evaluate kiye gaye.
- **Root-Cause Discovery Before Cleaning:** Data clean karne se pehle actual flaws (missing headers, format variations, ghost rows) samajhna zaroori tha taake Step 2 ke cleaning rules deterministic hon.

### 5. How It Works (Explained Simply)
- Profiling script `openpyxl` aur `pandas` use karke sheet dimensions aur types extract karta hai.
- Automated tests verify karte hain ke tamam sheets mojood hain aur documentation mein koi real customer email address leak nahi hua.

### 6. Commands Run
```powershell
# Run backend pytest suite (all 8 tests)
$env:PYTHONPATH="."
python -m pytest backend/tests/ -v
```

### 7. Tests and Results
- **Command:** `python -m pytest backend/tests/ -v`
- **Result:** **8 passed in 3.51s**
  - `test_source_file_and_sheet_count`: PASSED (All 14 sheets verified)
  - `test_core_sheets_dimensions`: PASSED (Row counts and mandatory columns verified)
  - `test_vehicle_registrations_cross_sheet_consistency`: PASSED (13 vehicles match across CC, pay day, and Sheet12 upon whitespace normalization)
  - `test_profile_documentation_privacy`: PASSED (Verified zero customer emails present in documentation)
  - `test_health_check`: PASSED
  - `test_project_structure_exists`: PASSED
  - `test_source_workbook_preserved`: PASSED
  - `test_gitignore_covers_sensitive_files`: PASSED

### 8. Decisions and Assumptions
- Raw workbook ko bilkul modify nahi kiya gaya.
- Driver sheets ko PCN entity ke audit source records ke taur par treat karne ka plan banaya gaya hai.

### 9. Security and Data-Handling Notes
- Automated privacy test run kiya gaya jo actual customer email list ko `docs/excel-data-profile.md` ke against check karta hai aur confirm karta hai ke koi email text mein shamil nahi.

### 10. Known Limitations and Remaining Work
- Status harmonization mapping aur canonical schemas abhi define hone hain (Step 2).
- Database pipeline abhi implement nahi hui (Step 3).

### 11. Next Step (Without Implementing It)
- **Step 2: Data cleaning rules and canonical model** (Completed - see below)

---

## Step 2: Data Cleaning Rules and Canonical Model

- **Date / Time:** 2026-10-29 13:39 PKT
- **Status:** Completed

### 1. Objective (Hum kya banana chahte thay)
Step 1 ki findings ki roshni mein canonical Pydantic schemas define karna (`PCNRecord`, `ContractRecord`, `CustomerRecord`, `VehicleRecord`, `DataQualityIssue`), raw aur normalized values ko alag preserve karna, deterministic cleaning rules (registration normalization, currency parsing, placeholder date interception, ghost rows removal) implement karna, cross-sheet duplicate PCN deduplication aur conflict resolution engine banana, comprehensive documentation `docs/data-cleaning-rules.md` likhna, aur synthetic unit tests ke sath test karna.

### 2. Files Created / Changed
- `D:\KARental\backend\app\schemas\canonical.py`: Canonical Pydantic schemas for entities and data quality issues.
- `D:\KARental\backend\app\schemas\__init__.py`: Schema exports.
- `D:\KARental\backend\app\services\cleaner.py`: Normalization and cleaning logic (registration, dates, amounts, status mappings, customer cleaning, duplicate/conflict resolver).
- `D:\KARental\backend\app\services\excel_loader.py`: In-memory multi-sheet workbook reader applying cleaning rules (headerless Ashley sheet recovery, ghost row filtering).
- `D:\KARental\docs\data-cleaning-rules.md`: Complete documentation of cleaning rules, status taxonomy, and conflict handling in Roman Urdu.
- `D:\KARental\backend\tests\test_cleaning_rules.py`: Comprehensive synthetic unit tests (zero real client data used).
- `D:\KARental\process.md`: Updated development log with Step 2 details.

### 3. What Was Implemented
- **Pydantic Schemas:**
  - `PCNRecord`: ticket number, registrations (raw & normalized), date, fine amount, raw status, canonical status (`paid`, `unpaid`, `action_needed`, `needs_review`, `unknown`, `conflict`), payment URL, `source_sheet`, `source_row`, `has_conflict`, `conflict_notes`.
  - `ContractRecord`: vehicle registrations, customer name, start/end dates, rate, period, raw status, canonical status (`signed`, `not_signed`, `no_contract`, `unknown`), make/model, hire duration, `source_sheet`, `source_row`.
  - `CustomerRecord`: customer id, full name, email, phone, driving license, source location.
  - `VehicleRecord`: registration, make/model, mileage, driver, active contract status.
  - `DataQualityIssue`: category, issue type, severity (`critical`, `warning`, `info`), record identifier, source sheet & row, field, raw value, description.
- **Normalization Rules:**
  - UK Vehicle Registration: Whitespace & punctuation removal, uppercase normalization (e.g. `'  la19 wpd  '` -> `'LA19WPD'`), jabke raw string intact rehti hai.
  - Status Normalization: `Not Payed` / `Awaiting Payment` -> `unpaid`; `Action Needed` -> `action_needed`; `Payed` -> `paid`; `Cant get info ` / `Fine Not Assignable` -> `needs_review`; `None` -> `unknown`.
  - Date Protection: Corrupt placeholder markers jaise `'-----------------------'` aur `'00/00/00'` ko null treat kiya gaya aur `DataQualityIssue(WARNING, 'INVALID_DATE_FORMAT')` emit kiya gaya.
  - Ashley Sheet Recovery: Sheet mein header row missing hone par synthetic column mapping apply ki gayi (`ticket`, `fine`, `reg`) aur issue log kiya gaya.
  - Cross-Sheet Duplicate & Conflict Engine: Tickets jo multiple sheets mein paye gaye unhein deduplicate kiya gaya. Jab kisi ticket ka status do sheets mein mutazaad (conflicting) paya gaya (e.g., ticket `2577262100014` ek sheet mein 'Payed' aur doosri mein 'paying needed'), to system ne silently overwrite karne ke bajaye record ko `PCNStatus.CONFLICT` mark kiya aur `CRITICAL` severity alert emit kiya.
- **In-Memory Trial on Workbook:**
  - Customers: 52 cleaned.
  - Contracts: 13 cleaned.
  - Vehicles: 13 unique fleet vehicles matched.
  - Harmonized PCNs: 78 unique PCNs (out of total sheet appearances).
  - Data Quality Issues: 75 issues categorized (1 Critical conflict, 5 Warnings, 69 Info).

### 4. Why We Chose This Approach
- **Business Protection (UK Rental Context):** Car rental operations mein PCN ka galat status (paid ko unpaid ya vice versa) bhari financial loss (bailiffs ya double payments) ka sabab ban sakta hai. Explicit `conflict` status aur anomaly tracking human operator ko exact source sheet aur row batati hai.
- **Zero Loss Traceability:** Raw source values aur original sheet/row metadata hamesha preserve hotay hain taake har decision verifiable ho.

### 5. How It Works (Explained Simply)
- Data loader har sheet ko read karta hai, header aur formatting quirks handle karta hai, aur data types ko clean karta hai.
- Tamam collected PCN candidates ko `resolve_pcn_duplicates` function se guzara jata hai jo single tickets ko retain karta hai aur multi-sheet tickets ke fields ko merge karte hue status agreement check karta hai.
- Pytest suite 9 synthetic unit tests chala kar har normalization rule ko dummy data ke sath verify karti hai.

### 6. Commands Run
```powershell
# Run backend pytest suite (all 17 tests)
$env:PYTHONPATH="."
python -m pytest backend/tests/ -v
```

### 7. Tests and Results
- **Command:** `python -m pytest backend/tests/ -v`
- **Result:** **17 passed in 3.57s**
  - `test_registration_normalization`: PASSED
  - `test_ticket_number_normalization`: PASSED
  - `test_pcn_status_normalization`: PASSED
  - `test_contract_status_normalization`: PASSED
  - `test_currency_amount_parsing`: PASSED
  - `test_placeholder_date_interception`: PASSED (invalid dates turn to None + raise issue)
  - `test_valid_date_parsing`: PASSED
  - `test_clean_customer_row_synthetic`: PASSED
  - `test_cross_sheet_duplicate_and_conflict_resolution`: PASSED (verifies deduplication and conflict alert)
  - `test_source_file_and_sheet_count`: PASSED
  - `test_core_sheets_dimensions`: PASSED
  - `test_vehicle_registrations_cross_sheet_consistency`: PASSED
  - `test_profile_documentation_privacy`: PASSED
  - Step 0 skeleton tests: 4 PASSED

### 8. Decisions and Assumptions
- User ki explicit permission ke mutabiq `Ashley ` sheet ko PCN sheet treat kiya gaya with synthetic headers.
- User ke agreement ke mutabiq Excel ki 900+ ghost blank rows ko drop kiya gaya.
- Client ki raw Excel workbook ko modify nahi kiya gaya.
- Database storage abhi implement nahi ki gayi (Step 3 ka scope).

### 9. Security and Data-Handling Notes
- Unit test fixtures mein sirf dummy/synthetic data (e.g. `'Synthetic Customer One'`, `'AB12CDE'`, `'SYNTH-TICKET-01'`) use kiya gaya. Real client personal records kabhi test files mein nahi likhay gaye.

### 10. Known Limitations and Remaining Work
- Cleaned data abhi persistent database (SQLite) mein save nahi ho raha (Step 3).
- FastAPI REST endpoints abhi implement nahi hue (Step 4).

### 11. Next Step (Without Implementing It)
- **Step 3: SQLite database and import pipeline**
  - SQLAlchemy 2.x models design karna (`Customer`, `Vehicle`, `Contract`, `PCN`, `DataQualityIssue`, `ImportRun`).
  - Schema initialization / migration utility setup karna.
  - Idempotent import pipeline banana (taake re-running import duplicates create na kare).
  - Database transactions use karna (atomic commit/rollback on failure).
  - Automated tests likhna for database operations.


