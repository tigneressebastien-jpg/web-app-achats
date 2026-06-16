from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PlatformParamModel
from app.schemas import PlatformParamSchema, PlatformResolveRequest
from app.services.platform_service import (
    PlatformNotFoundError,
    PlatformParam,
    lire_plateformes_dynamiques,
    mapper_code_erp_plateformes,
)


router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("/defaults", response_model=list[PlatformParamSchema])
def get_default_platforms() -> list[PlatformParamSchema]:
    return [
        PlatformParamSchema(**platform.__dict__)
        for platform in lire_plateformes_dynamiques()
    ]


@router.get("/saved", response_model=list[PlatformParamSchema])
def list_saved_platforms(db: Session = Depends(get_db)) -> list[PlatformParamSchema]:
    rows = (
        db.query(PlatformParamModel)
        .order_by(PlatformParamModel.code_erp.asc())
        .all()
    )
    return [_schema_from_model(row) for row in rows]


@router.post("/saved", response_model=PlatformParamSchema)
def upsert_saved_platform(
    payload: PlatformParamSchema,
    db: Session = Depends(get_db),
) -> PlatformParamSchema:
    code_erp = payload.code_erp.strip().upper()
    if not code_erp:
        raise HTTPException(status_code=400, detail="code_erp est obligatoire")

    row = (
        db.query(PlatformParamModel)
        .filter(PlatformParamModel.code_erp == code_erp)
        .one_or_none()
    )
    if row is None:
        row = PlatformParamModel(code_erp=code_erp)
        db.add(row)

    row.pf_rapide = payload.pf_rapide
    row.pf_lente = payload.pf_lente
    row.actif = payload.actif
    row.lent_avec_pourcentage = payload.lent_avec_pourcentage
    db.commit()
    db.refresh(row)
    return _schema_from_model(row)


@router.post("/resolve", response_model=PlatformParamSchema)
def resolve_platform(payload: PlatformResolveRequest) -> PlatformParamSchema:
    plateformes = _platforms_from_payload(payload.plateformes)
    try:
        platform = mapper_code_erp_plateformes(
            payload.code_erp,
            plateformes,
            inclure_inactives=payload.inclure_inactives,
        )
    except PlatformNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PlatformParamSchema(**platform.__dict__)


def _platforms_from_payload(
    plateformes: list[PlatformParamSchema] | None,
) -> list[PlatformParam]:
    if plateformes is None:
        return lire_plateformes_dynamiques()
    return [PlatformParam(**platform.model_dump()) for platform in plateformes]


def _schema_from_model(row: PlatformParamModel) -> PlatformParamSchema:
    return PlatformParamSchema(
        code_erp=row.code_erp,
        pf_rapide=row.pf_rapide,
        pf_lente=row.pf_lente,
        actif=row.actif,
        lent_avec_pourcentage=row.lent_avec_pourcentage,
    )
