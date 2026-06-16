from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_backend_v1_import_calculate_then_export_csv_flow() -> None:
    csv_content = (
        "C;D;F;G;I\n"
        "ART-SMT-001;Article test SMT;SMT;1155;-1000\n"
        "ART-CHA-001;Article test CHAPO;CHA;100;-20\n"
    )

    calculation_response = client.post(
        "/calculations/seb/from-erp-import",
        data={"buyer": "Seb", "coeff_lent": "0"},
        files={"file": ("erp.csv", csv_content, "text/csv")},
    )

    assert calculation_response.status_code == 200
    calculation_payload = calculation_response.json()
    assert calculation_payload["import_anomalies"] == []
    assert calculation_payload["import_row_count"] == 2
    assert len(calculation_payload["results"]) == 2

    export_response = client.post(
        "/exports/calculation-results.csv",
        json={
            "buyer": calculation_payload["buyer"],
            "results": calculation_payload["results"],
        },
    )

    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")
    assert "ART-SMT-001;Article test SMT;SMT;SAMATERRA;SAMATERRA LENT" in export_response.text
    assert "ART-CHA-001;Article test CHAPO;CHA;CHAPO;CHAPO LENT" in export_response.text
