import os
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    """Verify that the FastAPI skeleton health endpoint responds correctly."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_project_structure_exists():
    """Verify essential project directories and files exist."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    expected_dirs = [
        base_dir / "backend" / "app",
        base_dir / "frontend" / "src",
        base_dir / "data" / "source",
        base_dir / "data" / "processed",
        base_dir / "workflows",
        base_dir / "docs",
    ]
    for d in expected_dirs:
        assert d.exists() and d.is_dir(), f"Expected directory missing: {d}"


def test_source_workbook_preserved():
    """Verify source workbook exists in data/source and original is intact."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    source_wb = base_dir / "data" / "source" / "KA rentals DB.xlsx"
    root_wb = base_dir / "KA rentals DB.xlsx"
    assert source_wb.exists(), "Source copy in data/source does not exist."
    assert root_wb.exists(), "Original root workbook was removed or displaced."


def test_gitignore_covers_sensitive_files():
    """Verify .gitignore contains patterns to prevent leaking sensitive files."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    gitignore_path = base_dir / ".gitignore"
    assert gitignore_path.exists(), ".gitignore is missing."
    content = gitignore_path.read_text(encoding="utf-8")
    for pattern in ["*.xlsx", "*.db", ".env", "node_modules", "__pycache__"]:
        assert pattern in content, f"Pattern {pattern} missing from .gitignore"
