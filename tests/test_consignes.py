from __future__ import annotations

from app.services.consigne_service import appliquer_consigne


def test_consigne_ajout_stock_applique_la_formule_import_plus_ecart_stock() -> None:
    result = appliquer_consigne(
        solde_import=-369,
        texte_consigne="+60 stock",
        valeur_consigne=50,
    )

    assert result.solde_corrige == -359
    assert result.besoin_rapide == 359
    assert result.regle == "AJOUT_STOCK"


def test_consigne_az_retranche_la_valeur_consigne() -> None:
    result = appliquer_consigne(
        solde_import=-369,
        texte_consigne="TRANSFERT +5 AZ",
        valeur_consigne=50,
    )

    assert result.solde_corrige == -419
    assert result.besoin_rapide == 419
    assert result.regle == "AZ"


def test_consigne_transfert_stock_part_de_la_consigne() -> None:
    result = appliquer_consigne(
        solde_import=-369,
        texte_consigne="TRANSFERT +10 STOCK",
        valeur_consigne=-161,
    )

    assert result.solde_corrige == -151
    assert result.besoin_rapide == 151
    assert result.regle == "TRANSFERT_STOCK"


def test_consigne_que_ca_garde_le_besoin_import_inchange() -> None:
    result = appliquer_consigne(
        solde_import=-428,
        texte_consigne="-19 que ca",
        valeur_consigne=-19,
    )

    assert result.solde_corrige == -428
    assert result.besoin_rapide == 428
    assert result.regle == "QUE_CA"


def test_consigne_ok_est_neutre() -> None:
    result = appliquer_consigne(
        solde_import=-250,
        texte_consigne="TRANSFERT OK",
        valeur_consigne=100,
    )

    assert result.solde_corrige == -250
    assert result.besoin_rapide == 250
    assert result.regle == "CONSIGNE_NEUTRE"


def test_consigne_stock_peut_creer_un_surplus_positif() -> None:
    result = appliquer_consigne(
        solde_import=-146,
        texte_consigne="+150 stock",
        valeur_consigne=-32,
    )

    assert result.solde_corrige == 36
    assert result.besoin_rapide == 0
    assert result.surplus_positif == 36
