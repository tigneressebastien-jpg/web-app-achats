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


def test_consignes_saved_endpoint_creates_and_lists_consigne() -> None:
    response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": "ART-CONSIGNE-SAVED-001",
            "plateforme": "SAMATERRA",
            "texte_consigne": "+10 stock",
            "valeur_consigne": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] > 0
    assert payload["acheteur"] == "Seb"
    assert payload["code_article"] == "ART-CONSIGNE-SAVED-001"
    assert payload["plateforme"] == "SAMATERRA"
    assert payload["texte_consigne"] == "+10 stock"
    assert payload["valeur_consigne"] == 3

    list_response = client.get(
        "/consignes/saved",
        params={"acheteur": "Seb", "code_article": "ART-CONSIGNE-SAVED-001"},
    )

    assert list_response.status_code == 200
    consignes = list_response.json()["consignes"]
    assert len(consignes) == 1
    assert consignes[0]["id"] == payload["id"]


def test_consignes_saved_endpoint_upserts_existing_consigne() -> None:
    first_response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": "ART-CONSIGNE-UPSERT-001",
            "plateforme": "CHAPO",
            "texte_consigne": "OK",
            "valeur_consigne": 0,
        },
    )
    assert first_response.status_code == 200
    first_payload = first_response.json()

    second_response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": "ART-CONSIGNE-UPSERT-001",
            "plateforme": "CHAPO",
            "texte_consigne": "+25 stock",
            "valeur_consigne": 5,
        },
    )

    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["id"] == first_payload["id"]
    assert second_payload["texte_consigne"] == "+25 stock"
    assert second_payload["valeur_consigne"] == 5


def test_consignes_saved_endpoint_rejects_empty_code_article() -> None:
    response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": " ",
            "plateforme": "CHAPO",
            "texte_consigne": "OK",
            "valeur_consigne": 0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "code_article obligatoire"
