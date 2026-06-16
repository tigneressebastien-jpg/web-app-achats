from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_imports_status_is_ready() -> None:
    response = client.get("/imports/status")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_imports_erp_preview_accepts_csv_and_returns_normalized_rows() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        "ART-SMT-001;Article test SMT;SMT;1155;-1000\n"
    )

    response = client.post(
        "/imports/erp/preview",
        files={"file": ("erp.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["filename"] == "erp.csv"
    assert payload["source_type"] == "csv"
    assert payload["row_count"] == 1
    assert payload["anomalies"] == []
    assert payload["rows"] == [
        {
            "code_article": "ART-SMT-001",
            "libelle_article": "Article test SMT",
            "code_plateforme_erp": "SMT",
            "prevision": 1155,
            "solde_previsionnel_j1": -1000,
        }
    ]


def test_imports_erp_preview_rejects_unsupported_file_format() -> None:
    response = client.post(
        "/imports/erp/preview",
        files={"file": ("erp.pdf", b"nope", "application/pdf")},
    )

    assert response.status_code == 400
    assert "Format import ERP non supporte" in response.json()["detail"]
