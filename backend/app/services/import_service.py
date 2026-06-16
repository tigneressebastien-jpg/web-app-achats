from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from pathlib import Path
from typing import Iterable, Mapping

from app.services.besoin_service import ErpRow


@dataclass(frozen=True)
class ImportAnomaly:
    row_number: int
    level: str
    message: str
    context: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ErpImportPreview:
    source_type: str
    rows: tuple[ErpRow, ...]
    anomalies: tuple[ImportAnomaly, ...] = field(default_factory=tuple)


_COLUMN_ALIASES = {
    "code_article": ("code_article", "code article", "article", "c"),
    "libelle_article": ("libelle_article", "libelle article", "libelle", "d"),
    "code_plateforme_erp": (
        "code_plateforme_erp",
        "plateforme erp",
        "code plateforme erp",
        "plateforme",
        "f",
    ),
    "prevision": ("prevision", "prevision g", "g"),
    "solde_previsionnel_j1": (
        "solde_previsionnel_j1",
        "solde previsionnel j1",
        "solde previsionnel j+1",
        "solde j+1",
        "i",
    ),
}

_RAW_COLUMN_INDEXES = {
    "code_article": 2,
    "libelle_article": 3,
    "code_plateforme_erp": 5,
    "prevision": 6,
    "solde_previsionnel_j1": 8,
}


def read_erp_file(filename: str, content: bytes) -> ErpImportPreview:
    """Read an ERP export from CSV or Excel bytes and return normalized rows."""
    suffix = Path(filename or "").suffix.lower()
    if suffix in {".csv", ".txt", ""}:
        return read_erp_csv_text(content.decode("utf-8-sig"))
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return read_erp_excel_bytes(content)
    raise ValueError(f"Format import ERP non supporte: {suffix}")


def read_erp_csv_text(text: str) -> ErpImportPreview:
    """Read a CSV ERP export.

    Supported CSV shapes:
    - headers using ERP letters C, D, F, G, I;
    - business headers such as code_article, libelle_article, etc.;
    - raw ERP rows where C/D/F/G/I are physical columns 3/4/6/7/9.
    """
    if not text.strip():
        return ErpImportPreview(
            source_type="csv",
            rows=(),
            anomalies=(
                ImportAnomaly(
                    row_number=0,
                    level="ERROR",
                    message="Fichier import ERP vide",
                ),
            ),
        )

    dialect = _detect_csv_dialect(text)
    reader = csv.reader(StringIO(text), dialect)
    rows = list(reader)
    if not rows:
        return ErpImportPreview(source_type="csv", rows=())

    first_row = rows[0]
    if _looks_like_header(first_row):
        dict_reader = csv.DictReader(StringIO(text), dialect=dialect)
        return parse_erp_records(dict_reader, source_type="csv", first_data_row_number=2)

    records: list[dict[str, object]] = []
    anomalies: list[ImportAnomaly] = []
    for row_number, raw_row in enumerate(rows, start=1):
        if not any(str(value).strip() for value in raw_row):
            continue
        if len(raw_row) <= max(_RAW_COLUMN_INDEXES.values()):
            anomalies.append(
                ImportAnomaly(
                    row_number=row_number,
                    level="ERROR",
                    message="Ligne ERP trop courte pour lire les colonnes C/D/F/G/I",
                    context={"columns_count": len(raw_row)},
                )
            )
            continue
        records.append(
            {
                field: raw_row[index]
                for field, index in _RAW_COLUMN_INDEXES.items()
            }
        )

    parsed = parse_erp_records(records, source_type="csv", first_data_row_number=1)
    return ErpImportPreview(
        source_type="csv",
        rows=parsed.rows,
        anomalies=tuple(anomalies) + parsed.anomalies,
    )


def read_erp_excel_bytes(content: bytes) -> ErpImportPreview:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("pandas est requis pour lire un import ERP Excel") from exc

    frame = pd.read_excel(BytesIO(content), dtype=object)
    parsed = parse_erp_records(
        frame.to_dict(orient="records"),
        source_type="excel",
        first_data_row_number=2,
    )
    return ErpImportPreview(
        source_type="excel",
        rows=parsed.rows,
        anomalies=parsed.anomalies,
    )


def parse_erp_records(
    records: Iterable[Mapping[str, object]],
    *,
    source_type: str = "records",
    first_data_row_number: int = 1,
) -> ErpImportPreview:
    parsed_rows: list[ErpRow] = []
    anomalies: list[ImportAnomaly] = []

    for offset, record in enumerate(records):
        row_number = first_data_row_number + offset
        if _record_is_empty(record):
            continue

        code_article = _clean_text(_get_value(record, "code_article"))
        libelle_article = _clean_text(_get_value(record, "libelle_article"))
        code_plateforme_erp = _clean_text(_get_value(record, "code_plateforme_erp")).upper()

        missing_fields = []
        if not code_article:
            missing_fields.append("code_article/C")
        if not libelle_article:
            missing_fields.append("libelle_article/D")
        if not code_plateforme_erp:
            missing_fields.append("code_plateforme_erp/F")

        if missing_fields:
            anomalies.append(
                ImportAnomaly(
                    row_number=row_number,
                    level="ERROR",
                    message="Ligne ERP ignoree: champs obligatoires manquants",
                    context={"missing_fields": missing_fields},
                )
            )
            continue

        prevision = _to_float(
            _get_value(record, "prevision"),
            row_number=row_number,
            column="G",
            anomalies=anomalies,
        )
        solde_previsionnel_j1 = _to_float(
            _get_value(record, "solde_previsionnel_j1"),
            row_number=row_number,
            column="I",
            anomalies=anomalies,
        )

        parsed_rows.append(
            ErpRow(
                code_article=code_article,
                libelle_article=libelle_article,
                code_plateforme_erp=code_plateforme_erp,
                prevision=prevision,
                solde_previsionnel_j1=solde_previsionnel_j1,
            )
        )

    return ErpImportPreview(
        source_type=source_type,
        rows=tuple(parsed_rows),
        anomalies=tuple(anomalies),
    )


def _detect_csv_dialect(text: str) -> type[csv.Dialect] | csv.Dialect:
    sample = text[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,	")
    except csv.Error:
        return csv.excel


def _looks_like_header(row: list[str]) -> bool:
    normalized_values = {_normalize_key(value) for value in row}
    aliases = {
        alias
        for field_aliases in _COLUMN_ALIASES.values()
        for alias in field_aliases
    }
    return bool(normalized_values & aliases)


def _record_is_empty(record: Mapping[str, object]) -> bool:
    return not any(_clean_text(value) for value in record.values())


def _get_value(record: Mapping[str, object], field: str) -> object | None:
    normalized_record = {_normalize_key(key): value for key, value in record.items()}
    for alias in _COLUMN_ALIASES[field]:
        if alias in normalized_record:
            return normalized_record[alias]
    return None


def _normalize_key(value: object) -> str:
    return str(value).strip().lower().replace("_", " ")


def _clean_text(value: object | None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def _to_float(
    value: object | None,
    *,
    row_number: int,
    column: str,
    anomalies: list[ImportAnomaly],
) -> float:
    text = _clean_text(value)
    if not text:
        return 0.0
    normalized = text.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        anomalies.append(
            ImportAnomaly(
                row_number=row_number,
                level="WARNING",
                message="Valeur numerique invalide remplacee par 0",
                context={"column": column, "value": text},
            )
        )
        return 0.0
