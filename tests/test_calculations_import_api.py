from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_calculations_from_erp_import_reads_csv_and_calculates_results() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        "ART-SMT-001;Article test SMT;SMT;1155;-1000\n"
    )

    response = client.post(
        "/calculations/seb/from-erp-import",
        data={"buyer": "Seb", "coeff_lent": "0"},
        files={"file": ("erp.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["buyer"] == "Seb"
    assert payload["filename"] == "erp.csv"
    assert payload["source_type"] == "csv"
    assert payload["import_row_count"] == 1
    assert payload["import_anomalies"] == []

    result = payload["results"][0]
    assert result["code_article"] == "ART-SMT-001"
    assert result["pf_rapide"] == "SAMATERRA"
    assert result["pf_lente"] == "SAMATERRA LENT"
    assert result["solde_corrige"] == -1000
    assert result["besoin_rapide"] == 1000
    assert result["besoin_total"] == 1000


def test_calculations_from_erp_import_returns_import_anomalies() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        ";Article sans code;SMT;1155;-1000\n"
    )

    response = client.post(
        "/calculations/seb/from-erp-import",
        files={"file": ("erp.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["import_row_count"] == 0
    assert payload["results"] == []
    assert len(payload["import_anomalies"]) == 1
    assert payload["import_anomalies"][0]["level"] == "ERROR"
    assert "code_article/C" in payload["import_anomalies"][0]["context"]["missing_fields"]


def test_calculations_from_erp_import_rejects_unsupported_file_format() -> None:
    response = client.post(
        "/calculations/seb/from-erp-import",
        files={"file": ("erp.pdf", b"nope", "application/pdf")},
    )

    assert response.status_code == 400
    assert "Format import ERP non supporte" in response.json()["detail"]
