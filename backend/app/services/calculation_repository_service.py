from __future__ import annotations

import json
from typing import Mapping

from app.models import (
    CalculationLogModel,
    CalculationResultModel,
    CalculationRunModel,
)
from sqlalchemy.orm import Session


def save_calculation_run(
    db: Session,
    *,
    buyer: str,
    results: list[Mapping[str, object]],
    extra_logs: list[Mapping[str, object]] | None = None,
    status: str = "completed",
) -> CalculationRunModel:
    run = CalculationRunModel(buyer=buyer, status=status)
    db.add(run)
    db.flush()

    for result in results:
        db.add(
            CalculationResultModel(
                run_id=run.id,
                code_article=str(result.get("code_article", "")),
                libelle_article=str(result.get("libelle_article", "")),
                code_plateforme_erp=str(result.get("code_plateforme_erp", "")),
                pf_rapide=_optional_str(result.get("pf_rapide")),
                pf_lente=_optional_str(result.get("pf_lente")),
                besoin_rapide=_to_float(result.get("besoin_rapide")),
                besoin_lent=_to_float(result.get("besoin_lent")),
                besoin_total=_to_float(result.get("besoin_total")),
                consigne_appliquee=_optional_str(result.get("consigne_regle")),
            )
        )
        for message in result.get("logs", []) or []:
            db.add(
                CalculationLogModel(
                    run_id=run.id,
                    level="INFO",
                    message=str(message),
                    context_json=json.dumps(
                        {"code_article": result.get("code_article")},
                        ensure_ascii=True,
                    ),
                )
            )

    db.add(
        CalculationLogModel(
            run_id=run.id,
            level="INFO",
            message=f"Run calcul termine: {len(results)} resultat(s)",
            context_json=None,
        )
    )

    for extra_log in extra_logs or []:
        db.add(
            CalculationLogModel(
                run_id=run.id,
                level=str(extra_log.get("level", "INFO")),
                message=str(extra_log.get("message", "")),
                context_json=json.dumps(
                    extra_log.get("context", {}),
                    ensure_ascii=True,
                ),
            )
        )

    db.commit()
    db.refresh(run)
    return run


def list_calculation_runs(db: Session) -> list[CalculationRunModel]:
    return (
        db.query(CalculationRunModel)
        .order_by(CalculationRunModel.created_at.desc(), CalculationRunModel.id.desc())
        .all()
    )


def get_calculation_run(db: Session, run_id: int) -> CalculationRunModel | None:
    return (
        db.query(CalculationRunModel)
        .filter(CalculationRunModel.id == run_id)
        .one_or_none()
    )


def _optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _to_float(value: object | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)
