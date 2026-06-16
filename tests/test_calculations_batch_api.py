from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_calculations_from_saved_import_batch() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        "ART-CALC-BATCH-001;Article batch SMT;SMT;1155;-1000\n"
    )

    save_response = client.post(
        "/imports/erp/save",
        files={"file": ("erp_calc_batch.csv", csv_content, "text/csv")},
    )
    assert save_response.status_code == 200
    batch_id = save_response.json()["batch_id"]

    calculation_response = client.post(
        f"/calculations/seb/from-import-batch/{batch_id}",
        params={"buyer": "Seb", "coeff_lent": 0},
    )

    assert calculation_response.status_code == 200
    payload = calculation_response.json()

    assert payload["buyer"] == "Seb"
    assert payload["batch_id"] == batch_id
    assert payload["filename"] == "erp_calc_batch.csv"
    assert payload["source_type"] == "csv"
    assert payload["import_row_count"] == 1

    result = payload["results"][0]
    assert result["code_article"] == "ART-CALC-BATCH-001"
    assert result["pf_rapide"] == "SAMATERRA"
    assert result["pf_lente"] == "SAMATERRA LENT"
    assert result["besoin_rapide"] == 1000
    assert result["besoin_total"] == 1000


def test_calculations_from_saved_import_batch_returns_404_for_unknown_batch() -> None:
    response = client.post("/calculations/seb/from-import-batch/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Import batch introuvable"
