from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_imports_erp_save_persists_batch_and_rows() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        "ART-BATCH-001;Article batch SMT;SMT;1155;-1000\n"
    )

    save_response = client.post(
        "/imports/erp/save",
        files={"file": ("erp_batch.csv", csv_content, "text/csv")},
    )

    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["batch_id"] > 0
    assert saved["filename"] == "erp_batch.csv"
    assert saved["source_type"] == "csv"
    assert saved["row_count"] == 1
    assert saved["anomalies"] == []

    detail_response = client.get(f"/imports/batches/{saved['batch_id']}")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["batch_id"] == saved["batch_id"]
    assert detail["row_count"] == 1
    assert detail["rows"] == [
        {
            "code_article": "ART-BATCH-001",
            "libelle_article": "Article batch SMT",
            "code_plateforme_erp": "SMT",
            "prevision": 1155,
            "solde_previsionnel_j1": -1000,
        }
    ]


def test_imports_batches_list_contains_saved_batch() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        "ART-BATCH-LIST-001;Article batch list;SMT;10;-3\n"
    )

    save_response = client.post(
        "/imports/erp/save",
        files={"file": ("erp_batch_list.csv", csv_content, "text/csv")},
    )
    assert save_response.status_code == 200
    batch_id = save_response.json()["batch_id"]

    list_response = client.get("/imports/batches")

    assert list_response.status_code == 200
    batches = {batch["batch_id"]: batch for batch in list_response.json()}
    assert batch_id in batches
    assert batches[batch_id]["filename"] == "erp_batch_list.csv"
    assert batches[batch_id]["row_count"] == 1


def test_imports_batches_detail_returns_404_for_unknown_batch() -> None:
    response = client.get("/imports/batches/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Import batch introuvable"
