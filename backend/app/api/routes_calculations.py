from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas import (
    CalculationFromImportResponse,
    CalculationRequest,
    CalculationResponse,
    ImportAnomalySchema,
    PlatformParamSchema,
)
from app.services.besoin_service import calculer_besoin_rapide_lent
from app.services.import_service import read_erp_file
from app.services.platform_service import (
    PlatformNotFoundError,
    PlatformParam,
    lire_plateformes_dynamiques,
)


router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("/seb/simple", response_model=CalculationResponse)
def calculate_seb_simple(payload: CalculationRequest) -> CalculationResponse:
    plateformes = _platforms_from_payload(payload.plateformes)
    results = []
    for row in payload.rows:
        try:
            result = calculer_besoin_rapide_lent(
                row.model_dump(),
                plateformes,
                texte_consigne=row.texte_consigne,
                valeur_consigne=row.valeur_consigne,
                coeff_lent=row.coeff_lent,
                pct_lent=row.pct_lent,
                pourcentage_lent=row.pourcentage_lent,
            )
        except PlatformNotFoundError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Plateforme ERP invalide pour l'article {row.code_article}: "
                    f"{exc}"
                ),
            ) from exc
        results.append(result.as_dict())
    return CalculationResponse(buyer=payload.buyer, results=results)


@router.post("/seb/from-erp-import", response_model=CalculationFromImportResponse)
async def calculate_seb_from_erp_import(
    file: UploadFile = File(...),
    buyer: str = Form("Seb"),
    coeff_lent: float = Form(0),
    pct_lent: float | None = Form(None),
    pourcentage_lent: float | None = Form(None),
) -> CalculationFromImportResponse:
    content = await file.read()
    try:
        preview = read_erp_file(file.filename or "", content)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    plateformes = lire_plateformes_dynamiques()
    results = []
    for row in preview.rows:
        try:
            result = calculer_besoin_rapide_lent(
                row,
                plateformes,
                coeff_lent=coeff_lent,
                pct_lent=pct_lent,
                pourcentage_lent=pourcentage_lent,
            )
        except PlatformNotFoundError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Plateforme ERP invalide pour l'article {row.code_article}: "
                    f"{exc}"
                ),
            ) from exc
        results.append(result.as_dict())

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


def _platforms_from_payload(
    plateformes: list[PlatformParamSchema] | None,
) -> list[PlatformParam]:
    if plateformes is None:
        return lire_plateformes_dynamiques()
    return [PlatformParam(**platform.model_dump()) for platform in plateformes]
