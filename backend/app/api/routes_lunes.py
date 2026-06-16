from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import LunesCreditRequest, LunesCreditResponse
from app.services.lunes_service import compute_lunes_credit_from_week_lent


router = APIRouter(prefix="/lunes", tags=["lunes"])


@router.post("/credit-lent", response_model=LunesCreditResponse)
def compute_lunes_credit(payload: LunesCreditRequest) -> LunesCreditResponse:
    try:
        result = compute_lunes_credit_from_week_lent(
            pf_lente=payload.pf_lente,
            commandes_lent_semaine=payload.commandes_lent_semaine,
            achats_lent_semaine=payload.achats_lent_semaine,
            taux_lent=payload.taux_lent,
            lent_lunes_initial=payload.lent_lunes_initial,
            besoin_erp_rapide_brut=payload.besoin_erp_rapide_brut,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return LunesCreditResponse(**result.__dict__)
