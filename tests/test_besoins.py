from __future__ import annotations

import pytest

from app.services.besoin_service import ErpRow, calculer_besoin_rapide_lent
from app.services.platform_service import lire_plateformes_dynamiques


def test_besoin_rapide_solde_negatif_devient_abs_solde() -> None:
    plateformes = lire_plateformes_dynamiques()
    row = ErpRow(
        code_article="ART001",
        libelle_article="Article negatif",
        code_plateforme_erp="SMT",
        prevision=1155,
        solde_previsionnel_j1=-1000,
    )

    result = calculer_besoin_rapide_lent(row, plateformes)

    assert result.pf_rapide == "SAMATERRA"
    assert result.pf_lente == "SAMATERRA LENT"
    assert result.solde_corrige == -1000
    assert result.besoin_rapide == 1000
    assert result.surplus_positif == 0
    assert result.besoin_lent == 0


def test_besoin_rapide_solde_positif_devient_surplus() -> None:
    plateformes = lire_plateformes_dynamiques()
    row = ErpRow(
        code_article="ART002",
        libelle_article="Article positif",
        code_plateforme_erp="SMT",
        prevision=34,
        solde_previsionnel_j1=93,
    )

    result = calculer_besoin_rapide_lent(row, plateformes)

    assert result.solde_corrige == 93
    assert result.besoin_rapide == 0
    assert result.surplus_positif == 93


def test_besoin_lent_chapo_avec_pourcentage() -> None:
    plateformes = lire_plateformes_dynamiques()
    row = ErpRow(
        code_article="ART003",
        libelle_article="Courgette",
        code_plateforme_erp="CHA",
        prevision=100,
        solde_previsionnel_j1=-20,
    )

    result = calculer_besoin_rapide_lent(
        row,
        plateformes,
        coeff_lent=0.894,
        pct_lent=0.30,
    )

    assert result.pf_rapide == "CHAPO"
    assert result.pf_lente == "CHAPO LENT"
    assert result.besoin_rapide == 20
    assert result.besoin_lent_brut == pytest.approx(26.82)
    assert result.besoin_lent == pytest.approx(26.82)


def test_besoin_lent_scy_sans_pourcentage_reduit_par_surplus() -> None:
    plateformes = lire_plateformes_dynamiques()
    row = ErpRow(
        code_article="ART004",
        libelle_article="Aubergine",
        code_plateforme_erp="SCY",
        prevision=100,
        solde_previsionnel_j1=30,
    )

    result = calculer_besoin_rapide_lent(
        row,
        plateformes,
        coeff_lent=0.894,
        pct_lent=0.30,
    )

    assert result.besoin_rapide == 0
    assert result.surplus_positif == 30
    assert result.besoin_lent_brut == pytest.approx(89.4)
    assert result.besoin_lent == pytest.approx(59.4)


def test_consigne_est_appliquee_avant_le_besoin_lent() -> None:
    plateformes = lire_plateformes_dynamiques()
    row = ErpRow(
        code_article="ART005",
        libelle_article="Poivron rouge",
        code_plateforme_erp="CHA",
        prevision=596,
        solde_previsionnel_j1=-146,
    )

    result = calculer_besoin_rapide_lent(
        row,
        plateformes,
        texte_consigne="+150 stock",
        valeur_consigne=-32,
        coeff_lent=0.894,
        pct_lent=0.30,
    )

    assert result.solde_corrige == 36
    assert result.besoin_rapide == 0
    assert result.surplus_positif == 36
    assert result.besoin_lent_brut == pytest.approx(159.8712)
    assert result.besoin_lent == pytest.approx(123.8712)
