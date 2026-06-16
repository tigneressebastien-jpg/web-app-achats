from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_calculations_seb_simple_maps_smt_and_computes_fast_need() -> None:
    response = client.post(
        "/calculations/seb/simple",
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-SMT-001",
                    "libelle_article": "Article test SMT",
                    "code_plateforme_erp": "SMT",
                    "prevision": 1155,
                    "solde_previsionnel_j1": -1000,
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["buyer"] == "Seb"
    assert len(payload["results"]) == 1

    result = payload["results"][0]
    assert result["code_article"] == "ART-SMT-001"
    assert result["libelle_article"] == "Article test SMT"
    assert result["code_plateforme_erp"] == "SMT"
    assert result["pf_rapide"] == "SAMATERRA"
    assert result["pf_lente"] == "SAMATERRA LENT"
    assert result["solde_corrige"] == -1000
    assert result["besoin_rapide"] == 1000
    assert result["besoin_lent"] == 0
    assert result["besoin_lent_brut"] == 0
    assert result["surplus_positif"] == 0
    assert result["besoin_total"] == 1000
    assert result["consigne_regle"] is None
    assert result["logs"] == []


def test_calculations_seb_simple_returns_400_for_unknown_platform() -> None:
    response = client.post(
        "/calculations/seb/simple",
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-UNKNOWN-001",
                    "libelle_article": "Article plateforme inconnue",
                    "code_plateforme_erp": "XXX",
                    "prevision": 100,
                    "solde_previsionnel_j1": -10,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "ART-UNKNOWN-001" in response.json()["detail"]
    assert "XXX" in response.json()["detail"]


def test_calculations_seb_simple_returns_400_for_invalid_pct_lent() -> None:
    response = client.post(
        "/calculations/seb/simple",
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-PCT-LENT-NEG-001",
                    "libelle_article": "Article pct lent invalide",
                    "code_plateforme_erp": "CHA",
                    "prevision": 100,
                    "solde_previsionnel_j1": -10,
                    "coeff_lent": 1,
                    "pct_lent": -0.5,
                }
            ],
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "ART-PCT-LENT-NEG-001" in detail
    assert "Le pourcentage lent ne peut pas etre negatif" in detail
