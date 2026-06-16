from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.main import app
from app.services.import_service import read_erp_excel_bytes


client = TestClient(app)


def _erp_xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["C", "D", "F", "G", "I"])
    sheet.append(["ART-XLSX-001", "Article Excel SMT", "SMT", 1155, -1000])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_read_erp_excel_bytes_maps_expected_columns() -> None:
    preview = read_erp_excel_bytes(_erp_xlsx_bytes())

    assert preview.source_type == "excel"
    assert preview.anomalies == ()
    assert len(preview.rows) == 1

    row = preview.rows[0]
    assert row.code_article == "ART-XLSX-001"
    assert row.libelle_article == "Article Excel SMT"
    assert row.code_plateforme_erp == "SMT"
    assert row.prevision == 1155
    assert row.solde_previsionnel_j1 == -1000


def test_imports_erp_preview_accepts_xlsx_file() -> None:
    response = client.post(
        "/imports/erp/preview",
        files={
            "file": (
                "erp.xlsx",
                _erp_xlsx_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["filename"] == "erp.xlsx"
    assert payload["source_type"] == "excel"
    assert payload["row_count"] == 1
    assert payload["anomalies"] == []
    assert payload["rows"][0]["code_article"] == "ART-XLSX-001"
    assert payload["rows"][0]["code_plateforme_erp"] == "SMT"
