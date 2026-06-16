from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_fournisseurs_remplissage_endpoint_uses_pas_colis_before_palettisation() -> None:
    response = client.post(
        "/fournisseurs/remplissage",
        json={
            "plateforme": "CHAPO",
            "commandes": 100,
            "besoin": 100,
            "palettisation": 144,
            "pas_colis": 48,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "plateforme": "CHAPO",
        "quantite": 96,
        "pas_utilise": 48,
        "raison": "OK",
    }


def test_fournisseurs_remplissage_endpoint_never_fills_zero_orders() -> None:
    response = client.post(
        "/fournisseurs/remplissage",
        json={
            "plateforme": "CHAPO",
            "commandes": 0,
            "besoin": 100,
            "palettisation": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["quantite"] == 0
    assert response.json()["raison"] == "COMMANDES_ZERO"


def test_fournisseurs_remplissage_endpoint_respects_forbidden_platform() -> None:
    response = client.post(
        "/fournisseurs/remplissage",
        json={
            "plateforme": "CHAPO",
            "commandes": 100,
            "besoin": 100,
            "palettisation": 10,
            "pf_interdite": "CHAPO",
        },
    )

    assert response.status_code == 200
    assert response.json()["quantite"] == 0
    assert response.json()["raison"] == "PF_INTERDITE"


def test_fournisseurs_remplissage_endpoint_returns_400_for_unknown_rounding() -> None:
    response = client.post(
        "/fournisseurs/remplissage",
        json={
            "plateforme": "CHAPO",
            "commandes": 100,
            "besoin": 100,
            "palettisation": 10,
            "arrondi": "bizarre",
        },
    )

    assert response.status_code == 400
    assert "Strategie d'arrondi inconnue" in response.json()["detail"]
