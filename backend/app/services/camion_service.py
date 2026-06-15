from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass


COEFFICIENTS_SEMAINE_GLISSANTE = {
    "lundi": ("mardi", 0.840),
    "mardi": ("mercredi", 0.935),
    "mercredi": ("jeudi", 1.467),
    "jeudi": ("vendredi", 1.216),
    "vendredi": ("samedi", 0.664),
    "samedi": ("lundi", 0.894),
}

PLATEFORMES_CAMIONS_EXCEL = {
    "M8": "2C LOG",
    "M9": "CHAPO",
    "M10": "CHAPO LENT",
    "M11": "ST CYR",
    "M12": "ST CYR LENT",
    "M13": "SUD LOG",
    "M14": "SUD LOG LENT",
}


@dataclass(frozen=True)
class ProjectionCamion:
    jour: str
    camions: float
    camions_affichage: int


def calculer_projection_camions(
    jour_depart: str,
    camions_depart: float,
    *,
    nombre_jours: int = 6,
    inclure_depart: bool = True,
) -> list[ProjectionCamion]:
    """Project trucks over a rolling week without intermediate rounding."""
    if nombre_jours < 0:
        raise ValueError("nombre_jours ne peut pas etre negatif")

    jour = _normaliser_jour(jour_depart)
    camions = _to_float(camions_depart)
    projections: list[ProjectionCamion] = []

    if inclure_depart:
        projections.append(_projection(jour, camions))

    for _ in range(nombre_jours):
        if jour not in COEFFICIENTS_SEMAINE_GLISSANTE:
            raise ValueError(f"Jour non supporte pour la semaine glissante: {jour_depart}")
        jour_suivant, coefficient = COEFFICIENTS_SEMAINE_GLISSANTE[jour]
        camions = camions * coefficient
        jour = jour_suivant
        projections.append(_projection(jour, camions))

    return projections


def _projection(jour: str, camions: float) -> ProjectionCamion:
    return ProjectionCamion(
        jour=jour,
        camions=camions,
        camions_affichage=math.ceil(camions),
    )


def _normaliser_jour(jour: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(jour).strip().lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _to_float(value: float | int | str | None) -> float:
    if value is None or value == "":
        return 0
    return float(str(value).replace(",", "."))
