from __future__ import annotations

from pydantic import BaseModel, Field


class PlatformParamSchema(BaseModel):
    code_erp: str
    pf_rapide: str | None = None
    pf_lente: str | None = None
    actif: bool = True
    lent_avec_pourcentage: bool = False


class PlatformResolveRequest(BaseModel):
    code_erp: str
    plateformes: list[PlatformParamSchema] | None = None
    inclure_inactives: bool = False


class ConsigneApplyRequest(BaseModel):
    solde_import: float
    texte_consigne: str | None = None
    valeur_consigne: float = 0


class ConsigneApplyResponse(BaseModel):
    solde_corrige: float
    besoin_rapide: float
    surplus_positif: float
    regle: str
    texte_normalise: str
    anomalie: str | None = None


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


class ErpImportRowSchema(BaseModel):
    code_article: str
    libelle_article: str
    code_plateforme_erp: str
    prevision: float = 0
    solde_previsionnel_j1: float = 0


class ImportAnomalySchema(BaseModel):
    row_number: int
    level: str
    message: str
    context: dict[str, object] = Field(default_factory=dict)


class ErpImportPreviewResponse(BaseModel):
    filename: str
    source_type: str
    row_count: int
    rows: list[ErpImportRowSchema]
    anomalies: list[ImportAnomalySchema]


class CalculationFromImportResponse(BaseModel):
    buyer: str
    filename: str
    source_type: str
    import_row_count: int
    import_anomalies: list[ImportAnomalySchema]
    results: list[CalculationResultSchema]


class CamionProjectionRequest(BaseModel):
    jour_depart: str
    camions_depart: float
    nombre_jours: int = 6
    inclure_depart: bool = True


class CamionProjectionRow(BaseModel):
    jour: str
    camions: float
    camions_affichage: int


class CamionProjectionResponse(BaseModel):
    jour_depart: str
    camions_depart: float
    nombre_jours: int
    inclure_depart: bool
    projections: list[CamionProjectionRow]


class LunesCreditRequest(BaseModel):
    pf_lente: str
    commandes_lent_semaine: float
    achats_lent_semaine: float
    taux_lent: float
    lent_lunes_initial: float
    besoin_erp_rapide_brut: float | None = None


class LunesCreditResponse(BaseModel):
    pf_lente: str
    besoin_100: float
    rapide_lunes_final: float
    surplus_lent_semaine: float
    lent_lunes_initial: float
    lent_lunes_final: float
    detail_calcul: str
