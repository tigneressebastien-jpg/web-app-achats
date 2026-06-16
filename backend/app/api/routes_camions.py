from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import (
    CamionProjectionRequest,
    CamionProjectionResponse,
    CamionProjectionRow,
)
from app.services.camion_service import (
    PLATEFORMES_CAMIONS_EXCEL,
    calculer_projection_camions,
)


router = APIRouter(prefix="/camions", tags=["camions"])


@router.post("/projection", response_model=CamionProjectionResponse)
def project_camions(payload: CamionProjectionRequest) -> CamionProjectionResponse:
    try:
        projections = calculer_projection_camions(
            jour_depart=payload.jour_depart,
            camions_depart=payload.camions_depart,
            nombre_jours=payload.nombre_jours,
            inclure_depart=payload.inclure_depart,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CamionProjectionResponse(
        jour_depart=payload.jour_depart,
        camions_depart=payload.camions_depart,
        nombre_jours=payload.nombre_jours,
        inclure_depart=payload.inclure_depart,
        projections=[
            CamionProjectionRow(**projection.__dict__)
            for projection in projections
        ],
    )


@router.get("/platforms/excel")
def get_camion_excel_platform_mapping() -> dict[str, str]:
    return PLATEFORMES_CAMIONS_EXCEL
