from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from typing import Mapping

from app.services.import_service import ImportAnomaly


@dataclass(frozen=True)
class ConsigneImportRow:
    code_article: str
    plateforme: str
    texte_consigne: str
    valeur_consigne: float = 0
    acheteur: str = "Seb"


@dataclass(frozen=True)
class ConsigneImportPreview:
    source_type: str
    rows: tuple[ConsigneImportRow, ...]
    anomalies: tuple[ImportAnomaly, ...] = field(default_factory=tuple)


_COLUMN_ALIASES = {
    "code_article": ("code_article", "code article", "article", "c"),
    "plateforme": ("plateforme", "pf", "plateforme cible"),
    "texte_consigne": ("texte_consigne", "texte consigne", "consigne"),
    "valeur_consigne": ("valeur_consigne", "valeur consigne", "valeur"),
    "acheteur": ("acheteur", "buyer"),
}


def read_consignes_csv_text(text: str) -> ConsigneImportPreview:
    if not text.strip():
        return ConsigneImportPreview(
            source_type="csv",
            rows=(),
            anomalies=(
                ImportAnomaly(
                    row_number=0,
                    level="ERROR",
                    message="Fichier consignes vide",
                ),
            ),
        )

    dialect = _detect_csv_dialect(text)
    reader = csv.DictReader(StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return ConsigneImportPreview(
            source_type="csv",
            rows=(),
            anomalies=(
                ImportAnomaly(
                    row_number=0,
                    level="ERROR",
                    message="Fichier consignes sans en-tete",
                ),
            ),
        )

    rows: list[ConsigneImportRow] = []
    anomalies: list[ImportAnomaly] = []

    for row_number, record in enumerate(reader, start=2):
        if _record_is_empty(record):
            continue

        code_article = _clean_text(_get_value(record, "code_article"))
        plateforme = _clean_text(_get_value(record, "plateforme"))
        texte_consigne = _clean_text(_get_value(record, "texte_consigne"))
        acheteur = _clean_text(_get_value(record, "acheteur")) or "Seb"

        missing_fields = []
        if not code_article:
            missing_fields.append("code_article")
        if not plateforme:
            missing_fields.append("plateforme")
        if not texte_consigne:
            missing_fields.append("texte_consigne")

        if missing_fields:
            anomalies.append(
                ImportAnomaly(
                    row_number=row_number,
                    level="ERROR",
                    message="Ligne consigne ignoree: champs obligatoires manquants",
                    context={"missing_fields": missing_fields},
                )
            )
            continue

        rows.append(
            ConsigneImportRow(
                code_article=code_article,
                plateforme=plateforme,
                texte_consigne=texte_consigne,
                valeur_consigne=_to_float(
                    _get_value(record, "valeur_consigne"),
                    row_number=row_number,
                    anomalies=anomalies,
                ),
                acheteur=acheteur,
            )
        )

    return ConsigneImportPreview(
        source_type="csv",
        rows=tuple(rows),
        anomalies=tuple(anomalies),
    )


def _detect_csv_dialect(text: str) -> type[csv.Dialect] | csv.Dialect:
    sample = text[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        return csv.excel


def _get_value(record: Mapping[str, object], field: str) -> object:
    aliases = _COLUMN_ALIASES[field]
    normalized_record = {_normalize_key(key): value for key, value in record.items()}
    for alias in aliases:
        value = normalized_record.get(_normalize_key(alias))
        if value is not None:
            return value
    return ""


def _normalize_key(key: object) -> str:
    return str(key or "").strip().lower().replace("_", " ")


def _record_is_empty(record: Mapping[str, object]) -> bool:
    return not any(str(value or "").strip() for value in record.values())


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _to_float(
    value: object,
    *,
    row_number: int,
    anomalies: list[ImportAnomaly],
) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    text = str(value).strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        anomalies.append(
            ImportAnomaly(
                row_number=row_number,
                level="WARNING",
                message="Valeur consigne numerique invalide, remplacee par 0",
                context={"value": value},
            )
        )
        return 0.0
