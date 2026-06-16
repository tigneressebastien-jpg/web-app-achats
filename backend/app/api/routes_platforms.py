from __future__ import annotations

from fastapi import APIRouter, HTTPException

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
