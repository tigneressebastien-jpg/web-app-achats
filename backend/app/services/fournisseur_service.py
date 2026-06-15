from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RemplissageFournisseur:
    plateforme: str
    quantite: float
    pas_utilise: float
    raison: str


def choisir_pas_remplissage(
    *,
    palettisation: float | int | str | None,
    pas_colis: float | int | str | None = None,
) -> float:
    """Use PAS_COLIS when provided, otherwise fall back to palettisation."""
    pas_prioritaire = _to_float(pas_colis)
    if pas_prioritaire > 0:
        return pas_prioritaire
    return _to_float(palettisation)


def calculer_remplissage_fournisseur(
    *,
    plateforme: str,
    commandes: float | int | str | None,
    besoin: float | int | str | None,
    palettisation: float | int | str | None,
    pas_colis: float | int | str | None = None,
    pf_interdite: str | list[str] | tuple[str, ...] | None = None,
    arrondi: str = "sans_depasser",
) -> RemplissageFournisseur:
    pas_utilise = choisir_pas_remplissage(
        palettisation=palettisation,
        pas_colis=pas_colis,
    )
    plateforme_norm = _normaliser_pf(plateforme)

    if _to_float(commandes) <= 0:
        return RemplissageFournisseur(plateforme, 0, pas_utilise, "COMMANDES_ZERO")

    if plateforme_norm in _normaliser_pf_interdites(pf_interdite):
        return RemplissageFournisseur(plateforme, 0, pas_utilise, "PF_INTERDITE")

    besoin_a_servir = min(_to_float(commandes), _to_float(besoin))
    if besoin_a_servir <= 0 or pas_utilise <= 0:
        return RemplissageFournisseur(plateforme, 0, pas_utilise, "AUCUN_BESOIN")

    if arrondi == "sans_depasser":
        quantite = math.floor(besoin_a_servir / pas_utilise) * pas_utilise
    elif arrondi == "au_superieur":
        quantite = math.ceil(besoin_a_servir / pas_utilise) * pas_utilise
    else:
        raise ValueError(f"Strategie d'arrondi inconnue: {arrondi}")

    return RemplissageFournisseur(plateforme, quantite, pas_utilise, "OK")


def _normaliser_pf_interdites(
    pf_interdite: str | list[str] | tuple[str, ...] | None,
) -> set[str]:
    if pf_interdite is None:
        return set()
    if isinstance(pf_interdite, str):
        raw_values = pf_interdite.replace(";", ",").split(",")
    else:
        raw_values = list(pf_interdite)
    return {_normaliser_pf(value) for value in raw_values if str(value).strip()}


def _normaliser_pf(value: object) -> str:
    return str(value).strip().upper()


def _to_float(value: float | int | str | None) -> float:
    if value is None or value == "":
        return 0
    return float(str(value).replace(",", "."))

