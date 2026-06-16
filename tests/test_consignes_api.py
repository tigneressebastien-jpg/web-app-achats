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


def test_consignes_saved_endpoint_creates_and_lists_consigne_by_erp_key() -> None:
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
    assert payload["plateforme_erp"] == "SMT"
    assert payload["texte_consigne"] == "+10 stock"
    assert payload["valeur_consigne"] == 3

    list_response = client.get(
        "/consignes/saved",
        params={
            "acheteur": "Seb",
            "code_article": "ART-CONSIGNE-SAVED-001",
            "plateforme_erp": "SMT",
        },
    )

    assert list_response.status_code == 200
    consignes = list_response.json()["consignes"]
    assert len(consignes) == 1
    assert consignes[0]["id"] == payload["id"]
    assert consignes[0]["plateforme_erp"] == "SMT"


def test_consignes_saved_endpoint_upserts_existing_consigne_after_pf_normalization() -> None:
    first_response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": "ART-CONSIGNE-UPSERT-001",
            "plateforme_erp": "CHAPO",
            "texte_consigne": "OK",
            "valeur_consigne": 0,
        },
    )
    assert first_response.status_code == 200
    first_payload = first_response.json()
    assert first_payload["plateforme_erp"] == "CHA"

    second_response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": "ART-CONSIGNE-UPSERT-001",
            "plateforme_erp": "CHAPO LENT",
            "texte_consigne": "+25 stock",
            "valeur_consigne": 5,
        },
    )

    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["id"] == first_payload["id"]
    assert second_payload["plateforme_erp"] == "CHA"
    assert second_payload["texte_consigne"] == "+25 stock"
    assert second_payload["valeur_consigne"] == 5


def test_consignes_saved_endpoint_rejects_empty_code_article() -> None:
    response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": " ",
            "plateforme_erp": "CHAPO",
            "texte_consigne": "OK",
            "valeur_consigne": 0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "code_article obligatoire"


def test_consignes_import_csv_saves_valid_rows_and_reports_anomalies() -> None:
    csv_content = "\n".join(
        [
            "code_article;plateforme;texte_consigne;valeur_consigne;acheteur",
            "ART-CONSIGNE-IMPORT-001;SAMATERRA;+15 stock;4;Seb",
            "ART-CONSIGNE-IMPORT-002;CHAPO;;0;Seb",
            "ART-CONSIGNE-IMPORT-003;CHAPO;OK;abc;Seb",
        ]
    )

    response = client.post(
        "/consignes/import/csv",
        files={"file": ("consignes.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["filename"] == "consignes.csv"
    assert payload["source_type"] == "csv"
    assert payload["saved_count"] == 2

    saved_by_code = {
        consigne["code_article"]: consigne for consigne in payload["consignes"]
    }
    assert saved_by_code["ART-CONSIGNE-IMPORT-001"] == {
        "id": saved_by_code["ART-CONSIGNE-IMPORT-001"]["id"],
        "acheteur": "Seb",
        "code_article": "ART-CONSIGNE-IMPORT-001",
        "plateforme_erp": "SMT",
        "texte_consigne": "+15 stock",
        "valeur_consigne": 4,
    }
    assert saved_by_code["ART-CONSIGNE-IMPORT-003"] == {
        "id": saved_by_code["ART-CONSIGNE-IMPORT-003"]["id"],
        "acheteur": "Seb",
        "code_article": "ART-CONSIGNE-IMPORT-003",
        "plateforme_erp": "CHA",
        "texte_consigne": "OK",
        "valeur_consigne": 0,
    }

    anomalies = payload["anomalies"]
    assert anomalies == [
        {
            "row_number": 3,
            "level": "ERROR",
            "message": "Ligne consigne ignoree: champs obligatoires manquants",
            "context": {"missing_fields": ["texte_consigne"]},
        },
        {
            "row_number": 4,
            "level": "WARNING",
            "message": "Valeur consigne numerique invalide, remplacee par 0",
            "context": {"value": "abc"},
        },
    ]

    list_response = client.get(
        "/consignes/saved",
        params={"acheteur": "Seb", "code_article": "ART-CONSIGNE-IMPORT-001"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["consignes"][0]["plateforme_erp"] == "SMT"
    assert list_response.json()["consignes"][0]["texte_consigne"] == "+15 stock"


def test_consignes_import_csv_preview_does_not_save_rows() -> None:
    csv_content = "\n".join(
        [
            "code_article;plateforme;texte_consigne;valeur_consigne;acheteur",
            "ART-CONSIGNE-PREVIEW-001;ST CYR;+20 stock;2;Seb",
        ]
    )

    response = client.post(
        "/consignes/import/csv/preview",
        files={"file": ("consignes.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "filename": "consignes.csv",
        "source_type": "csv",
        "row_count": 1,
        "rows": [
            {
                "acheteur": "Seb",
                "code_article": "ART-CONSIGNE-PREVIEW-001",
                "plateforme_erp": "SCY",
                "texte_consigne": "+20 stock",
                "valeur_consigne": 2,
            }
        ],
        "anomalies": [],
    }

    list_response = client.get(
        "/consignes/saved",
        params={"acheteur": "Seb", "code_article": "ART-CONSIGNE-PREVIEW-001"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["consignes"] == []


def test_consignes_import_csv_rejects_unsupported_format() -> None:
    response = client.post(
        "/consignes/import/csv",
        files={"file": ("consignes.xlsx", "fake", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Format consignes non supporte: .xlsx"
