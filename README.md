# Fleet Rental Automation Prototype

Yeh project car rental operations ke PCN records, contract status aur data quality issues ko organize aur track karne ke liye banaya ja raha hai.

## Architecture Overview
- **Backend:** Python + FastAPI
- **Data Engine:** Pandas + OpenPyXL + SQLite (SQLAlchemy 2.x)
- **Frontend:** Vite + React (JavaScript)
- **Automation / Workflow:** n8n (future step)

## Project Directory Structure
```text
D:\KARental\
  ├── backend/
  │   ├── app/
  │   │   ├── api/
  │   │   ├── core/
  │   │   ├── db/
  │   │   ├── models/
  │   │   ├── schemas/
  │   │   ├── services/
  │   │   └── main.py
  │   ├── tests/
  │   ├── requirements.txt
  │   └── .env.example
  ├── frontend/
  │   ├── src/
  │   │   ├── components/
  │   │   ├── pages/
  │   │   ├── services/
  │   │   ├── hooks/
  │   │   ├── layouts/
  │   │   └── styles/
  │   ├── package.json
  │   └── vite.config.js
  ├── data/
  │   ├── source/       # Confidential raw workbooks (git-ignored)
  │   └── processed/    # Processed datasets (git-ignored)
  ├── docs/             # Technical documentation & data profiling
  ├── workflows/        # n8n workflows
  ├── process.md        # Step-by-step development log (Roman Urdu)
  ├── README.md
  └── .gitignore
```

## Setup & Running Instructions

### Backend Setup
1. Virtual environment create aur activate karein (optional but recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Dependencies install karein:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Backend tests run karein:
   ```bash
   $env:PYTHONPATH="."
   python -m pytest backend/tests/ -v
   ```
4. Development server start karein:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Frontend directory mein jayein aur packages install karein:
   ```bash
   cd frontend
   npm install
   ```
2. Development server start karein:
   ```bash
   npm run dev
   ```

## Data Privacy & Security Rules
- Client ki raw Excel workbook (`KA rentals DB.xlsx`) confidential business data hai.
- Sensitive files (`*.xlsx`, `*.db`, `.env`) `.gitignore` ke zariye version control se exclude ki gayi hain.
- Testing synthetic / mock data par hoti hai, real personal records kabi log ya commit nahi hotay.
