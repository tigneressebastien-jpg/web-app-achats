from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ErpImportBatchDetailResponse,
    ErpImportBatchSummary,
    ErpImportPreviewResponse,
    ErpImportRowSchema,
    ErpImportSaveResponse,
    ImportAnomalySchema,
)
from app.services.import_repository_service import (
    get_import_batch,
    list_import_batches,
    save_erp_import_preview,
)
from app.services.import_service import read_erp_file


router = APIRouter(prefix="/imports", tags=["imports"])


@router.get("/status")
def imports_status() -> dict[str, str]:
    return {"status": "ready"}


@router.post("/erp/preview", response_model=ErpImportPreviewResponse)
async def preview_erp_import(file: UploadFile = File(...)) -> ErpImportPreviewResponse:
    preview = await _read_upload_preview(file)
    return _preview_response(file.filename or "", preview)


@router.post("/erp/save", response_model=ErpImportSaveResponse)
async def save_erp_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ErpImportSaveResponse:
    preview = await _read_upload_preview(file)
    batch = save_erp_import_preview(
        db,
        filename=file.filename or "",
        preview=preview,
    )
    return ErpImportSaveResponse(
        batch_id=batch.id,
        filename=batch.filename,
        source_type=batch.source_type,
        row_count=len(preview.rows),
        anomalies=[ImportAnomalySchema(**anomaly.__dict__) for anomaly in preview.anomalies],
    )


@router.get("/batches", response_model=list[ErpImportBatchSummary])
def get_import_batches(db: Session = Depends(get_db)) -> list[ErpImportBatchSummary]:
    return [
        ErpImportBatchSummary(
            batch_id=batch.id,
            filename=batch.filename,
            source_type=batch.source_type,
            imported_at=batch.imported_at.isoformat(),
            row_count=len(batch.rows),
        )
        for batch in list_import_batches(db)
    ]


@router.get("/batches/{batch_id}", response_model=ErpImportBatchDetailResponse)
def get_import_batch_detail(
    batch_id: int,
    db: Session = Depends(get_db),
) -> ErpImportBatchDetailResponse:
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch introuvable")

    return ErpImportBatchDetailResponse(
        batch_id=batch.id,
        filename=batch.filename,
        source_type=batch.source_type,
        imported_at=batch.imported_at.isoformat(),
        row_count=len(batch.rows),
        rows=[
            ErpImportRowSchema(
                code_article=row.code_article,
                libelle_article=row.libelle_article,
                code_plateforme_erp=row.code_plateforme_erp,
                prevision=row.prevision,
                solde_previsionnel_j1=row.solde_previsionnel_j1,
            )
            for row in batch.rows
        ],
    )


async def _read_upload_preview(file: UploadFile):
    content = await file.read()
    try:
        return read_erp_file(file.filename or "", content)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _preview_response(filename: str, preview) -> ErpImportPreviewResponse:
    return ErpImportPreviewResponse(
        filename=filename,
        source_type=preview.source_type,
        row_count=len(preview.rows),
        rows=[ErpImportRowSchema(**row.__dict__) for row in preview.rows],
        anomalies=[ImportAnomalySchema(**anomaly.__dict__) for anomaly in preview.anomalies],
    )
