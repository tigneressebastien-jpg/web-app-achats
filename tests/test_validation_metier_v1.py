from __future__ import annotations

import pytest

from app.services.besoin_service import ErpRow, calculer_besoin_rapide_lent
from app.services.camion_service import calculer_projection_camions
from app.services.consigne_service import appliquer_consigne
from app.services.platform_service import (
    PlatformNotFoundError,
    lire_plateformes_dynamiques,
    mapper_code_erp_plateformes,
)


COEFF_LENT = 0.894
PCT_LENT = 0.30


@pytest.mark.parametrize(
    ("code_erp", "pf_rapide", "pf_lente", "lent_avec_pourcentage"),
    [
        ("2C1", None, "2C LOG", False),
        ("CHA", "CHAPO", "CHAPO LENT", True),
        ("SCY", "ST CYR", "ST CYR LENT", False),
        ("NME", "SUD LOG", "SUD LOG LENT", True),
        ("SMT", "SAMATERRA", "SAMATERRA LENT", True),
        ("TLS", "TOULOUSE", "TOULOUSE LENT", True),
    ],
)
def test_validation_mapping_plateformes_dynamiques(
    code_erp: str,
    pf_rapide: str | None,
    pf_lente: str | None,
    lent_avec_pourcentage: bool,
) -> None:
    plateformes = lire_plateformes_dynamiques()

    plateforme = mapper_code_erp_plateformes(code_erp, plateformes)

    assert plateforme.pf_rapide == pf_rapide
    assert plateforme.pf_lente == pf_lente
    assert plateforme.lent_avec_pourcentage is lent_avec_pourcentage


def test_validation_mapping_code_inconnu_ne_fallback_pas() -> None:
    plateformes = lire_plateformes_dynamiques()

    with pytest.raises(PlatformNotFoundError):
        mapper_code_erp_plateformes("XXX", plateformes)


@pytest.mark.parametrize(
    ("prevision", "solde_import", "besoin_rapide", "surplus_positif"),
    [
        (1155, -1000, 1000, 0),
        (34, 93, 0, 93),
        (100, 0, 0, 0),
    ],
)
def test_validation_besoin_rapide_simple_sans_consigne(
    prevision: float,
    solde_import: float,
    besoin_rapide: float,
    surplus_positif: float,
) -> None:
    result = _calculer("SMT", prevision, solde_import)

    assert result.solde_corrige == solde_import
    assert result.besoin_rapide == besoin_rapide
    assert result.surplus_positif == surplus_positif


@pytest.mark.parametrize(
    (
        "solde_import",
        "valeur_consigne",
        "texte_consigne",
        "solde_corrige",
        "besoin_rapide",
        "surplus_positif",
        "regle",
    ),
    [
        (-369, 50, "+60 stock", -359, 359, 0, "AJOUT_STOCK"),
        (-146, -32, "+150 stock", 36, 0, 36, "AJOUT_STOCK"),
        (-369, 50, "AZ", -419, 419, 0, "AZ"),
        (-369, 50, "+20 AZ", -419, 419, 0, "AZ"),
        (-369, 50, "TRANSFERT +20 AZ", -419, 419, 0, "AZ"),
        (-369, -161, "TRANSFERT +10 STOCK", -151, 151, 0, "TRANSFERT_STOCK"),
        (-428, -19, "-19 que ca", -428, 428, 0, "QUE_CA"),
        (-250, 100, "OK", -250, 250, 0, "CONSIGNE_NEUTRE"),
    ],
)
def test_validation_consignes_erp(
    solde_import: float,
    valeur_consigne: float,
    texte_consigne: str,
    solde_corrige: float,
    besoin_rapide: float,
    surplus_positif: float,
    regle: str,
) -> None:
    result = appliquer_consigne(solde_import, texte_consigne, valeur_consigne)

    assert result.solde_corrige == solde_corrige
    assert result.besoin_rapide == besoin_rapide
    assert result.surplus_positif == surplus_positif
    assert result.regle == regle


def test_validation_chapo_lent_avec_pourcentage() -> None:
    result = _calculer("CHA", 100, -20, coeff_lent=COEFF_LENT, pct_lent=PCT_LENT)

    assert result.pf_rapide == "CHAPO"
    assert result.pf_lente == "CHAPO LENT"
    assert result.besoin_rapide == 20
    assert result.surplus_positif == 0
    assert result.besoin_lent_brut == pytest.approx(26.82)
    assert result.besoin_lent == pytest.approx(26.82)


