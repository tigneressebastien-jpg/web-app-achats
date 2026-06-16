from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CalculationResponse
from app.services.calculation_repository_service import get_calculation_run
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
    return _csv_response(csv_content, filename="calculation-results.csv")


@router.get("/calculation-runs/{run_id}.csv")
def export_calculation_run_csv(
    run_id: int,
    db: Session = Depends(get_db),
) -> Response:
    run = get_calculation_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run calcul introuvable")

    csv_content = calculation_results_to_csv(
        [_stored_result_to_export_row(result) for result in run.results]
    )
    return _csv_response(csv_content, filename=f"calculation-run-{run_id}.csv")


def _stored_result_to_export_row(result) -> dict[str, object]:
    return {
        "code_article": result.code_article,
        "libelle_article": result.libelle_article,
        "code_plateforme_erp": result.code_plateforme_erp,
        "pf_rapide": result.pf_rapide,
        "pf_lente": result.pf_lente,
        "solde_corrige": 0,
        "besoin_rapide": result.besoin_rapide,
        "besoin_lent": result.besoin_lent,
        "besoin_lent_brut": 0,
        "surplus_positif": 0,
        "besoin_total": result.besoin_total,
        "consigne_regle": result.consigne_appliquee,
        "logs": [],
    }


def _csv_response(csv_content: str, *, filename: str) -> Response:
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )
