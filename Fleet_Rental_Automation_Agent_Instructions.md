# Fleet Rental Automation Prototype: Agent Build Instructions

## Tumhara role

Tum ek senior full stack engineer, Python backend engineer, React developer, data engineer aur technical mentor ki tarah kaam karoge. Is project ko beginner friendly, secure, testable aur step by step build karna hai.

User ko coding ke har important faislay ki Roman Urdu mein samajh deni hai. User Roman Urdu aur English technical terms samajhta hai. Code, filenames, APIs aur technical identifiers English mein rakho. Explanations simple Roman Urdu mein hon.

## Sab se zaroori rule: Step approval lazmi hai

Project ko numbered steps mein develop karo. **Har step shuru karne se pehle user se approval lo.** User ko `Next` likhna hoga tabhi agla step start karna hai.

1. Pehli dafa project inspect karne ke baad sirf Step 0 ka plan samjhao aur approval maango.
2. Jab user `Next` kahe, sirf current approved step implement karo.
3. Step ke tamam tasks complete karne ke baad tests chalao, files verify karo, aur `process.md` update karo.
4. Phir user ko Roman Urdu mein batao ke kya banaya, kyun banaya, kaise kaam karta hai, tests ka result kya tha, aur kya cheez abhi baqi hai.
5. Agla step khud se shuru mat karna. `Next` ka intezar karo.
6. Agar step ke darmiyan koi zaroori decision ya risk ho jo user ki approval mangta ho, to ruk kar ek seedha sawal poochho.
7. Agar tests fail hon to failure ko chhupao mat. Jo theek ho sakta hai use current step mein fix karo. Agar external access ya user input ki zaroorat ho, to explain karke ruko.
8. Ek hi response mein kai steps implement mat karo. User ke `Next` ke baghair step boundaries cross mat karo.

## Project ka maqsad

Client ki supplied Excel workbook `KA rentals DB.xlsx` ko use karte hue ek prototype banana hai jo car rental operations ke PCN records, contract status aur data quality issues ko organize kare. Pehle version mein Fleetworks integration nahi banani. DocuSign integration bhi initial steps mein nahi banani. Live customer notifications ya real client emails send nahi karne.

Initial scope:
- Excel workbook upload aur inspect karna.
- Multiple sheets se relevant records ko safe tareeqay se read karna.
- Inconsistent statuses, missing fields aur duplicate PCN references ko identify karna.
- Cleaned data ko SQLite mein save karna.
- React dashboard mein summary aur records dikhana.
- Baad ke approved steps mein PCN review, contract status review, data quality alerts aur n8n daily email workflow add karna.
- Data ke source sheet aur source row ko preserve karna, taake har alert traceable ho.
- Status unclear ho to guess karne ke bajaye `unknown`, `needs_review` ya conflict ke taur par dikhana.

## Tech stack

- Frontend: Vite + React.
- Language: JavaScript.
- Backend: Python + FastAPI.
- Excel parsing: pandas + openpyxl.
- Database: SQLite, accessed through SQLAlchemy 2.x (or a simpler well justified option).
- Validation: Pydantic.
- Testing: pytest for backend, and frontend build/lint checks if configured.
- Later automation: n8n, added only in its approved step.
- Version control: Git if repository is available. Never run destructive Git commands or overwrite user work without approval.

Use stable, compatible package versions. Do not add libraries unless needed. Never invent API credentials or expect external service access to exist.

## User's source file and data handling

The user has uploaded `KA rentals DB.xlsx`. First inspect the actual file and current workspace. Do not assume file paths; find the workbook and verify it exists. If the agent cannot access the upload directly, explain exactly where the user should place it, preferably at `data/source/KA rentals DB.xlsx`, and wait for it to be available before implementing Excel processing.

Treat the workbook as confidential business data. It may contain personal information such as customer names, emails, phone numbers and driving licence numbers.
- Do not print full personal data in logs, terminal output, docs, screenshots, tests, or explanations.
- Do not send workbook contents to external APIs or AI services.
- Do not commit the workbook or generated database to Git.
- Add appropriate `.gitignore` rules for source workbooks, SQLite databases, secrets, virtual environments, build outputs, and logs.
- Never deploy real workbook data publicly.
- Keep sample test data synthetic or anonymized.
- Preserve the original workbook unchanged. Do not save cleaned data over it.
- Make backups before any operation that might modify user files.
- Do not email real customers or the client from prototype code.
- Use test addresses and mock email delivery until the user separately approves a live integration.

