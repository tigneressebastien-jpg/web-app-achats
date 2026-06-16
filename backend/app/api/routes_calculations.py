from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CalculationFromBatchResponse,
    CalculationFromImportResponse,
    CalculationRequest,
    CalculationResponse,
    ImportAnomalySchema,
    PlatformParamSchema,
)
from app.services.besoin_service import ErpRow, calculer_besoin_rapide_lent
from app.services.import_repository_service import (
    erp_row_model_to_domain,
    get_import_batch,
)
from app.services.import_service import read_erp_file
from app.services.platform_repository_service import load_effective_platforms
from app.services.platform_service import PlatformNotFoundError, PlatformParam


router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("/seb/simple", response_model=CalculationResponse)
def calculate_seb_simple(
    payload: CalculationRequest,
    db: Session = Depends(get_db),
) -> CalculationResponse:
    plateformes = _platforms_from_payload(payload.plateformes, db)
    results = _calculate_rows_for_seb(
        rows=[row.model_dump() for row in payload.rows],
        plateformes=plateformes,
        coeff_lent_by_default=None,
        pct_lent_by_default=None,
        pourcentage_lent_by_default=None,
    )
    return CalculationResponse(buyer=payload.buyer, results=results)


@router.post("/seb/from-erp-import", response_model=CalculationFromImportResponse)
async def calculate_seb_from_erp_import(
    file: UploadFile = File(...),
    buyer: str = Form("Seb"),
    coeff_lent: float = Form(0),
    pct_lent: float | None = Form(None),
    pourcentage_lent: float | None = Form(None),
    db: Session = Depends(get_db),
) -> CalculationFromImportResponse:
    content = await file.read()
    try:
        preview = read_erp_file(file.filename or "", content)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    plateformes = load_effective_platforms(db)
    results = _calculate_rows_for_seb(
        rows=list(preview.rows),
        plateformes=plateformes,
        coeff_lent_by_default=coeff_lent,
        pct_lent_by_default=pct_lent,
        pourcentage_lent_by_default=pourcentage_lent,
    )

    return CalculationFromImportResponse(
        buyer=buyer,
        filename=file.filename or "",
        source_type=preview.source_type,
        import_row_count=len(preview.rows),
        import_anomalies=[
            ImportAnomalySchema(**anomaly.__dict__)
            for anomaly in preview.anomalies
        ],
        results=results,
    )


@router.post("/seb/from-import-batch/{batch_id}", response_model=CalculationFromBatchResponse)
def calculate_seb_from_import_batch(
    batch_id: int,
    buyer: str = "Seb",
    coeff_lent: float = 0,
    pct_lent: float | None = None,
    pourcentage_lent: float | None = None,
    db: Session = Depends(get_db),
) -> CalculationFromBatchResponse:
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch introuvable")

    plateformes = load_effective_platforms(db)
    rows = [erp_row_model_to_domain(row) for row in batch.rows]
    results = _calculate_rows_for_seb(
        rows=rows,
        plateformes=plateformes,
        coeff_lent_by_default=coeff_lent,
        pct_lent_by_default=pct_lent,
        pourcentage_lent_by_default=pourcentage_lent,
    )

    return CalculationFromBatchResponse(
        buyer=buyer,
        batch_id=batch.id,
        filename=batch.filename,
        source_type=batch.source_type,
        import_row_count=len(rows),
        results=results,
    )


def _calculate_rows_for_seb(
    *,
    rows: list[ErpRow | dict[str, object]],
    plateformes: list[PlatformParam],
    coeff_lent_by_default: float | None,
    pct_lent_by_default: float | None,
    pourcentage_lent_by_default: float | None,
) -> list[dict[str, object]]:
    results = []
    for row in rows:
        code_article = row.code_article if isinstance(row, ErpRow) else str(row.get("code_article", ""))
        try:
            if isinstance(row, ErpRow):
                result = calculer_besoin_rapide_lent(
                    row,
                    plateformes,
                    coeff_lent=coeff_lent_by_default or 0,
                    pct_lent=pct_lent_by_default,
                    pourcentage_lent=pourcentage_lent_by_default,
                )
            else:
                result = calculer_besoin_rapide_lent(
                    row,
                    plateformes,
                    texte_consigne=row.get("texte_consigne"),
                    valeur_consigne=float(row.get("valeur_consigne", 0) or 0),
                    coeff_lent=float(row.get("coeff_lent", coeff_lent_by_default or 0) or 0),
                    pct_lent=row.get("pct_lent", pct_lent_by_default),
                    pourcentage_lent=row.get("pourcentage_lent", pourcentage_lent_by_default),
                )
        except PlatformNotFoundError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Plateforme ERP invalide pour l'article {code_article}: "
                    f"{exc}"
                ),
            ) from exc
        results.append(result.as_dict())
    return results


def _platforms_from_payload(
    plateformes: list[PlatformParamSchema] | None,
    db: Session,
) -> list[PlatformParam]:
    if plateformes is None:
        return load_effective_platforms(db)
    return [PlatformParam(**platform.model_dump()) for platform in plateformes]
