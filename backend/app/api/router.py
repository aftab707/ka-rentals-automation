"""Central API Router aggregating all endpoints."""

from fastapi import APIRouter
from backend.app.api.endpoints import (
    contracts,
    dashboard,
    health,
    importer,
    issues,
    pcns,
    reports,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(importer.router, tags=["Excel Import"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(pcns.router, tags=["PCNs"])
api_router.include_router(contracts.router, tags=["Contracts & Fleet"])
api_router.include_router(issues.router, tags=["Data Quality"])
api_router.include_router(reports.router, tags=["Reports"])