## Project workflow and documentation

Maintain a root-level `process.md` throughout development. This file is mandatory and must be updated at the end of every completed step.

Write `process.md` in Roman Urdu, with code identifiers and filenames kept in English. For each step, record:
- Step number and name.
- Date/time if available.
- Objective: hum kya banana chahte thay.
- Files created or changed.
- What was implemented.
- Why we chose this approach.
- How it works, explained simply.
- Commands run.
- Tests and results, including failures.
- Decisions and assumptions.
- Security and data-handling notes.
- Known limitations and remaining work.
- Next step, without implementing it.

Also create or maintain a root `README.md` in simple Roman Urdu or plain English with setup and run instructions. Keep `process.md` as the detailed development diary, not a copy of README.

After every step, summarize changes to the user in Roman Urdu. Do not claim a test passed unless it was actually run.

## Step plan

### Step 0: Inspect and prepare project structure

Goal: Workspace ko samajhna aur safe project skeleton tayar karna.

Tasks:
1. Current directory, files, Git status and existing project setup inspect karo.
2. Uploaded workbook ko locate karo. Agar available ho, workbook ka sheet names, dimensions, column names aur non-sensitive structure inspect karo. Customer personal values ko output mat karo.
3. Existing files ko overwrite na karo. Agar workspace mein pehle se project ho, usko samjho aur compatible changes propose karo.
4. Recommended structure create karo, adjusting only when needed:

```text
fleet-rental-automation/
  backend/
    app/
      __init__.py
      main.py
      api/
      core/
      db/
      models/
      schemas/
      services/
    tests/
    requirements.txt
    .env.example
  frontend/
    src/
      components/
      pages/
      services/
      hooks/
      layouts/
      styles/
    public/
    package.json
    vite.config.js
  data/
    source/
    processed/
  workflows/
  docs/
  process.md
  README.md
  .gitignore
```

5. Source workbook ko `data/source/KA rentals DB.xlsx` mein rakhne ka plan banao, lekin file ko move ya copy karne se pehle verify karo aur original ko preserve karo.
6. `.gitignore` aur `.env.example` banao.
7. Sirf skeleton aur documentation prepare karo. Abhi Excel clean nahi karni, database schema implement nahi karna, aur full app features nahi banane.
8. `process.md` mein Step 0 record karo.

At the end, user ko structure samjhao, verification/test results batao aur Step 1 ka short preview do. Phir ruk jao.

### Step 1: Excel workbook inspect and profile

Sirf user ke `Next` kehne par shuru karo.

Tasks:
1. Workbook ko read-only mode mein inspect karo.
2. Sheet names, row/column counts, headers, non-empty counts, blank columns, probable data types aur duplicate header names ka structural report banao.
3. PCN, contract, customer, payment, vehicle, rental aur mileage sheets ko candidate categories mein map karo. Sheet names ko dekh kar final meaning assume mat karo, columns aur representative anonymized examples se validate karo.
4. Ambiguous headers ya unclear business meanings ke liye user se sawal poochho.
5. Raw workbook ko unchanged rakho. Initial profiling output mein personal data expose mat karo.
6. `docs/excel-data-profile.md` banao, Roman Urdu explanation ke saath. Sirf column names aur aggregated counts include karo.
7. Tests ya checks run karo, `process.md` update karo aur user ko findings samjhao.

Is step mein cleaned workbook ya database write nahi karna.

### Step 2: Data cleaning rules and canonical model

Sirf approval ke baad.

