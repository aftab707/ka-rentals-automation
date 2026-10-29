# Excel Workbook Data Profile: `KA rentals DB.xlsx`

Yeh document `data/source/KA rentals DB.xlsx` ki complete structural aur exploratory profiling report hai. Is profiling ko read-only mode mein perform kiya gaya hai aur is mein customer ka koi bhi personal data (Name, Email, Phone, License) expose nahi kiya gaya.

---

## 1. Executive Summary

- **Total Sheets:** 14
- **Active Operational Entities Identified:**
  1. Master Customers (`Customer details`)
  2. Vehicle Fleet & Hire Contracts (`Current Contracts`, `pay day`)
  3. PCN / Parking Infringements (`Outstanding PCN`, `paying needed`, `Sheet15`, aur 6 Driver Sheets)
  4. Vehicle Mileage & Odometer Tracking (`Sheet12`, `Milegae`)
- **Key Challenge:** Workbook mein standardized schema ki kami hai; sheets alag alag waqt par manually maintain ki gayi hain, jis ki wajah se missing headers, unnormalized registrations, informal first-name references, aur duplicate PCN entries mojood hain.

---

## 2. Comprehensive Sheet-by-Sheet Profiling

### Category A: Customer Entity

#### 1. `Customer details`
- **Purpose:** Master customer register.
- **Total Rows:** 52 data rows (Excel row count: 53)
- **Total Columns:** 5
- **Column Details:**
  | Column Name | Inferred Dtype | Non-Null Count | Null Count | Data Quality Observation |
  | :--- | :--- | :--- | :--- | :--- |
  | `sr` | Integer | 52 | 0 | Sequential identifier |
  | `Name` | String | 52 | 0 | Complete full customer names |
  | `Email` | String | 46 | 6 | 6 records mein email missing hai |
  | `Phone number` | Float / String | 32 | 20 | 20 records mein contact number missing hai |
  | `Driving License Number ` | String | 40 | 12 | 12 records missing; trailing space in header |

---

### Category B: Fleet & Contract Entities

#### 2. `Current Contracts`
- **Purpose:** Official contract tracking aur legal status.
- **Total Rows:** 13 rows
- **Total Columns:** 8
- **Column Details:**
  | Column Name | Inferred Dtype | Non-Null Count | Null Count | Data Quality Observation |
  | :--- | :--- | :--- | :--- | :--- |
  | `Sr` | Integer | 13 | 0 | Sequential identifier |
  | `Name` | String | 12 | 1 | 1 row mein customer name missing |
  | `Reg number` | String | 13 | 0 | Unique vehicle registrations (13 total) |
  | `Start date` | Mixed (Date/String) | 10 | 3 | Invalid markers mojood hain: `'-----------------------'`, `'00/00/00'` |
  | `End date` | Mixed (Date/String) | 10 | 3 | Invalid markers mojood hain: `'----------------------'`, `'00/00/00'` |
  | `Rate` | Integer | 13 | 0 | Numeric rate values |
  | `Payment Period` | String | 12 | 1 | Values: `'Per Month'`, `'Per Week'`, `'One month'` |
  | `Status contract` | String | 13 | 0 | Values: `'Signed'`, `'Not signed'`, `'No Contract'` |

#### 3. `pay day`
- **Purpose:** Operational vehicle rental terms aur hire duration.
- **Total Rows:** 13 active rows (Excel formatted up to 1001 rows with 987 blank rows)
- **Total Columns:** 8
- **Column Details:**
  | Column Name | Inferred Dtype | Non-Null Count | Null Count | Data Quality Observation |
  | :--- | :--- | :--- | :--- | :--- |
  | `Registration` | String | 13 | 0 | Matches exactly the 13 vehicles in Current Contracts |
  | `Vehicle` | String | 13 | 0 | Vehicle make/model (e.g. Kia Niro, Tesla Model 3, Ford Kuga) |
  | `Name` | String | 9 | 4 | 4 driver names missing |
  | `Start date ` | Mixed (Date/String) | 8 | 5 | Trailing space in header; mixed formats (ISO vs DD/MM/YYYY) |
  | `end date` | Mixed (Date/String) | 8 | 5 | Mixed formats (ISO vs DD/MM/YYYY) |
  | `hire rate` | String | 8 | 5 | Text formatted currency (e.g. `'£1,300 PM'`, `'£180 per week'`, `'£500pm'`, `'670'`) |
  | `hire duration` | String | 6 | 7 | Descriptive durations (e.g. `'1 Month'`, `'28 (days)'`, `'5 years'`) |
  | `Unnamed: 7` | String | 1 | 12 | Extra column with 1 stray entry |

---

### Category C: PCN / Parking Infringement Entities

#### 4. `Outstanding PCN`
- **Purpose:** Main PCN tracking log.
- **Total Rows:** 45 active rows
- **Total Columns:** 7
- **Column Details:**
  | Column Name | Inferred Dtype | Non-Null Count | Null Count | Data Quality Observation |
  | :--- | :--- | :--- | :--- | :--- |
  | `SR` | Integer | 45 | 0 | Sequential counter |
  | `Customer name` | String | 45 | 0 | 15 out of 16 are single words (first names/handles) |
  | `Reg Number` | String | 45 | 0 | Vehicle registrations |
  | `PCN number` | String | 45 | 0 | Unique PCN reference numbers |
  | `Date of PCN` | DateTime | 44 | 1 | 1 missing date |
  | `Status` | String | 44 | 1 | Values: `'Not Payed'`, `'Cant get info '`, `'Payed'`, 1 Null |
  | `Column 1` | String | 42 | 3 | Payment portal URLs (e.g., Council / Horizon / Euro Car Parks links) |

