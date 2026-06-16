from __future__ import annotations

from app.services.import_service import parse_erp_records, read_erp_csv_text


def test_read_erp_csv_with_excel_letter_headers() -> None:
    preview = read_erp_csv_text(
        "C;D;F;G;I\n"
        "ART001;Tomate ronde;SMT;1155;-1000\n"
    )

    assert preview.source_type == "csv"
    assert preview.anomalies == ()
    assert len(preview.rows) == 1

    row = preview.rows[0]
    assert row.code_article == "ART001"
    assert row.libelle_article == "Tomate ronde"
    assert row.code_plateforme_erp == "SMT"
    assert row.prevision == 1155
    assert row.solde_previsionnel_j1 == -1000


def test_read_erp_csv_with_raw_erp_column_positions() -> None:
    preview = read_erp_csv_text(
        "x;x;ART002;Melon charentais;x;CHA;200;x;-75\n"
    )

    assert preview.anomalies == ()
    assert len(preview.rows) == 1

    row = preview.rows[0]
    assert row.code_article == "ART002"
    assert row.libelle_article == "Melon charentais"
    assert row.code_plateforme_erp == "CHA"
    assert row.prevision == 200
    assert row.solde_previsionnel_j1 == -75


def test_parse_erp_records_reports_missing_required_fields() -> None:
    preview = parse_erp_records(
        [
            {
                "C": "",
                "D": "Article sans code",
                "F": "SMT",
                "G": 10,
                "I": -5,
            }
        ]
    )

    assert preview.rows == ()
    assert len(preview.anomalies) == 1
    assert preview.anomalies[0].level == "ERROR"
    assert "code_article/C" in preview.anomalies[0].context["missing_fields"]


def test_parse_erp_records_replaces_invalid_numbers_with_zero_and_logs_warning() -> None:
    preview = parse_erp_records(
        [
            {
                "C": "ART003",
                "D": "Article nombre invalide",
                "F": "SCY",
                "G": "abc",
                "I": "-12,5",
            }
        ]
    )

    assert len(preview.rows) == 1
    assert preview.rows[0].prevision == 0
    assert preview.rows[0].solde_previsionnel_j1 == -12.5
    assert len(preview.anomalies) == 1
    assert preview.anomalies[0].level == "WARNING"
    assert preview.anomalies[0].context == {"column": "G", "value": "abc"}
