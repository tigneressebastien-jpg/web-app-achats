from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.main import app


client = TestClient(app)


def test_exports_status_is_ready() -> None:
    response = client.get("/exports/status")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_exports_calculation_results_csv_returns_downloadable_csv() -> None:
    response = client.post(
        "/exports/calculation-results.csv",
        json=_calculation_payload(),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        "attachment; filename=calculation-results.csv"
    )
    assert "ART-SMT-001;Article test SMT;SMT;SAMATERRA" in response.text


def test_exports_calculation_results_xlsx_returns_openable_workbook() -> None:
    response = client.post(
        "/exports/calculation-results.xlsx",
        json=_calculation_payload(),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == (
        "attachment; filename=calculation-results.xlsx"
    )

    worksheet = _load_first_worksheet(response.content)
    assert worksheet.title == "Calculs"
    assert worksheet["A1"].value == "code_article"
    assert worksheet["A2"].value == "ART-SMT-001"
    assert worksheet["D2"].value == "SAMATERRA"
    assert worksheet["G2"].value == 1000


def test_exports_calculation_run_csv_returns_persisted_results() -> None:
    run_id = _create_persisted_calculation_run()

    response = client.get(f"/exports/calculation-runs/{run_id}.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        f"attachment; filename=calculation-run-{run_id}.csv"
    )
    assert "ART-EXPORT-RUN-001;Article export run;SMT;SAMATERRA;SAMATERRA LENT" in response.text
    assert ";12.0;0.0;" in response.text


def test_exports_calculation_run_xlsx_returns_persisted_results() -> None:
    run_id = _create_persisted_calculation_run()

    response = client.get(f"/exports/calculation-runs/{run_id}.xlsx")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.headers["content-disposition"] == (
        f"attachment; filename=calculation-run-{run_id}.xlsx"
    )

    worksheet = _load_first_worksheet(response.content)
    assert worksheet["A2"].value == "ART-EXPORT-RUN-001"
    assert worksheet["D2"].value == "SAMATERRA"
    assert worksheet["E2"].value == "SAMATERRA LENT"
    assert worksheet["G2"].value == 12


def test_exports_calculation_run_csv_returns_404_for_unknown_run() -> None:
    response = client.get("/exports/calculation-runs/999999999.csv")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run calcul introuvable"


def test_exports_calculation_run_xlsx_returns_404_for_unknown_run() -> None:
    response = client.get("/exports/calculation-runs/999999999.xlsx")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run calcul introuvable"


def _calculation_payload() -> dict[str, object]:
    return {
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
    }


def _create_persisted_calculation_run() -> int:
    calculation_response = client.post(
        "/calculations/seb/simple",
        params={"persist": True},
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-EXPORT-RUN-001",
                    "libelle_article": "Article export run",
                    "code_plateforme_erp": "SMT",
                    "prevision": 0,
                    "solde_previsionnel_j1": -12,
                }
            ],
        },
    )
    assert calculation_response.status_code == 200
    return calculation_response.json()["run_id"]


def _load_first_worksheet(content: bytes):
    workbook = load_workbook(BytesIO(content))
    return workbook.active
