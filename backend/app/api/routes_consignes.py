from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import ConsigneApplyRequest, ConsigneApplyResponse
from app.services.consigne_service import appliquer_consigne


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
