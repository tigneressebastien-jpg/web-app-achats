from __future__ import annotations

from fastapi import APIRouter, Response

from app.schemas import CalculationResponse
from app.services.export_service import calculation_results_to_csv


router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/status")
def exports_status() -> dict[str, str]:
    return {"status": "ready"}


@router.post("/calculation-results.csv")
def export_calculation_results_csv(payload: CalculationResponse) -> Response:
    csv_content = calculation_results_to_csv(
        [result.model_dump() for result in payload.results]
    )
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=calculation-results.csv",
        },
    )
