from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_camions_projection_endpoint_keeps_intermediate_values_unrounded() -> None:
    response = client.post(
        "/camions/projection",
        json={
            "jour_depart": "samedi",
            "camions_depart": 40,
            "nombre_jours": 2,
            "inclure_depart": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["jour_depart"] == "samedi"
    assert payload["camions_depart"] == 40
    assert payload["nombre_jours"] == 2
    assert payload["inclure_depart"] is False
    assert len(payload["projections"]) == 2

    lundi = payload["projections"][0]
    mardi = payload["projections"][1]

    assert lundi["jour"] == "lundi"
    assert lundi["camions"] == pytest.approx(35.76)
    assert lundi["camions_affichage"] == 36
    assert mardi["jour"] == "mardi"
    assert mardi["camions"] == pytest.approx(30.0384)
    assert mardi["camions"] == pytest.approx(lundi["camions"] * 0.840)
    assert mardi["camions_affichage"] == 31


def test_camions_projection_endpoint_returns_400_for_invalid_day() -> None:
    response = client.post(
        "/camions/projection",
        json={
            "jour_depart": "dimanche",
            "camions_depart": 10,
            "nombre_jours": 1,
            "inclure_depart": False,
        },
    )

    assert response.status_code == 400
    assert "Jour non supporte" in response.json()["detail"]


def test_camions_platforms_excel_endpoint_returns_m8_m14_mapping() -> None:
    response = client.get("/camions/platforms/excel")

    assert response.status_code == 200
    assert response.json() == {
        "M8": "2C LOG",
        "M9": "CHAPO",
        "M10": "CHAPO LENT",
        "M11": "ST CYR",
        "M12": "ST CYR LENT",
        "M13": "SUD LOG",
        "M14": "SUD LOG LENT",
    }
