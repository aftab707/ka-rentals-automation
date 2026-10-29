"""Excel upload and import history endpoints."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.entities import ImportRun
from backend.app.schemas.api import ImportRunResponse
from backend.app.services.importer import run_import_pipeline

router = APIRouter()

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("/import/excel", response_model=ImportRunResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Uploads an Excel file, validates content/type, and runs the idempotent import pipeline."""
    # 1. Validation of file extension
    filename = file.filename or ""
    if not (filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only Excel files (.xlsx, .xls) are accepted.",
        )

    # 2. Secure file write with size limit checking
    upload_dir = settings.SOURCE_DATA_PATH
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Create safe temporary file in source directory
    temp_suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(dir=upload_dir, suffix=temp_suffix, delete=False) as temp_dest:
        temp_file_path = Path(temp_dest.name)
        total_bytes = 0

        while chunk := await file.read(65536):
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE_BYTES:
                temp_dest.close()
                if temp_file_path.exists():
                    temp_file_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File exceeds maximum permissible size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
                )
            temp_dest.write(chunk)

    try:
        # Run atomic import pipeline
        import_run = run_import_pipeline(temp_file_path, db)
        return import_run
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Import failed during processing: {str(exc)}",
        )
    finally:
        # Cleanup temporary uploaded file
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except OSError:
                pass


@router.get("/imports", response_model=List[ImportRunResponse])
def get_import_history(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Returns historical list of import executions."""
    stmt = select(ImportRun).order_by(desc(ImportRun.id)).limit(limit)
    return db.scalars(stmt).all()
