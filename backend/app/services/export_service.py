from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Iterable, Mapping

from openpyxl import Workbook


CALCULATION_RESULT_CSV_COLUMNS = [
    "code_article",
    "libelle_article",
    "code_plateforme_erp",
    "pf_rapide",
    "pf_lente",
    "solde_corrige",
    "besoin_rapide",
    "besoin_lent",
    "besoin_lent_brut",
    "surplus_positif",
    "besoin_total",
    "consigne_regle",
    "logs",
]


CALCULATION_RESULT_XLSX_COLUMNS = CALCULATION_RESULT_CSV_COLUMNS


def calculation_results_to_csv(
    results: Iterable[Mapping[str, object]],
    *,
    delimiter: str = ";",
) -> str:
    """Export calculation results to a semicolon CSV string for Excel users."""
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=CALCULATION_RESULT_CSV_COLUMNS,
        delimiter=delimiter,
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()

    for result in results:
        writer.writerow(
            {
                column: _format_csv_value(result.get(column))
                for column in CALCULATION_RESULT_CSV_COLUMNS
            }
        )

    return output.getvalue()


def calculation_results_to_xlsx(
    results: Iterable[Mapping[str, object]],
    *,
    sheet_name: str = "Calculs",
) -> bytes:
    """Export calculation results to an XLSX workbook for direct Excel opening."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    worksheet.append(CALCULATION_RESULT_XLSX_COLUMNS)

    for result in results:
        worksheet.append(
            [
                _format_xlsx_value(result.get(column))
                for column in CALCULATION_RESULT_XLSX_COLUMNS
            ]
        )

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _format_csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " | ".join(str(item) for item in value)
    return value


def _format_xlsx_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return " | ".join(str(item) for item in value)
    return value
