from __future__ import annotations

from pathlib import Path


def lire_erp_depuis_fichier(path: str | Path) -> list[dict[str, object]]:
    """Read a minimal ERP export from CSV or Excel into dictionaries."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(file_path)
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return _read_excel(file_path)
    raise ValueError(f"Format ERP non supporte: {suffix}")


def _read_csv(path: Path) -> list[dict[str, object]]:
    import pandas as pd

    frame = pd.read_csv(path)
    return frame.to_dict(orient="records")


def _read_excel(path: Path) -> list[dict[str, object]]:
    import pandas as pd

    frame = pd.read_excel(path)
    return frame.to_dict(orient="records")

