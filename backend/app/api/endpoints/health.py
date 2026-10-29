"""Health check API endpoint."""

from fastapi import APIRouter
from backend.app.schemas.api import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Returns application service status and version."""
    return HealthResponse(
        status="ok",
        app="Fleet Rental Automation API",
        version="0.1.0",
    )