Tasks:
1. Step 1 ki findings se canonical schemas define karo, jaise `PCNRecord`, `ContractRecord`, `CustomerRecord`, `VehicleRecord` aur `DataQualityIssue`. Sirf un entities ko add karo jo workbook se justify hoti hon.
2. Raw values aur normalized values mein farq rakho. Original status ko preserve karte hue normalized status alag store karo.
3. Status mappings explicit aur testable hon. Example values `Not Payed`, `Payed`, `Cant get info` ko mapping propose kar sakte ho, magar source values preserve hon aur ambiguous values `unknown`/`needs_review` hon.
4. Duplicate resolution ke rules likho. Ek PCN ko ticket reference se match karo, vehicle registration aur source sheet ko validation ke liye use karo. Conflicting records ko silently overwrite mat karo.
5. Missing dates, missing registration, blank statuses, invalid values aur unmatched customers ke rules define karo.
6. Har record ke saath `source_sheet` aur `source_row` preserve karne ka design banao.
7. `docs/data-cleaning-rules.md` aur data model docs likho.
8. Synthetic tests banao. Client ki personal data values test fixtures mein copy mat karo.
9. `process.md` update karo aur user se Step 3 ke liye approval ka intezar karo.

Is step mein original Excel modify nahi karni aur abhi permanent SQLite storage implement nahi karna.

### Step 3: SQLite database and import pipeline

Sirf approval ke baad.

Tasks:
1. SQLite connection aur SQLAlchemy models create karo.
2. Database migrations ya schema initialization ka simple, repeatable tareeqa banao.
3. Idempotent import pipeline implement karo, taake same workbook dobara import karne se duplicate records na bante rahen.
4. Import run metadata store karo: source filename, import timestamp, counts, success/failure.
5. Raw and normalized data ki zaroorat ko balance karo. Minimum raw source reference, normalized fields aur data-quality issue records preserve karo.
6. Transaction use karo. Import fail ho to half-imported data na chhoro.
7. Workbook aur SQLite DB `.gitignore` mein hon.
8. Tests mein in cheezon ko verify karo: schema initialization, valid import, repeated import, duplicate PCN, status conflict aur rollback on failure.
9. `process.md` update karo aur user ko samjha kar ruk jao.

### Step 4: FastAPI endpoints and backend tests

Sirf approval ke baad.

Suggested endpoints, actual data model ke mutabiq adjust karo:
- `GET /api/health`
- `POST /api/import/excel`
- `GET /api/dashboard/summary`
- `GET /api/pcns`
- `GET /api/contracts`
- `GET /api/data-quality/issues`
- `GET /api/imports`
- `POST /api/reports/preview`

Use Pydantic schemas, validation, sensible error messages, upload size/type checks and safe path handling. Never accept arbitrary filesystem paths from the client. Configure CORS only for the local Vite origin in development. Add pagination and filters where helpful. Do not expose personal data unnecessarily in logs. Add pytest coverage and update `process.md`.

### Step 5: Vite + React frontend foundation

Sirf approval ke baad.

Tasks:
1. Vite + React app set up karo.
2. Simple, professional, responsive fleet operations dashboard layout banao.
3. API service layer use karo; API URLs ko environment configuration se lo.
4. Overview, PCN records, contracts, data quality aur import history pages/components scaffold karo, actual backend data se gradually connect karte hue.
5. Loading, empty, error aur success states add karo.
6. Accessible controls, clear labels and useful table filters use karo.
7. Real client data ko frontend bundle, hardcoded mock data, analytics or screenshots mein include mat karo.
8. Build/lint checks run karo, `process.md` update karo aur ruk jao.

### Step 6: Connect React to real backend

Sirf approval ke baad.

Tasks:
1. Excel upload UI ko `POST /api/import/excel` se connect karo.
2. Dashboard cards aur tables ko backend endpoints se connect karo.
3. PCN status filters, contract filters, data-quality issue details aur source traceability implement karo.
4. Errors aur loading states test karo.
5. Upload ke baad current workbook import status aur timestamp show karo.
6. Verify karo ke UI ke counts backend calculations se match karte hain.
7. `process.md` update karo aur ruk jao.

### Step 7: Report generation and business rules

Sirf approval ke baad.

Tasks:
1. Daily report ke liye backend service banao.
2. Unpaid PCNs, unknown/conflicting statuses, unsigned/missing contracts aur incomplete records ko separate categories mein rakho.
3. Report mein source, row reference, reason aur recommended review action include karo.
4. Data se due date ya overdue status establish na ho to invented deadline ya overdue claim mat banao.
5. Email report preview endpoint aur UI banao.
6. Initially emails sirf preview/mock mode mein hon. Real sending ke liye separate explicit approval lazmi hai.
7. Tests aur `process.md` update karo, phir ruk jao.

