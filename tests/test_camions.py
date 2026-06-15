from __future__ import annotations

import pytest

from app.services.camion_service import (
    PLATEFORMES_CAMIONS_EXCEL,
    calculer_projection_camions,
)


def test_projection_camions_samedi_vers_lundi_puis_mardi_sans_arrondi_intermediaire() -> None:
    projections = calculer_projection_camions(
        jour_depart="samedi",
        camions_depart=40,
        nombre_jours=2,
        inclure_depart=False,
    )

    lundi = projections[0]
    mardi = projections[1]

    assert lundi.jour == "lundi"
    assert lundi.camions == pytest.approx(35.76)
    assert mardi.jour == "mardi"
    assert mardi.camions == pytest.approx(30.0384)
    assert mardi.camions == pytest.approx(lundi.camions * 0.840)
    assert mardi.camions != pytest.approx(36 * 0.840)
    assert mardi.camions_affichage == 31


def test_projection_camions_mercredi_vers_jeudi() -> None:
    projections = calculer_projection_camions(
        jour_depart="mercredi",
        camions_depart=10,
        nombre_jours=1,
        inclure_depart=False,
    )

    assert projections[0].jour == "jeudi"
    assert projections[0].camions == pytest.approx(14.67)
    assert projections[0].camions_affichage == 15


def test_mapping_cellules_excel_dashboard_camions_v1() -> None:
    assert PLATEFORMES_CAMIONS_EXCEL["M8"] == "2C LOG"
    assert PLATEFORMES_CAMIONS_EXCEL["M10"] == "CHAPO LENT"
    assert PLATEFORMES_CAMIONS_EXCEL["M14"] == "SUD LOG LENT"
