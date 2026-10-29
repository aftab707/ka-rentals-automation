"""Fleet Rental Automation - FastAPI Application Entry Point (Skeleton)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Fleet Rental Automation API",
    description="Backend API for managing rental fleet PCNs, contracts, and data quality",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "Fleet Rental Automation API", "version": "0.1.0"}