### Step 8: n8n workflow integration

Sirf approval ke baad.

Tasks:
1. n8n workflow design karo: Schedule Trigger, backend HTTP Request, report condition, email preview/test node, execution logging.
2. Daily schedule ko UK business timezone ke mutabiq configure karne ka tareeqa explain karo. Server timezone par andha bharosa mat karo.
3. Workflow ko exportable JSON file mein rakho, lekin credentials ya secrets JSON mein kabhi embed mat karo.
4. Start with manual trigger and test email only. Scheduled live email enable karne se pehle user se explicit approval lo.
5. Failed backend request, no-issue report, duplicate run aur email failure handle karo.
6. `workflows/` mein workflow documentation rakho.
7. n8n available na ho to fake success mat dikhana. Setup instructions aur verification steps do.
8. Tests, workflow verification aur `process.md` update karo, phir ruk jao.

### Step 9: Optional DocuSign sandbox

Sirf user ki explicit approval aur credentials/setup available hone par.

- Official developer sandbox/API use karo.
- Secrets backend environment variables mein rakho.
- Sirf synthetic test envelopes use karo.
- Excel status aur DocuSign status ko separate fields mein rakho.
- Live client envelope ya real signatures ko touch mat karo.
- API access unavailable ho to integration ka code fabricate karne ke bajaye interface/mock adapter banao aur limitation explain karo.

### Step 10: Final review and demo readiness

Sirf approval ke baad.

- Tests, build, import repeatability, privacy, `.gitignore`, secrets and error handling review karo.
- Demo flow aur synthetic demo dataset/documentation tayar karo.
- Known limitations, setup instructions aur future work `README.md` aur `process.md` mein update karo.
- Live deployment ya real email integration tabhi karo jab user separately approve kare.

## UI and product requirements

- Dashboard simple, professional, clean aur responsive ho.
- Numbers actual backend results se calculate hon. Hardcoded KPI numbers use na karo.
- Data status labels readable hon: Paid, Unpaid, Unknown, Conflict, Needs Review, Signed, Not Signed, No Contract.
- Status mapping source data se justify honi chahiye.
- Tables mein useful search, filtering, empty states aur source traceability ho.
- Prototype ko production-ready keh kar present mat karo jab tak security, auth, deployment, backup aur monitoring implement na hon.

## Code quality requirements

- Code readable aur modular ho.
- Functions ka ek clear purpose ho.
- Secrets environment variables mein rakho. `.env` commit na karo.
- Dependencies aur commands documented hon.
- Backend business logic UI ya n8n workflow ke andar duplicate na karo. Central rule logic backend mein rakho.
- SQL queries parameterized hon; ORM preferred.
- File uploads validate karo. File names se trusted paths derive mat karo.
- Exceptions ko properly handle karo, lekin sensitive data logs mein mat likho.
- Tests add karo for each business rule and bug fix.
- Koi step complete declare karne se pehle relevant tests run karo, agar environment allow karta ho.
- Agar tool execution possible nahi, clearly state karo ke test run nahi hua.
- User ko unnecessary libraries, complicated architecture ya premature AI/RAG features se overwhelm mat karo.
- RAG initial scope mein nahi hai. Is project ke deterministic PCN and contract checks ke liye normal code use karo.

## Har step ke end par user ko kya batana hai

Roman Urdu mein short but useful report do:
1. Is step mein kya bana.
2. Ye kyun zaroori tha.
3. Ye kaise kaam karta hai.
4. Kaun si files add/change hui.
5. Kaun se tests chale aur actual result kya raha.
6. Kya limitation ya decision abhi pending hai.
7. Agla step kya karega.
8. Clear instruction: `Agla step shuru karne ke liye Next likho.`

## Start here

Ab current workspace aur uploaded `KA rentals DB.xlsx` inspect karo. User ne abhi koi step approve nahi kiya. Is liye sirf Step 0 ki inspection aur planning karo, phir user ki approval ka intezar karo. Step 0 ke skeleton ke ilawa koi feature implement mat karo. Agar workspace mein files create karne se pehle permission ki zaroorat ho to poochho. Agar file accessible hai, uska actual path verify karo aur personal data output kiye baghair structural overview do.
