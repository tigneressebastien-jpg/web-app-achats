from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_calculations_seb_simple_applies_consigne_before_slow_need() -> None:
    response = client.post(
        "/calculations/seb/simple",
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-CONSIGNE-001",
                    "libelle_article": "Poivron rouge",
                    "code_plateforme_erp": "CHA",
                    "prevision": 596,
                    "solde_previsionnel_j1": -146,
                    "texte_consigne": "+150 stock",
                    "valeur_consigne": -32,
                    "coeff_lent": 0.894,
                    "pct_lent": 0.30,
                }
            ],
        },
    )

    assert response.status_code == 200
    result = response.json()["results"][0]

    assert result["pf_rapide"] == "CHAPO"
    assert result["pf_lente"] == "CHAPO LENT"
    assert result["consigne_regle"] == "AJOUT_STOCK"
    assert result["solde_corrige"] == 36
    assert result["besoin_rapide"] == 0
    assert result["surplus_positif"] == 36
    assert result["besoin_lent_brut"] == pytest.approx(159.8472)
    assert result["besoin_lent"] == pytest.approx(123.8472)
    assert result["besoin_total"] == pytest.approx(123.8472)
    assert result["logs"] == ["Consigne AJOUT_STOCK appliquee: -146.0 -> 36.0"]
