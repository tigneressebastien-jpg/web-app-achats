from __future__ import annotations

from pydantic import BaseModel


class PlatformParamSchema(BaseModel):
    code_erp: str
    pf_rapide: str | None = None
    pf_lente: str | None = None
    actif: bool = True
    lent_avec_pourcentage: bool = False


class CalculationInputRow(BaseModel):
    code_article: str
    libelle_article: str
    code_plateforme_erp: str
    prevision: float = 0
    solde_previsionnel_j1: float = 0
    texte_consigne: str | None = None
    valeur_consigne: float = 0
    coeff_lent: float = 0
    pct_lent: float | None = None
    pourcentage_lent: float | None = None


class CalculationRequest(BaseModel):
    buyer: str = "Seb"
    rows: list[CalculationInputRow]
    plateformes: list[PlatformParamSchema] | None = None


class CalculationResultSchema(BaseModel):
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
    consigne_regle: str | None
    logs: list[str]


class CalculationResponse(BaseModel):
    buyer: str
    results: list[CalculationResultSchema]
