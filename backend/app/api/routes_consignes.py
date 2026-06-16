from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ConsigneApplyRequest,
    ConsigneApplyResponse,
    ConsigneImportPreviewResponse,
    ConsigneImportResponse,
    ConsigneImportRowSchema,
    ConsigneSavedListResponse,
    ConsigneSavedRequest,
    ConsigneSavedSchema,
    ImportAnomalySchema,
)
from app.services.consigne_import_service import read_consignes_csv_text
from app.services.consigne_repository_service import list_consignes, upsert_consigne
from app.services.consigne_service import appliquer_consigne
from app.services.platform_repository_service import load_effective_platforms
from app.services.platform_service import normaliser_plateforme_erp


router = APIRouter(prefix="/consignes", tags=["consignes"])


@router.post("/apply", response_model=ConsigneApplyResponse)
def apply_consigne(payload: ConsigneApplyRequest) -> ConsigneApplyResponse:
    try:
        result = appliquer_consigne(
            solde_import=payload.solde_import,
            texte_consigne=payload.texte_consigne,
            valeur_consigne=payload.valeur_consigne,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ConsigneApplyResponse(**result.__dict__)


@router.post("/saved", response_model=ConsigneSavedSchema)
def save_consigne(
    payload: ConsigneSavedRequest,
    db: Session = Depends(get_db),
) -> ConsigneSavedSchema:
    try:
        consigne = upsert_consigne(
            db,
            code_article=payload.code_article,
            plateforme_erp=_normalize_consigne_plateforme_erp(payload.plateforme_erp, db),
            texte_consigne=payload.texte_consigne,
            valeur_consigne=payload.valeur_consigne,
            acheteur=payload.acheteur,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _consigne_to_schema(consigne)


@router.get("/saved", response_model=ConsigneSavedListResponse)
def get_saved_consignes(
    acheteur: str | None = None,
    code_article: str | None = None,
    plateforme_erp: str | None = None,
    plateforme: str | None = None,
    db: Session = Depends(get_db),
) -> ConsigneSavedListResponse:
    plateforme_filter = plateforme_erp or plateforme
    if plateforme_filter:
        plateforme_filter = _normalize_consigne_plateforme_erp(plateforme_filter, db)

    consignes = list_consignes(
        db,
        acheteur=acheteur,
        code_article=code_article,
        plateforme_erp=plateforme_filter,
    )
    return ConsigneSavedListResponse(
        consignes=[_consigne_to_schema(consigne) for consigne in consignes]
    )


@router.post("/import/csv/preview", response_model=ConsigneImportPreviewResponse)
async def preview_consignes_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ConsigneImportPreviewResponse:
    preview = await _read_consignes_csv_upload(file)
    return _consigne_import_preview_response(file.filename or "", preview, db)


@router.post("/import/csv", response_model=ConsigneImportResponse)
async def import_consignes_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ConsigneImportResponse:
    preview = await _read_consignes_csv_upload(file)

    saved_consignes = []
    for row in preview.rows:
        consigne = upsert_consigne(
            db,
            code_article=row.code_article,
            plateforme_erp=_normalize_consigne_plateforme_erp(row.plateforme_erp, db),
            texte_consigne=row.texte_consigne,
            valeur_consigne=row.valeur_consigne,
            acheteur=row.acheteur,
        )
        saved_consignes.append(_consigne_to_schema(consigne))

    return ConsigneImportResponse(
        filename=file.filename or "",
        source_type=preview.source_type,
        saved_count=len(saved_consignes),
        consignes=saved_consignes,
        anomalies=_anomaly_schemas(preview.anomalies),
    )


async def _read_consignes_csv_upload(file: UploadFile):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".txt", ""}:
        raise HTTPException(status_code=400, detail=f"Format consignes non supporte: {suffix}")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Fichier consignes non lisible en UTF-8",
        ) from exc
    return read_consignes_csv_text(text)


def _consigne_import_preview_response(
    filename: str,
    preview,
    db: Session,
) -> ConsigneImportPreviewResponse:
    return ConsigneImportPreviewResponse(
        filename=filename,
        source_type=preview.source_type,
        row_count=len(preview.rows),
        rows=[
            ConsigneImportRowSchema(
                code_article=row.code_article,
                plateforme_erp=_normalize_consigne_plateforme_erp(row.plateforme_erp, db),
                texte_consigne=row.texte_consigne,
                valeur_consigne=row.valeur_consigne,
                acheteur=row.acheteur,
            )
            for row in preview.rows
        ],
        anomalies=_anomaly_schemas(preview.anomalies),
    )


def _normalize_consigne_plateforme_erp(value: str, db: Session) -> str:
    try:
        return normaliser_plateforme_erp(value, load_effective_platforms(db))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _anomaly_schemas(anomalies) -> list[ImportAnomalySchema]:
    return [ImportAnomalySchema(**anomaly.__dict__) for anomaly in anomalies]


def _consigne_to_schema(consigne) -> ConsigneSavedSchema:
    return ConsigneSavedSchema(
        id=consigne.id,
        code_article=consigne.code_article,
        plateforme_erp=consigne.plateforme,
        texte_consigne=consigne.texte_consigne,
        valeur_consigne=consigne.valeur_consigne,
        acheteur=consigne.acheteur,
    )