def test_validation_st_cyr_lent_sans_pourcentage_avec_surplus() -> None:
    result = _calculer("SCY", 100, 30, coeff_lent=COEFF_LENT, pct_lent=PCT_LENT)

    assert result.pf_rapide == "ST CYR"
    assert result.pf_lente == "ST CYR LENT"
    assert result.besoin_rapide == 0
    assert result.surplus_positif == 30
    assert result.besoin_lent_brut == pytest.approx(89.4)
    assert result.besoin_lent == pytest.approx(59.4)


def test_validation_2c1_surplus_annule_le_lent() -> None:
    result = _calculer("2C1", 34, 93, coeff_lent=COEFF_LENT, pct_lent=PCT_LENT)

    assert result.pf_rapide is None
    assert result.pf_lente == "2C LOG"
    assert result.besoin_rapide == 0
    assert result.surplus_positif == 93
    assert result.besoin_lent_brut == pytest.approx(30.396)
    assert result.besoin_lent == 0


def test_validation_samaterra_lent_dynamique() -> None:
    result = _calculer("SMT", 1155, -1000, coeff_lent=COEFF_LENT, pct_lent=PCT_LENT)

    assert result.pf_rapide == "SAMATERRA"
    assert result.pf_lente == "SAMATERRA LENT"
    assert result.besoin_rapide == 1000
    assert result.surplus_positif == 0
    assert result.besoin_lent_brut == pytest.approx(309.771)
    assert result.besoin_lent == pytest.approx(309.771)


def test_validation_consigne_stock_surplus_reduit_le_lent() -> None:
    result = _calculer(
        "CHA",
        596,
        -146,
        texte_consigne="+150 stock",
        valeur_consigne=-32,
        coeff_lent=COEFF_LENT,
        pct_lent=PCT_LENT,
    )

    assert result.pf_rapide == "CHAPO"
    assert result.pf_lente == "CHAPO LENT"
    assert result.solde_corrige == 36
    assert result.besoin_rapide == 0
    assert result.surplus_positif == 36
    assert result.besoin_lent_brut == pytest.approx(159.8712)
    assert result.besoin_lent == pytest.approx(123.8712)


def test_validation_camions_samedi_40_semaine_glissante() -> None:
    projections = calculer_projection_camions(
        jour_depart="samedi",
        camions_depart=40,
        nombre_jours=5,
        inclure_depart=True,
    )

    assert [projection.jour for projection in projections] == [
        "samedi",
        "lundi",
        "mardi",
        "mercredi",
        "jeudi",
        "vendredi",
    ]
    assert [projection.camions for projection in projections] == pytest.approx(
        [40, 35.76, 30.0384, 28.085904, 41.202021168, 50.101657740288]
    )
    assert [projection.camions_affichage for projection in projections] == [
        40,
        36,
        31,
        29,
        42,
        51,
    ]


def test_validation_camions_vendredi_40_semaine_glissante() -> None:
    projections = calculer_projection_camions(
        jour_depart="vendredi",
        camions_depart=40,
        nombre_jours=6,
        inclure_depart=True,
    )

    assert [projection.jour for projection in projections] == [
        "vendredi",
        "samedi",
        "lundi",
        "mardi",
        "mercredi",
        "jeudi",
        "vendredi",
    ]
    assert [projection.camions for projection in projections] == pytest.approx(
        [
            40,
            26.56,
            23.74464,
            19.9454976,
            18.649040256,
            27.358142055552,
            33.267500739551232,
        ]
    )
    assert [projection.camions_affichage for projection in projections] == [
        40,
        27,
        24,
        20,
        19,
        28,
        34,
    ]


def test_validation_camions_anti_arrondi_intermediaire() -> None:
    projections = calculer_projection_camions(
        jour_depart="samedi",
        camions_depart=40,
        nombre_jours=2,
        inclure_depart=False,
    )

    lundi = projections[0]
    mardi = projections[1]

    assert lundi.camions == pytest.approx(35.76)
    assert mardi.camions == pytest.approx(30.0384)
    assert mardi.camions == pytest.approx(lundi.camions * 0.840)
    assert mardi.camions != pytest.approx(36 * 0.840)


def _calculer(
    code_erp: str,
    prevision: float,
    solde_import: float,
    *,
    texte_consigne: str | None = None,
    valeur_consigne: float = 0,
    coeff_lent: float = 0,
    pct_lent: float | None = None,
):
    plateformes = lire_plateformes_dynamiques()
    row = ErpRow(
        code_article=f"ART-{code_erp}",
        libelle_article=f"Article test {code_erp}",
        code_plateforme_erp=code_erp,
        prevision=prevision,
        solde_previsionnel_j1=solde_import,
    )
    return calculer_besoin_rapide_lent(
        row,
        plateformes,
        texte_consigne=texte_consigne,
        valeur_consigne=valeur_consigne,
        coeff_lent=coeff_lent,
        pct_lent=pct_lent,
    )
