from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Mapping

from app.services.consigne_service import (
    ConsigneApplication,
    appliquer_consigne,
    calculer_besoin_rapide_et_surplus,
)
from app.services.platform_service import PlatformParam, mapper_code_erp_plateformes


@dataclass(frozen=True)
class ErpRow:
    code_article: str
    libelle_article: str
    code_plateforme_erp: str
    prevision: float = 0
    solde_previsionnel_j1: float = 0


@dataclass(frozen=True)
class BesoinResult:
    code_article: str
    libelle_article: str
    code_plateforme_erp: str
    pf_rapide: str | None
    pf_lente: str | None
    solde_corrige: float
    besoin_rapide: float
    besoin_lent: float
    besoin_lent_brut: float
    surplus_positif: float
    besoin_total: float
    consigne_appliquee: ConsigneApplication | None = None
    logs: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "code_article": self.code_article,
            "libelle_article": self.libelle_article,
            "code_plateforme_erp": self.code_plateforme_erp,
            "pf_rapide": self.pf_rapide,
            "pf_lente": self.pf_lente,
            "solde_corrige": self.solde_corrige,
            "besoin_rapide": self.besoin_rapide,
            "besoin_lent": self.besoin_lent,
            "besoin_lent_brut": self.besoin_lent_brut,
            "surplus_positif": self.surplus_positif,
            "besoin_total": self.besoin_total,
            "consigne_regle": (
                self.consigne_appliquee.regle if self.consigne_appliquee else None
            ),
            "logs": list(self.logs),
        }


def calculer_besoin_rapide_lent(
    row_erp: ErpRow | Mapping[str, object],
    plateformes: list[PlatformParam],
    *,
    texte_consigne: str | None = None,
    valeur_consigne: float = 0,
    coeff_lent: float = 0,
    pct_lent: float | None = None,
    pourcentage_lent: float | None = None,
) -> BesoinResult:
    """Calculate a simple rapid/slow need split for one ERP row."""
    row = _coerce_erp_row(row_erp)
    plateforme = mapper_code_erp_plateformes(row.code_plateforme_erp, plateformes)
    solde_import = _to_float(row.solde_previsionnel_j1)
    logs: list[str] = []

    consigne_appliquee: ConsigneApplication | None = None
    if texte_consigne:
        consigne_appliquee = appliquer_consigne(
            solde_import,
            texte_consigne,
            valeur_consigne,
        )
        solde_corrige = consigne_appliquee.solde_corrige
        besoin_rapide = consigne_appliquee.besoin_rapide
        surplus_positif = consigne_appliquee.surplus_positif
        logs.append(
            f"Consigne {consigne_appliquee.regle} appliquee: "
            f"{solde_import} -> {solde_corrige}"
        )
        if consigne_appliquee.anomalie:
            logs.append(consigne_appliquee.anomalie)
    else:
        solde_corrige = solde_import
        besoin_rapide, surplus_positif = calculer_besoin_rapide_et_surplus(solde_corrige)

    ratio_lent = _normaliser_pourcentage(
        pct_lent if pct_lent is not None else pourcentage_lent
    )
    coefficient_lent = _to_float(coeff_lent)
    besoin_lent_brut = calculer_besoin_lent_brut(
        prevision=row.prevision,
        coeff_lent=coefficient_lent,
        lent_avec_pourcentage=plateforme.lent_avec_pourcentage,
        pct_lent=ratio_lent,
        has_pf_lente=plateforme.pf_lente is not None,
    )
    besoin_lent = max(0, besoin_lent_brut - surplus_positif)
    besoin_total = besoin_rapide + besoin_lent

    return BesoinResult(
        code_article=row.code_article,
        libelle_article=row.libelle_article,
        code_plateforme_erp=row.code_plateforme_erp,
        pf_rapide=plateforme.pf_rapide,
        pf_lente=plateforme.pf_lente,
        solde_corrige=solde_corrige,
        besoin_rapide=besoin_rapide,
        besoin_lent=besoin_lent,
        besoin_lent_brut=besoin_lent_brut,
        surplus_positif=surplus_positif,
        besoin_total=besoin_total,
        consigne_appliquee=consigne_appliquee,
        logs=tuple(logs),
    )


def calculer_besoin_import_simple(solde_previsionnel_j1: float | int | str | None) -> float:
    """Convert ERP J+1 balance into a positive need.

    In the V1 validation rules, a negative balance means a shortage to cover.
    Example: I = -1000 gives a need of 1000.
    """
    return max(-_to_float(solde_previsionnel_j1), 0)


def calculer_besoin_lent_brut(
    *,
    prevision: float,
    coeff_lent: float,
    lent_avec_pourcentage: bool,
    pct_lent: float,
    has_pf_lente: bool = True,
) -> float:
    if not has_pf_lente or coeff_lent <= 0:
        return 0.0
    besoin_lent = _to_float(prevision) * coeff_lent
    if lent_avec_pourcentage:
        besoin_lent *= pct_lent
    return besoin_lent


def _coerce_erp_row(row: ErpRow | Mapping[str, object]) -> ErpRow:
    if isinstance(row, ErpRow):
        return row
    return ErpRow(
        code_article=str(_first(row, "code_article", "Code article", "C") or ""),
        libelle_article=str(_first(row, "libelle_article", "Libelle article", "D") or ""),
        code_plateforme_erp=str(
            _first(row, "code_plateforme_erp", "Plateforme ERP", "F") or ""
        ),
        prevision=_to_float(_first(row, "prevision", "Prevision", "G")),
        solde_previsionnel_j1=_to_float(
            _first(row, "solde_previsionnel_j1", "Solde previsionnel J+1", "I")
        ),
    )


def _first(row: Mapping[str, object], *keys: str) -> object | None:
    normalized = {_normaliser_key(str(key)): value for key, value in row.items()}
    for key in keys:
        value = normalized.get(_normaliser_key(key))
        if value is not None:
            return value
    return None


def _normaliser_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _normaliser_pourcentage(value: float | int | str | None) -> float:
    ratio = _to_float(value)
    if ratio < 0:
        raise ValueError("Le pourcentage lent ne peut pas etre negatif")
    if ratio > 1:
        ratio = ratio / 100
    if ratio > 1:
        raise ValueError("Le pourcentage lent ne peut pas depasser 100%")
    return ratio


def _to_float(value: float | int | str | None) -> float:
    if value is None or value == "":
        return 0
    return float(str(value).replace(",", "."))
