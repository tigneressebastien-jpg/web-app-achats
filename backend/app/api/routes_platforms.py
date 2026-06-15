from __future__ import annotations

from fastapi import APIRouter

from app.schemas import PlatformParamSchema
from app.services.platform_service import lire_plateformes_dynamiques


router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.get("/defaults", response_model=list[PlatformParamSchema])
def get_default_platforms() -> list[PlatformParamSchema]:
    return [
        PlatformParamSchema(**platform.__dict__)
        for platform in lire_plateformes_dynamiques()
    ]

