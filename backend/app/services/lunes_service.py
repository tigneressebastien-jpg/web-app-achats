from __future__ import annotations

from dataclasses import dataclass


PF_LENTES_LUNES_TAUX_100 = {"ST CYR LENT"}
PF_LENTES_LUNES_TAUX_PCT = {"CHAPO LENT", "SUD LOG LENT"}


@dataclass(frozen=True)
class LunesCreditResult:
    pf_lente: str
    besoin_100: float
    rapide_lunes_final: float
    surplus_lent_semaine: float
    lent_lunes_initial: float
    lent_lunes_final: float
    detail_calcul: str

    @property
    def rapide_lunes(self) -> float:
        return self.rapide_lunes_final

    @property
    def surplus(self) -> float:
        return self.surplus_lent_semaine


def compute_lunes_credit_from_week_lent(
    *,
    pf_lente: str,
    commandes_lent_semaine: float | int | str | None,
    achats_lent_semaine: float | int | str | None,
    taux_lent: float | int | str | None,
    lent_lunes_initial: float | int | str | None,
    besoin_erp_rapide_brut: float | int | str | None = None,
) -> LunesCreditResult:
    """Compute final Lunes fast need from week slow credit.

    `besoin_erp_rapide_brut` is accepted for traceability but deliberately not
    used in this validated rule.
    """
    commandes_lent = _to_float(commandes_lent_semaine)
    achats_lent = _to_float(achats_lent_semaine)
    taux = normalize_taux_lent(taux_lent)
    lent_initial = _to_float(lent_lunes_initial)

    besoin_100 = commandes_lent / taux
    rapide_lunes_final = max(0, besoin_100 - achats_lent)
    surplus_lent_semaine = max(0, achats_lent - besoin_100)
    lent_lunes_final = max(0, lent_initial - surplus_lent_semaine)

    detail_calcul = (
        f"besoin_100={commandes_lent}/{taux}; "
        f"rapide_lunes_final=max(0,{besoin_100}-{achats_lent}); "
        f"surplus_lent_semaine=max(0,{achats_lent}-{besoin_100}); "
        f"lent_lunes_final=max(0,{lent_initial}-{surplus_lent_semaine}); "
        "besoin_erp_rapide_brut ignored"
    )

    return LunesCreditResult(
        pf_lente=pf_lente,
        besoin_100=besoin_100,
        rapide_lunes_final=rapide_lunes_final,
        surplus_lent_semaine=surplus_lent_semaine,
        lent_lunes_initial=lent_initial,
        lent_lunes_final=lent_lunes_final,
        detail_calcul=detail_calcul,
    )


def normalize_taux_lent(taux_lent: float | int | str | None) -> float:
    taux = _to_float(taux_lent)
    if taux <= 0:
        raise ValueError("Le taux_lent doit etre strictement positif")
    if taux > 1:
        taux = taux / 100
    if taux <= 0:
        raise ValueError("Le taux_lent doit etre strictement positif")
    return taux


def resolve_lunes_taux_lent_for_platform(
    pf_lente: str,
    *,
    pct_lent: float | int | str | None,
    taux_lent_parametre: float | int | str | None = None,
) -> float:
    """Resolve the validated Lunes slow-rate by slow platform."""
    if taux_lent_parametre not in (None, ""):
        return normalize_taux_lent(taux_lent_parametre)

    plateforme = _normaliser_pf(pf_lente)
    if plateforme in PF_LENTES_LUNES_TAUX_100:
        return 1.0
    if plateforme in PF_LENTES_LUNES_TAUX_PCT:
        return normalize_taux_lent(pct_lent)

    raise ValueError(
        f"Taux lent Lunes non parametre pour la plateforme lente: {pf_lente}"
    )


def calculate_lunes_fast_for_platform(
    *,
    pf_lente: str,
    commandes_lent_semaine: float | int | str | None,
    achats_lent_semaine: float | int | str | None,
    pct_lent: float | int | str | None,
    taux_lent_parametre: float | int | str | None = None,
    lent_lunes_initial: float | int | str | None = 0,
    besoin_erp_rapide_brut: float | int | str | None = None,
) -> LunesCreditResult:
    taux_lent = resolve_lunes_taux_lent_for_platform(
        pf_lente,
        pct_lent=pct_lent,
        taux_lent_parametre=taux_lent_parametre,
    )
    return compute_lunes_credit_from_week_lent(
        pf_lente=pf_lente,
        commandes_lent_semaine=commandes_lent_semaine,
        achats_lent_semaine=achats_lent_semaine,
        taux_lent=taux_lent,
        lent_lunes_initial=lent_lunes_initial,
        besoin_erp_rapide_brut=besoin_erp_rapide_brut,
    )


def calculate_lunes_fast_from_week_slow(
    commandes_lent_semaine: float | int | str | None,
    achats_lent_semaine: float | int | str | None,
    taux_lent: float | int | str | None,
) -> LunesCreditResult:
    return compute_lunes_credit_from_week_lent(
        pf_lente="",
        commandes_lent_semaine=commandes_lent_semaine,
        achats_lent_semaine=achats_lent_semaine,
        taux_lent=taux_lent,
        lent_lunes_initial=0,
    )


def calculer_rapide_lunes_depuis_lent_semaine(
    commandes_lent_semaine: float | int | str | None,
    achats_lent_semaine: float | int | str | None,
    taux_lent: float | int | str | None,
) -> LunesCreditResult:
    return calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine,
        achats_lent_semaine,
        taux_lent,
    )


def _normaliser_pf(value: object) -> str:
    return str(value).strip().upper()


def _to_float(value: float | int | str | None) -> float:
    if value is None or value == "":
        return 0
    return float(str(value).replace(",", "."))
