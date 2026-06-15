from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ConsigneApplication:
    solde_corrige: float
    besoin_rapide: float
    surplus_positif: float
    regle: str
    texte_normalise: str
    anomalie: str | None = None

    @property
    def besoin(self) -> float:
        """Backward-compatible alias for the rapid need."""
        return self.besoin_rapide


def appliquer_consigne(
    solde_import: float,
    texte_consigne: str | None,
    valeur_consigne: float = 0,
) -> ConsigneApplication:
    """Apply the V1 consigne rules to an ERP balance.

    The rules work on the ERP balance, not directly on a positive need:
    negative balance => shortage, positive balance => surplus.
    """
    solde_import = _to_float(solde_import)
    valeur_consigne = _to_float(valeur_consigne)
    texte_normalise = normaliser_consigne(texte_consigne)

    if not texte_normalise:
        return _result(solde_import, "AUCUNE_CONSIGNE", texte_normalise)

    if texte_normalise in {"OK", "TRANSFERT OK"}:
        return _result(solde_import, "CONSIGNE_NEUTRE", texte_normalise)

    if re.search(r"\bQUE\s+CA\b", texte_normalise):
        return _result(solde_import, "QUE_CA", texte_normalise)

    transfert_stock = re.fullmatch(
        r"TRANSFERT\s+\+?\s*(?P<quantite>-?\d+(?:[.,]\d+)?)\s+STOCK",
        texte_normalise,
    )
    if transfert_stock:
        quantite = _parse_number(transfert_stock.group("quantite"))
        solde_corrige = valeur_consigne + quantite
        return _result(solde_corrige, "TRANSFERT_STOCK", texte_normalise)

    if re.fullmatch(r"(?:TRANSFERT\s+)?(?:\+?\s*-?\d+(?:[.,]\d+)?\s+)?AZ", texte_normalise):
        solde_corrige = solde_import - valeur_consigne
        return _result(solde_corrige, "AZ", texte_normalise)

    stock = re.fullmatch(
        r"\+?\s*(?P<quantite>-?\d+(?:[.,]\d+)?)\s+STOCK",
        texte_normalise,
    )
    if stock:
        quantite = _parse_number(stock.group("quantite"))
        solde_corrige = solde_import + (quantite - valeur_consigne)
        return _result(solde_corrige, "AJOUT_STOCK", texte_normalise)

    return _result(
        solde_import,
        "CONSIGNE_INCONNUE",
        texte_normalise,
        anomalie=f"Consigne non reconnue: {texte_consigne}",
    )


def normaliser_consigne(texte_consigne: str | None) -> str:
    if texte_consigne is None:
        return ""
    without_accents = unicodedata.normalize("NFKD", str(texte_consigne))
    without_accents = "".join(
        char for char in without_accents if not unicodedata.combining(char)
    )
    return " ".join(without_accents.upper().split())


def calculer_besoin_rapide_et_surplus(solde_corrige: float) -> tuple[float, float]:
    solde = _to_float(solde_corrige)
    return max(-solde, 0), max(solde, 0)


def _result(
    solde_corrige: float,
    regle: str,
    texte_normalise: str,
    anomalie: str | None = None,
) -> ConsigneApplication:
    besoin_rapide, surplus_positif = calculer_besoin_rapide_et_surplus(solde_corrige)
    return ConsigneApplication(
        solde_corrige=solde_corrige,
        besoin_rapide=besoin_rapide,
        surplus_positif=surplus_positif,
        regle=regle,
        texte_normalise=texte_normalise,
        anomalie=anomalie,
    )


def _parse_number(value: str) -> float:
    return float(str(value).replace(",", "."))


def _to_float(value: float | int | str | None) -> float:
    if value is None or value == "":
        return 0
    return float(str(value).replace(",", "."))
