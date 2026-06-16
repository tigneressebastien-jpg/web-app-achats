from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_consignes_apply_endpoint_applies_stock_rule() -> None:
    response = client.post(
        "/consignes/apply",
        json={
            "solde_import": -146,
            "texte_consigne": "+150 stock",
            "valeur_consigne": -32,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "solde_corrige": 36,
        "besoin_rapide": 0,
        "surplus_positif": 36,
        "regle": "AJOUT_STOCK",
        "texte_normalise": "+150 STOCK",
        "anomalie": None,
    }


def test_consignes_apply_endpoint_returns_neutral_ok_rule() -> None:
    response = client.post(
        "/consignes/apply",
        json={
            "solde_import": -250,
            "texte_consigne": "TRANSFERT OK",
            "valeur_consigne": 100,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["solde_corrige"] == -250
    assert payload["besoin_rapide"] == 250
    assert payload["regle"] == "CONSIGNE_NEUTRE"
    assert payload["anomalie"] is None


def test_consignes_apply_endpoint_keeps_unknown_rule_visible() -> None:
    response = client.post(
        "/consignes/apply",
        json={
            "solde_import": -100,
            "texte_consigne": "A VERIFIER",
            "valeur_consigne": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["solde_corrige"] == -100
    assert payload["besoin_rapide"] == 100
    assert payload["regle"] == "CONSIGNE_INCONNUE"
    assert payload["anomalie"] == "Consigne non reconnue: A VERIFIER"
