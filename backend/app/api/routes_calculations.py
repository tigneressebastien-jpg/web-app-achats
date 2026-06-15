from __future__ import annotations

from fastapi import APIRouter

from app.schemas import CalculationRequest, CalculationResponse, PlatformParamSchema
from app.services.besoin_service import calculer_besoin_rapide_lent
from app.services.platform_service import PlatformParam, lire_plateformes_dynamiques


router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("/seb/simple", response_model=CalculationResponse)
def calculate_seb_simple(payload: CalculationRequest) -> CalculationResponse:
    plateformes = _platforms_from_payload(payload.plateformes)
    results = []
    for row in payload.rows:
        result = calculer_besoin_rapide_lent(
            row.model_dump(),
            plateformes,
            texte_consigne=row.texte_consigne,
            valeur_consigne=row.valeur_consigne,
            coeff_lent=row.coeff_lent,
            pct_lent=row.pct_lent,
            pourcentage_lent=row.pourcentage_lent,
        )
        results.append(result.as_dict())
    return CalculationResponse(buyer=payload.buyer, results=results)


def _platforms_from_payload(
    plateformes: list[PlatformParamSchema] | None,
) -> list[PlatformParam]:
    if plateformes is None:
        return lire_plateformes_dynamiques()
    return [PlatformParam(**platform.model_dump()) for platform in plateformes]
