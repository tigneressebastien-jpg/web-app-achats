from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PlatformParamModel
from app.schemas import PlatformParamSchema, PlatformResolveRequest
from app.services.platform_repository_service import (
    load_effective_platforms,
    model_to_platform_param,
)
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
    return [_schema_from_param(model_to_platform_param(row)) for row in rows]


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
    return _schema_from_param(model_to_platform_param(row))


@router.get("/effective", response_model=list[PlatformParamSchema])
def list_effective_platforms(db: Session = Depends(get_db)) -> list[PlatformParamSchema]:
    return [
        _schema_from_param(platform)
        for platform in load_effective_platforms(db)
    ]


@router.post("/resolve", response_model=PlatformParamSchema)
def resolve_platform(
    payload: PlatformResolveRequest,
    db: Session = Depends(get_db),
) -> PlatformParamSchema:
    plateformes = _platforms_from_payload(payload.plateformes, db)
    try:
        platform = mapper_code_erp_plateformes(
            payload.code_erp,
            plateformes,
            inclure_inactives=payload.inclure_inactives,
        )
    except PlatformNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _schema_from_param(platform)


def _platforms_from_payload(
    plateformes: list[PlatformParamSchema] | None,
    db: Session,
) -> list[PlatformParam]:
    if plateformes is None:
        return load_effective_platforms(db)
    return [PlatformParam(**platform.model_dump()) for platform in plateformes]


def _schema_from_param(platform: PlatformParam) -> PlatformParamSchema:
    return PlatformParamSchema(**platform.__dict__)
