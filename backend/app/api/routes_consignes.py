from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ConsigneApplyRequest,
    ConsigneApplyResponse,
    ConsigneSavedListResponse,
    ConsigneSavedRequest,
    ConsigneSavedSchema,
)
from app.services.consigne_repository_service import list_consignes, upsert_consigne
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


@router.post("/saved", response_model=ConsigneSavedSchema)
def save_consigne(
    payload: ConsigneSavedRequest,
    db: Session = Depends(get_db),
) -> ConsigneSavedSchema:
    try:
        consigne = upsert_consigne(
            db,
            code_article=payload.code_article,
            plateforme=payload.plateforme,
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
    plateforme: str | None = None,
    db: Session = Depends(get_db),
) -> ConsigneSavedListResponse:
    consignes = list_consignes(
        db,
        acheteur=acheteur,
        code_article=code_article,
        plateforme=plateforme,
    )
    return ConsigneSavedListResponse(
        consignes=[_consigne_to_schema(consigne) for consigne in consignes]
    )


def _consigne_to_schema(consigne) -> ConsigneSavedSchema:
    return ConsigneSavedSchema(
        id=consigne.id,
        code_article=consigne.code_article,
        plateforme=consigne.plateforme,
        texte_consigne=consigne.texte_consigne,
        valeur_consigne=consigne.valeur_consigne,
        acheteur=consigne.acheteur,
    )
