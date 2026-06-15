from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from app.seed.default_platforms import DEFAULT_PLATFORM_ROWS


@dataclass(frozen=True)
class PlatformParam:
    code_erp: str
    pf_rapide: str | None
    pf_lente: str | None = None
    actif: bool = True
    lent_avec_pourcentage: bool = False


class PlatformNotFoundError(ValueError):
    """Raised when an ERP platform code is missing from dynamic parameters."""


_FIELD_ALIASES = {
    "code_erp": ("code_erp", "code erp", "code plateforme", "plateforme erp"),
    "pf_rapide": ("pf_rapide", "pf rapide", "plateforme rapide", "rapide"),
    "pf_lente": ("pf_lente", "pf lente", "plateforme lente", "lente"),
    "actif": ("actif", "active"),
    "lent_avec_pourcentage": (
        "lent_avec_pourcentage",
        "lent avec %",
        "lent avec pourcentage",
        "lente avec %",
    ),
}


def lire_plateformes_dynamiques(
    source: str | Path | Iterable[Mapping[str, object]] | None = None,
) -> list[PlatformParam]:
    """Read dynamic platform parameters from rows, CSV, Excel, or defaults."""
    if source is None:
        return _normaliser_lignes(DEFAULT_PLATFORM_ROWS)

    if isinstance(source, (str, Path)):
        path = Path(source)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return _normaliser_lignes(csv.DictReader(handle))
        if suffix in {".xlsx", ".xlsm", ".xls"}:
            return _read_excel_platforms(path)
        raise ValueError(f"Format plateformes non supporte: {suffix}")

    return _normaliser_lignes(source)


def mapper_code_erp_plateformes(
    code_erp: str,
    plateformes: Iterable[PlatformParam],
    *,
    inclure_inactives: bool = False,
) -> PlatformParam:
    """Map an ERP code to its rapid/slow platform parameter row."""
    normalized_code = _normaliser_code(code_erp)
    for plateforme in plateformes:
        if _normaliser_code(plateforme.code_erp) != normalized_code:
            continue
        if plateforme.actif or inclure_inactives:
            return plateforme
        raise PlatformNotFoundError(f"Plateforme ERP inactive: {code_erp}")
    raise PlatformNotFoundError(f"Code ERP plateforme inconnu: {code_erp}")


def _read_excel_platforms(path: Path) -> list[PlatformParam]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas est requis pour lire les plateformes depuis Excel"
        ) from exc

    frame = pd.read_excel(path)
    return _normaliser_lignes(frame.to_dict(orient="records"))


def _normaliser_lignes(rows: Iterable[Mapping[str, object]]) -> list[PlatformParam]:
    plateformes: list[PlatformParam] = []
    for row in rows:
        plateformes.append(
            PlatformParam(
                code_erp=_get_required(row, "code_erp").upper(),
                pf_rapide=_clean_optional(_get_optional(row, "pf_rapide")),
                pf_lente=_clean_optional(_get_optional(row, "pf_lente")),
                actif=_to_bool(_get_optional(row, "actif"), default=True),
                lent_avec_pourcentage=_to_bool(
                    _get_optional(row, "lent_avec_pourcentage"), default=False
                ),
            )
        )
    return plateformes


def _get_required(row: Mapping[str, object], field: str) -> str:
    value = _get_optional(row, field)
    cleaned = _clean_optional(value)
    if cleaned is None:
        raise ValueError(f"Champ plateformes obligatoire manquant: {field}")
    return cleaned


def _get_optional(row: Mapping[str, object], field: str) -> object | None:
    normalized_row = {str(key).strip().lower(): value for key, value in row.items()}
    for alias in _FIELD_ALIASES[field]:
        if alias in normalized_row:
            return normalized_row[alias]
    return None


def _clean_optional(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    return text


def _to_bool(value: object | None, *, default: bool) -> bool:
    cleaned = _clean_optional(value)
    if cleaned is None:
        return default
    return cleaned.strip().lower() in {"1", "true", "vrai", "oui", "yes", "y", "x"}


def _normaliser_code(code: str) -> str:
    return str(code).strip().upper()
