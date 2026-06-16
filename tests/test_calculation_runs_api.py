from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_calculation_simple_can_persist_run_and_logs() -> None:
    response = client.post(
        "/calculations/seb/simple",
        params={"persist": True},
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-RUN-001",
                    "libelle_article": "Article run",
                    "code_plateforme_erp": "SMT",
                    "prevision": 0,
                    "solde_previsionnel_j1": -12,
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] > 0

    detail_response = client.get(f"/calculations/runs/{payload['run_id']}")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["run_id"] == payload["run_id"]
    assert detail["buyer"] == "Seb"
    assert detail["status"] == "completed"
    assert detail["result_count"] == 1
    assert detail["log_count"] >= 1
    assert detail["results"][0]["code_article"] == "ART-RUN-001"
    assert detail["results"][0]["besoin_rapide"] == 12
    assert any("Run calcul termine" in log["message"] for log in detail["logs"])


def test_calculation_runs_list_contains_persisted_run() -> None:
    response = client.post(
        "/calculations/seb/simple",
        params={"persist": True},
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-RUN-LIST-001",
                    "libelle_article": "Article run liste",
                    "code_plateforme_erp": "SMT",
                    "prevision": 0,
                    "solde_previsionnel_j1": -7,
                }
            ],
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    list_response = client.get("/calculations/runs")

    assert list_response.status_code == 200
    runs = {run["run_id"]: run for run in list_response.json()}
    assert run_id in runs
    assert runs[run_id]["result_count"] == 1


def test_calculation_from_import_can_persist_import_anomaly_logs() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        "ART-RUN-IMPORT-001;Article run import;SMT;abc;-12\n"
    )

    response = client.post(
        "/calculations/seb/from-erp-import",
        data={"buyer": "Seb", "persist": "true"},
        files={"file": ("erp_run.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] > 0
    assert len(payload["import_anomalies"]) == 1

    detail_response = client.get(f"/calculations/runs/{payload['run_id']}")

    assert detail_response.status_code == 200
    logs = detail_response.json()["logs"]
    assert any("Valeur numerique invalide" in log["message"] for log in logs)


def test_calculation_run_detail_returns_404_for_unknown_run() -> None:
    response = client.get("/calculations/runs/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run calcul introuvable"
