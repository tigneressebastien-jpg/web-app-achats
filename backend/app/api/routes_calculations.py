from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ConsigneModel
from app.schemas import (
    CalculationFromBatchResponse,
    CalculationFromImportResponse,
    CalculationLogSchema,
    CalculationRequest,
    CalculationResponse,
    CalculationRunDetail,
    CalculationRunSummary,
    ImportAnomalySchema,
    PlatformParamSchema,
    StoredCalculationResultSchema,
)
from app.services.besoin_service import ErpRow, calculer_besoin_rapide_lent
from app.services.calculation_repository_service import (
    get_calculation_run,
    list_calculation_runs,
    save_calculation_run,
)
from app.services.consigne_repository_service import get_consigne_for_erp_row
from app.services.import_repository_service import (
    erp_row_model_to_domain,
    get_import_batch,
)
from app.services.import_service import read_erp_file
from app.services.platform_repository_service import load_effective_platforms
from app.services.platform_service import PlatformNotFoundError, PlatformParam


router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post(
    "/seb/simple",
    response_model=CalculationResponse,
)
def calculate_seb_simple(
    payload: CalculationRequest,
    persist: bool = False,
    db: Session = Depends(get_db),
) -> CalculationResponse:
    plateformes = _platforms_from_payload(payload.plateformes, db)
    results = _calculate_rows_for_seb(
        rows=[row.model_dump() for row in payload.rows],
        plateformes=plateformes,
        coeff_lent_by_default=None,
        pct_lent_by_default=None,
        pourcentage_lent_by_default=None,
        db=db,
        buyer=payload.buyer,
    )
    run_id = _persist_run_if_requested(db, persist=persist, buyer=payload.buyer, results=results)
    return CalculationResponse(buyer=payload.buyer, results=results, run_id=run_id)


@router.post(
    "/seb/from-erp-import",
    response_model=CalculationFromImportResponse,
)
async def calculate_seb_from_erp_import(
    file: UploadFile = File(...),
    buyer: str = Form("Seb"),
    coeff_lent: float = Form(0),
    pct_lent: float | None = Form(None),
    pourcentage_lent: float | None = Form(None),
    persist: bool = Form(False),
    db: Session = Depends(get_db),
) -> CalculationFromImportResponse:
    content = await file.read()
    try:
        preview = read_erp_file(file.filename or "", content)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    plateformes = load_effective_platforms(db)
    results = _calculate_rows_for_seb(
        rows=list(preview.rows),
        plateformes=plateformes,
        coeff_lent_by_default=coeff_lent,
        pct_lent_by_default=pct_lent,
        pourcentage_lent_by_default=pourcentage_lent,
        db=db,
        buyer=buyer,
    )
    import_anomalies = [
        ImportAnomalySchema(**anomaly.__dict__)
        for anomaly in preview.anomalies
    ]
    run_id = _persist_run_if_requested(
        db,
        persist=persist,
        buyer=buyer,
        results=results,
        extra_logs=[anomaly.model_dump() for anomaly in import_anomalies],
    )

    return CalculationFromImportResponse(
        buyer=buyer,
        filename=file.filename or "",
        source_type=preview.source_type,
        import_row_count=len(preview.rows),
        import_anomalies=import_anomalies,
        results=results,
        run_id=run_id,
    )


@router.post(
    "/seb/from-import-batch/{batch_id}",
    response_model=CalculationFromBatchResponse,
)
def calculate_seb_from_import_batch(
    batch_id: int,
    buyer: str = "Seb",
    coeff_lent: float = 0,
    pct_lent: float | None = None,
    pourcentage_lent: float | None = None,
    persist: bool = False,
    db: Session = Depends(get_db),
) -> CalculationFromBatchResponse:
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch introuvable")

    plateformes = load_effective_platforms(db)
    rows = [erp_row_model_to_domain(row) for row in batch.rows]
    results = _calculate_rows_for_seb(
        rows=rows,
        plateformes=plateformes,
        coeff_lent_by_default=coeff_lent,
        pct_lent_by_default=pct_lent,
        pourcentage_lent_by_default=pourcentage_lent,
        db=db,
        buyer=buyer,
    )
    run_id = _persist_run_if_requested(db, persist=persist, buyer=buyer, results=results)

    return CalculationFromBatchResponse(
        buyer=buyer,
        batch_id=batch.id,
        filename=batch.filename,
        source_type=batch.source_type,
        import_row_count=len(rows),
        results=results,
        run_id=run_id,
    )


@router.get("/runs", response_model=list[CalculationRunSummary])
def get_calculation_runs(db: Session = Depends(get_db)) -> list[CalculationRunSummary]:
    return [_run_summary(run) for run in list_calculation_runs(db)]


