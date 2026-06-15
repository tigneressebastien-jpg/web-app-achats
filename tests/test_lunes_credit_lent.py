from __future__ import annotations

from backend.app.services.lunes_service import compute_lunes_credit_from_week_lent


def test_lunes_credit_st_cyr_lent() -> None:
    result = compute_lunes_credit_from_week_lent(
        pf_lente="ST CYR LENT",
        commandes_lent_semaine=163,
        achats_lent_semaine=110,
        taux_lent=1.00,
        lent_lunes_initial=0,
    )

    assert result.pf_lente == "ST CYR LENT"
    assert result.besoin_100 == 163
    assert result.rapide_lunes_final == 53
    assert result.surplus_lent_semaine == 0
    assert result.lent_lunes_initial == 0
    assert result.lent_lunes_final == 0
    assert "besoin_100" in result.detail_calcul


def test_lunes_credit_chapo_lent() -> None:
    result = compute_lunes_credit_from_week_lent(
        pf_lente="CHAPO LENT",
        commandes_lent_semaine=110,
        achats_lent_semaine=110,
        taux_lent=0.50,
        lent_lunes_initial=0,
    )

    assert result.pf_lente == "CHAPO LENT"
    assert result.besoin_100 == 220
    assert result.rapide_lunes_final == 110
    assert result.surplus_lent_semaine == 0
    assert result.lent_lunes_initial == 0
    assert result.lent_lunes_final == 0


def test_lunes_credit_sud_log_lent() -> None:
    result = compute_lunes_credit_from_week_lent(
        pf_lente="SUD LOG LENT",
        commandes_lent_semaine=85,
        achats_lent_semaine=55,
        taux_lent=0.50,
        lent_lunes_initial=0,
    )

    assert result.pf_lente == "SUD LOG LENT"
    assert result.besoin_100 == 170
    assert result.rapide_lunes_final == 115
    assert result.surplus_lent_semaine == 0
    assert result.lent_lunes_initial == 0
    assert result.lent_lunes_final == 0


def test_lunes_credit_surplus_achats_lents_semaine_reduit_lent_lunes() -> None:
    result = compute_lunes_credit_from_week_lent(
        pf_lente="CHAPO LENT",
        commandes_lent_semaine=100,
        achats_lent_semaine=250,
        taux_lent=0.50,
        lent_lunes_initial=80,
    )

    assert result.besoin_100 == 200
    assert result.surplus_lent_semaine == 50
    assert result.rapide_lunes_final == 0
    assert result.lent_lunes_initial == 80
    assert result.lent_lunes_final == 30


def test_lunes_credit_anti_regression_ignore_besoin_erp_rapide_brut() -> None:
    result = compute_lunes_credit_from_week_lent(
        pf_lente="ST CYR LENT",
        commandes_lent_semaine=163,
        achats_lent_semaine=110,
        taux_lent=1.00,
        lent_lunes_initial=0,
        besoin_erp_rapide_brut=71,
    )

    assert result.rapide_lunes_final == 53
    assert result.rapide_lunes_final != 71
    assert "ignored" in result.detail_calcul
