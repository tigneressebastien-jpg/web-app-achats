from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import ErpImportPreviewResponse, ErpImportRowSchema, ImportAnomalySchema
from app.services.import_service import read_erp_file


router = APIRouter(prefix="/imports", tags=["imports"])


@router.get("/status")
def imports_status() -> dict[str, str]:
    return {"status": "ready"}


@router.post("/erp/preview", response_model=ErpImportPreviewResponse)
async def preview_erp_import(file: UploadFile = File(...)) -> ErpImportPreviewResponse:
    content = await file.read()
    try:
        preview = read_erp_file(file.filename or "", content)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ErpImportPreviewResponse(
        filename=file.filename or "",
        source_type=preview.source_type,
        row_count=len(preview.rows),
        rows=[ErpImportRowSchema(**row.__dict__) for row in preview.rows],
        anomalies=[ImportAnomalySchema(**anomaly.__dict__) for anomaly in preview.anomalies],
    )
