from __future__ import annotations

import csv
from io import StringIO
from typing import Iterable, Mapping


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


def _format_csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " | ".join(str(item) for item in value)
    return value
