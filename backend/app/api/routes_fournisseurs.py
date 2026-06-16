from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import FournisseurFillRequest, FournisseurFillResponse
from app.services.fournisseur_service import calculer_remplissage_fournisseur


router = APIRouter(prefix="/fournisseurs", tags=["fournisseurs"])


@router.post("/remplissage", response_model=FournisseurFillResponse)
def fill_supplier_platform(payload: FournisseurFillRequest) -> FournisseurFillResponse:
    try:
        result = calculer_remplissage_fournisseur(
            plateforme=payload.plateforme,
            commandes=payload.commandes,
            besoin=payload.besoin,
            palettisation=payload.palettisation,
            pas_colis=payload.pas_colis,
            pf_interdite=payload.pf_interdite,
            arrondi=payload.arrondi,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FournisseurFillResponse(**result.__dict__)
