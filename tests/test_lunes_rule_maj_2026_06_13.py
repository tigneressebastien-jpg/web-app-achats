from __future__ import annotations

import pytest

from app.services.lunes_service import (
    calculate_lunes_fast_for_platform,
    calculate_lunes_fast_from_week_slow,
    resolve_lunes_taux_lent_for_platform,
)


@pytest.mark.parametrize(
    (
        "label",
        "commandes_lent_semaine",
        "achats_lent_semaine",
        "taux_lent",
        "besoin_100_attendu",
        "rapide_lunes_attendu",
    ),
    [
        ("ST CYR LENT", 163, 110, 1.00, 163, 53),
        ("CHAPO LENT", 110, 110, 0.50, 220, 110),
        ("SUD LOG LENT", 85, 55, 0.50, 170, 115),
    ],
)
def test_maj_2026_06_13_lunes_reconstitue_le_lent_semaine_a_100_pourcent(
    label: str,
    commandes_lent_semaine: float,
    achats_lent_semaine: float,
    taux_lent: float,
    besoin_100_attendu: float,
    rapide_lunes_attendu: float,
) -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=commandes_lent_semaine,
        achats_lent_semaine=achats_lent_semaine,
        taux_lent=taux_lent,
    )

    assert result.besoin_100 == pytest.approx(besoin_100_attendu), label
    assert result.rapide_lunes == pytest.approx(rapide_lunes_attendu), label
    assert result.surplus == 0


def test_maj_2026_06_13_lunes_ne_fait_pas_un_simple_diff_lent() -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=110,
        achats_lent_semaine=110,
        taux_lent=0.50,
    )

    ancien_diff_interdit = 110 - 110

    assert result.besoin_100 == 220
    assert result.rapide_lunes == 110
    assert result.rapide_lunes != ancien_diff_interdit


def test_maj_2026_06_13_lunes_retourne_zero_et_surplus_si_achats_depassent_besoin_100() -> None:
    result = calculate_lunes_fast_from_week_slow(
        commandes_lent_semaine=100,
        achats_lent_semaine=240,
        taux_lent=0.50,
    )

    assert result.besoin_100 == 200
    assert result.rapide_lunes == 0
    assert result.surplus == 40


def test_maj_2026_06_13_taux_lent_plateformes_historiques() -> None:
    assert resolve_lunes_taux_lent_for_platform("ST CYR LENT", pct_lent=0.50) == 1.00
    assert resolve_lunes_taux_lent_for_platform("CHAPO LENT", pct_lent=0.50) == 0.50
    assert resolve_lunes_taux_lent_for_platform("SUD LOG LENT", pct_lent=0.50) == 0.50


def test_maj_2026_06_13_taux_lent_plateforme_dynamique_parametree() -> None:
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


def test_maj_2026_06_13_taux_lent_dynamique_obligatoire() -> None:
    with pytest.raises(ValueError, match="non parametre"):
        calculate_lunes_fast_for_platform(
            pf_lente="SAMATERRA LENT",
            commandes_lent_semaine=80,
            achats_lent_semaine=30,
            pct_lent=0.50,
        )