@router.get("/runs/{run_id}", response_model=CalculationRunDetail)
def get_calculation_run_detail(
    run_id: int,
    db: Session = Depends(get_db),
) -> CalculationRunDetail:
    run = get_calculation_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run calcul introuvable")

    return CalculationRunDetail(
        **_run_summary(run).model_dump(),
        results=[
            StoredCalculationResultSchema(
                code_article=result.code_article,
                libelle_article=result.libelle_article,
                code_plateforme_erp=result.code_plateforme_erp,
                pf_rapide=result.pf_rapide,
                pf_lente=result.pf_lente,
                besoin_rapide=result.besoin_rapide,
                besoin_lent=result.besoin_lent,
                besoin_total=result.besoin_total,
                consigne_regle=result.consigne_appliquee,
            )
            for result in run.results
        ],
        logs=[
            CalculationLogSchema(
                id=log.id,
                level=log.level,
                message=log.message,
                context_json=log.context_json,
                created_at=log.created_at.isoformat(),
            )
            for log in run.logs
        ],
    )


def _calculate_rows_for_seb(
    *,
    rows: list[ErpRow | dict[str, object]],
    plateformes: list[PlatformParam],
    coeff_lent_by_default: float | None,
    pct_lent_by_default: float | None,
    pourcentage_lent_by_default: float | None,
    db: Session,
    buyer: str,
) -> list[dict[str, object]]:
    results = []
    for row in rows:
        code_article = _row_code_article(row)
        try:
            consigne = _find_saved_consigne(db, buyer=buyer, row=row)
            texte_consigne, valeur_consigne = _consigne_values(row, consigne)
            if isinstance(row, ErpRow):
                result = calculer_besoin_rapide_lent(
                    row,
                    plateformes,
                    texte_consigne=texte_consigne,
                    valeur_consigne=valeur_consigne,
                    coeff_lent=coeff_lent_by_default or 0,
                    pct_lent=pct_lent_by_default,
                    pourcentage_lent=pourcentage_lent_by_default,
                )
            else:
                result = calculer_besoin_rapide_lent(
                    row,
                    plateformes,
                    texte_consigne=texte_consigne,
                    valeur_consigne=valeur_consigne,
                    coeff_lent=float(row.get("coeff_lent", coeff_lent_by_default or 0) or 0),
                    pct_lent=row.get("pct_lent", pct_lent_by_default),
                    pourcentage_lent=row.get("pourcentage_lent", pourcentage_lent_by_default),
                )
        except PlatformNotFoundError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Plateforme ERP invalide pour l'article {code_article}: "
                    f"{exc}"
                ),
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Calcul invalide pour l'article {code_article}: {exc}",
            ) from exc
        results.append(result.as_dict())
    return results


def _find_saved_consigne(
    db: Session,
    *,
    buyer: str,
    row: ErpRow | dict[str, object],
) -> ConsigneModel | None:
    return get_consigne_for_erp_row(
        db,
        acheteur=buyer,
        code_article=_row_code_article(row),
        plateforme_erp=_row_code_plateforme_erp(row),
    )


def _consigne_values(
    row: ErpRow | dict[str, object],
    saved_consigne: ConsigneModel | None,
) -> tuple[str | None, float]:
    if saved_consigne is not None:
        return saved_consigne.texte_consigne, saved_consigne.valeur_consigne
    if isinstance(row, ErpRow):
        return None, 0
    return row.get("texte_consigne"), float(row.get("valeur_consigne", 0) or 0)


def _row_code_article(row: ErpRow | dict[str, object]) -> str:
    if isinstance(row, ErpRow):
        return row.code_article
    return str(row.get("code_article", ""))


def _row_code_plateforme_erp(row: ErpRow | dict[str, object]) -> str:
    if isinstance(row, ErpRow):
        return row.code_plateforme_erp
    return str(row.get("code_plateforme_erp", ""))


def _platforms_from_payload(
    plateformes: list[PlatformParamSchema] | None,
    db: Session,
) -> list[PlatformParam]:
    if plateformes is None:
        return load_effective_platforms(db)
    return [PlatformParam(**platform.model_dump()) for platform in plateformes]


def _persist_run_if_requested(
    db: Session,
    *,
    persist: bool,
    buyer: str,
    results: list[dict[str, object]],
    extra_logs: list[dict[str, object]] | None = None,
) -> int | None:
    if not persist:
        return None
    run = save_calculation_run(
        db,
        buyer=buyer,
        results=results,
        extra_logs=extra_logs,
    )
    return run.id


def _run_summary(run) -> CalculationRunSummary:
    return CalculationRunSummary(
        run_id=run.id,
        buyer=run.buyer,
        created_at=run.created_at.isoformat(),
        status=run.status,
        result_count=len(run.results),
        log_count=len(run.logs),
    )
