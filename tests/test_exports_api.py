from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_exports_status_is_ready() -> None:
    response = client.get("/exports/status")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_exports_calculation_results_csv_returns_downloadable_csv() -> None:
    response = client.post(
        "/exports/calculation-results.csv",
        json={
            "buyer": "Seb",
            "results": [
                {
                    "code_article": "ART-SMT-001",
                    "libelle_article": "Article test SMT",
                    "code_plateforme_erp": "SMT",
                    "pf_rapide": "SAMATERRA",
                    "pf_lente": "SAMATERRA LENT",
                    "solde_corrige": -1000,
                    "besoin_rapide": 1000,
                    "besoin_lent": 0,
                    "besoin_lent_brut": 0,
                    "surplus_positif": 0,
                    "besoin_total": 1000,
                    "consigne_regle": None,
                    "logs": [],
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        "attachment; filename=calculation-results.csv"
    )
    assert "ART-SMT-001;Article test SMT;SMT;SAMATERRA" in response.text
