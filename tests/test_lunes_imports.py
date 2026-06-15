from __future__ import annotations

import pytest

from app.services.lunes_service import (
    calculate_lunes_fast_for_platform,
    calculate_lunes_fast_from_week_slow,
    compute_lunes_credit_from_week_lent,
    resolve_lunes_taux_lent_for_platform,
)


def test_lunes_st_cyr_lent_taux_100_pourcent() -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=163,
        achats_lent_semaine=110,
        taux_lent=1.00,
    )

    assert result.besoin_100 == 163
    assert result.rapide_lunes == 53
    assert result.surplus == 0


def test_lunes_chapo_lent_taux_50_pourcent() -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=110,
        achats_lent_semaine=110,
        taux_lent=0.50,
    )

    assert result.besoin_100 == 220
    assert result.rapide_lunes == 110
    assert result.surplus == 0


def test_lunes_sud_log_lent_taux_50_pourcent() -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=85,
        achats_lent_semaine=55,
        taux_lent=0.50,
    )

    assert result.besoin_100 == 170
    assert result.rapide_lunes == 115
    assert result.surplus == 0


def test_lunes_chapo_ne_doit_pas_utiliser_le_diff_seul() -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=110,
        achats_lent_semaine=110,
        taux_lent=0.50,
    )

    assert result.rapide_lunes == 110
    assert result.rapide_lunes != 0


def test_lunes_resout_taux_par_plateforme_lente_excel_vba() -> None:
    assert resolve_lunes_taux_lent_for_platform(
        "ST CYR LENT",
        pct_lent=0.50,
    ) == 1.0
    assert resolve_lunes_taux_lent_for_platform(
        "CHAPO LENT",
        pct_lent=0.50,
    ) == 0.50
    assert resolve_lunes_taux_lent_for_platform(
        "SUD LOG LENT",
        pct_lent=0.50,
    ) == 0.50


def test_lunes_plateforme_dynamique_utilise_son_taux_parametre() -> None:
    result = calculate_lunes_fast_for_platform(
        pf_lente="SAMATERRA LENT",
        commandes_lent_semaine=80,
        achats_lent_semaine=30,
        pct_lent=0.50,
        taux_lent_parametre=0.40,
    )

    assert result.besoin_100 == 200
    assert result.rapide_lunes == 170
    assert result.surplus == 0


def test_lunes_plateforme_dynamique_refuse_un_taux_non_parametre() -> None:
    with pytest.raises(ValueError, match="non parametre"):
        calculate_lunes_fast_for_platform(
            pf_lente="SAMATERRA LENT",
            commandes_lent_semaine=80,
            achats_lent_semaine=30,
            pct_lent=0.50,
        )


def test_lunes_retourne_zero_et_surplus_si_achats_depassent_besoin_100() -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=100,
        achats_lent_semaine=240,
        taux_lent=0.50,
    )

    assert result.besoin_100 == 200
    assert result.rapide_lunes == 0
    assert result.surplus == 40


def test_lunes_refuse_un_taux_lent_nul() -> None:
    with pytest.raises(ValueError, match="taux_lent"):
        calculate_lunes_fast_from_week_slow(
            commandes_lent_semaine=100,
            achats_lent_semaine=10,
            taux_lent=0,
        )


def test_lunes_compute_normalise_taux_pourcentage_entier() -> None:
    result = compute_lunes_credit_from_week_lent(
        pf_lente="CHAPO LENT",
        commandes_lent_semaine=110,
        achats_lent_semaine=110,
        taux_lent=50,
        lent_lunes_initial=0,
    )

    assert result.besoin_100 == 220
    assert result.rapide_lunes_final == 110