#### 5. `paying needed`
- **Purpose:** Immediate actionable PCN payment list.
- **Total Rows:** 36 active rows (Excel formatted up to 990 rows with 954 blank rows)
- **Total Columns:** 3
- **Column Details:**
  | Column Name | Inferred Dtype | Non-Null Count | Null Count | Data Quality Observation |
  | :--- | :--- | :--- | :--- | :--- |
  | `Ticket Reference` | String | 36 | 0 | 10 tickets overlap with `Outstanding PCN` |
  | `Vehicle Reg` | String | 36 | 0 | 10 unique vehicle registrations |
  | `Amount` | Mixed (Float/String) | 36 | 0 | PCN fine amounts |

#### 6. `Sheet15`
- **Purpose:** Driver/Customer specific PCN status review sheet.
- **Total Rows:** 9 rows
- **Total Columns:** 4
- **Column Details:**
  | Column Name | Inferred Dtype | Non-Null Count | Null Count | Data Quality Observation |
  | :--- | :--- | :--- | :--- | :--- |
  | `Number` | String | 9 | 0 | PCN ticket numbers (5 overlap with `paying needed`, 1 with `Outstanding PCN`) |
  | `Surname` | String | 9 | 0 | Single driver surname across all rows |
  | `Status` | String | 9 | 0 | Values: `'Awaiting Payment'`, `'Fine Not Assignable'`, `'Action Needed'` |
  | `Ticket Date` | DateTime | 9 | 0 | Date of ticket |

#### 7. Driver-Specific PCN Sheets (6 Sheets)
- **Sheets:** `kashif ` (5 rows), `Mohammed PCN` (3 rows), `Mohammed COW PCN` (7 rows), `Adangoh ` (7 rows), `Ashley ` (3 rows), `Edwards PCN` (4 rows).
- **Key Findings:**
  - `Ashley ` sheet mein header row missing hai (Row 0 par seedha ticket reference, fine, aur registration mojood hai).
  - Trailing spaces sheet names mein mojood hain (`'kashif '`, `'Adangoh '`, `'Ashley '`).
  - Dates: `Date of offence` DateTime format mein hai.
  - Fines: Numeric aur text mixed formats mein hain.
  - Duplicate references: `Edwards PCN` ke tamam 4 tickets `Outstanding PCN` mein mojood hain. `Mohammed PCN` aur `Mohammed COW PCN` ke darmiyan 2 tickets common hain.

---

### Category D: Vehicle Mileage Tracking

#### 8. `Sheet12`
- **Purpose:** Current mileage snapshot and vehicle assignment scratch sheet.
- **Total Rows:** 13 rows
- **Total Columns:** 6 (`Car Reg`, `Milage`, `Unnamed: 2` to `Unnamed: 5`)
- **Observation:** Exact 13 vehicles cover hotay hain. `LP21FYB` bina space ke likha gaya hai jabke doosri sheets mein `LP21 FYB` hai. `Unnamed` columns mein driver assignment notes darj hain.

#### 9. `Milegae`
- **Purpose:** Multi-month odometer tracking matrix.
- **Total Rows:** 28 active rows (Excel formatted to 1001 rows)
- **Total Columns:** 35 columns
- **Observation:** Row 0 mukammal blank hai. Actual column headers Row 1 par hain (`REG`, `STARTING`, aur monthly timestamps e.g. `2025-06-01` se `2027-11-01`). Rows mein monthly cumulative mileage values recorded hain.

---

## 3. Critical Data Inconsistencies & Cleaning Rules Required (Step 2 Preview)

1. **Whitespace & Registration Normalization:**
   - Registration strings mein spaces aur casing ko standard karna lazmi hai (e.g. `'LP21FYB'` -> `'LP21 FYB'` ya alphanumeric uppercase `LP21FYB`).
2. **Missing Headers Handling:**
   - `Ashley ` sheet ko parse karte waqt header row ki absence detect karna aur synthetic column mapping assign karna (`PCN number`, `Fine`, `Reg number`).
3. **Ghost / Empty Rows Exclusion:**
   - Sheets mein 900+ empty formatted rows ko drop karna.
4. **Invalid Date Value Sanitization:**
   - `'-----------------------'` aur `'00/00/00'` ko null/None treat karna aur `DataQualityIssue` flag generate karna.
5. **PCN Status Harmonization:**
   - `Not Payed`, `Awaiting Payment`, `Fine Not Assignable`, `Action Needed`, `Cant get info `, `Payed`, aur `None` ko canonical status taxonomy mein map karna jabke raw status string ko audit ke liye preserve rakhna.
6. **Cross-Sheet Traceability:**
   - Har record ke sath `source_sheet` aur `source_row` lazmi store karna taake duplicate ya conflicting tickets ka exact audit trail mojood ho.
