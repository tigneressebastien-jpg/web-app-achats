from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import PlatformParamModel
from app.services.platform_service import PlatformParam, lire_plateformes_dynamiques


def model_to_platform_param(row: PlatformParamModel) -> PlatformParam:
    return PlatformParam(
        code_erp=row.code_erp,
        pf_rapide=row.pf_rapide,
        pf_lente=row.pf_lente,
        actif=row.actif,
        lent_avec_pourcentage=row.lent_avec_pourcentage,
    )


def load_effective_platforms(db: Session) -> list[PlatformParam]:
    """Return default platform settings overridden by saved SQLite settings."""
    platforms_by_code = {
        platform.code_erp.upper(): platform
        for platform in lire_plateformes_dynamiques()
    }

    saved_rows = db.query(PlatformParamModel).all()
    for row in saved_rows:
        platforms_by_code[row.code_erp.upper()] = model_to_platform_param(row)

    return sorted(platforms_by_code.values(), key=lambda platform: platform.code_erp)
