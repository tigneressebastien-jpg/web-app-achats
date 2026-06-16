from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _save_dynamic_platform(code: str = "DYN") -> None:
    response = client.post(
        "/platforms/saved",
        json={
            "code_erp": code,
            "pf_rapide": "DYNAMIQUE RAPIDE",
            "pf_lente": "DYNAMIQUE LENT",
            "actif": True,
            "lent_avec_pourcentage": True,
        },
    )
    assert response.status_code == 200


def test_platforms_effective_endpoint_includes_saved_dynamic_platform() -> None:
    _save_dynamic_platform("DYN")

    response = client.get("/platforms/effective")

    assert response.status_code == 200
    platforms = {platform["code_erp"]: platform for platform in response.json()}
    assert platforms["DYN"]["pf_rapide"] == "DYNAMIQUE RAPIDE"
    assert platforms["DYN"]["pf_lente"] == "DYNAMIQUE LENT"
    assert platforms["SMT"]["pf_rapide"] == "SAMATERRA"


def test_platforms_resolve_uses_saved_dynamic_platform_when_no_payload_table() -> None:
    _save_dynamic_platform("DYN")

    response = client.post("/platforms/resolve", json={"code_erp": "DYN"})

    assert response.status_code == 200
    assert response.json()["pf_rapide"] == "DYNAMIQUE RAPIDE"
    assert response.json()["pf_lente"] == "DYNAMIQUE LENT"


def test_calculation_uses_saved_dynamic_platform_when_no_payload_table() -> None:
    _save_dynamic_platform("DYN")

    response = client.post(
        "/calculations/seb/simple",
        json={
            "buyer": "Seb",
            "rows": [
                {
                    "code_article": "ART-DYN-001",
                    "libelle_article": "Article dynamique",
                    "code_plateforme_erp": "DYN",
                    "prevision": 0,
                    "solde_previsionnel_j1": -12,
                }
            ],
        },
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["pf_rapide"] == "DYNAMIQUE RAPIDE"
    assert result["pf_lente"] == "DYNAMIQUE LENT"
    assert result["besoin_rapide"] == 12
