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
from fastapi.responses import HTMLResponse

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

# Configure CORS for local development and Vercel deployments
allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:5173"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints (Health, Import, PCNs, Fleet, Issues, Reports)
app.include_router(api_router, prefix="/api")


@app.api_route("/", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
def root_health_check():
    """Root health check for Render, UptimeRobot, and cloud monitors."""
    return {"status": "ok", "app": "Fleet Rental Automation API", "version": "0.1.0"}


@app.get("/callback", response_class=HTMLResponse)
def oauth_callback(code: str = None):
    """Handles OAuth redirect callback for DocuSign Admin Consent."""
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head><title>DocuSign Consent Granted</title></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0fdf4; margin: 0;">
            <div style="background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center; max-width: 450px; border: 1px solid #bbf7d0;">
                <div style="font-size: 48px; margin-bottom: 12px;">✅</div>
                <h2 style="color: #16a34a; margin: 0 0 8px;">DocuSign Consent Granted!</h2>
                <p style="color: #475569; font-size: 14px; line-height: 1.5;">Aap ki DocuSign app successfully authenticate ho chuki hai. Backend ab automatically DocuSign envelopes create aur sign karwa sakta hai. Aap is tab ko band kar sakte hain.</p>
            </div>
        </body>
        </html>
        """
    )
