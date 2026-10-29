"""Fleet Rental Automation - FastAPI Application Entry Point."""

import sys
from pathlib import Path

# Add project root to sys.path so 'backend.app...' works from both root and backend/ directory
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes tables on application startup."""
    init_db()
    yield


app = FastAPI(
    title="Fleet Rental Automation API",
    description="Backend API for managing rental fleet PCNs, contracts, and data quality",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS only for development origin
allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(api_router, prefix="/api")
