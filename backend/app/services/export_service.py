from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping


def exporter_resultats_csv(rows: Iterable[Mapping[str, object]], path: str | Path) -> Path:
    import pandas as pd

    output_path = Path(path)
    frame = pd.DataFrame(list(rows))
    frame.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def exporter_resultats_excel(rows: Iterable[Mapping[str, object]], path: str | Path) -> Path:
    import pandas as pd

    output_path = Path(path)
    frame = pd.DataFrame(list(rows))
    frame.to_excel(output_path, index=False)
    return output_path

