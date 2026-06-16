from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_platforms_defaults_endpoint_contains_smt() -> None:
    response = client.get("/platforms/defaults")

    assert response.status_code == 200
    platforms = {platform["code_erp"]: platform for platform in response.json()}

    assert platforms["SMT"] == {
        "code_erp": "SMT",
        "pf_rapide": "SAMATERRA",
        "pf_lente": "SAMATERRA LENT",
        "actif": True,
        "lent_avec_pourcentage": True,
    }


def test_platforms_resolve_endpoint_maps_smt_from_defaults() -> None:
    response = client.post(
        "/platforms/resolve",
        json={"code_erp": "smt"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "code_erp": "SMT",
        "pf_rapide": "SAMATERRA",
        "pf_lente": "SAMATERRA LENT",
        "actif": True,
        "lent_avec_pourcentage": True,
    }


def test_platforms_resolve_endpoint_accepts_dynamic_payload() -> None:
    response = client.post(
        "/platforms/resolve",
        json={
            "code_erp": "ABC",
            "plateformes": [
                {
                    "code_erp": "ABC",
                    "pf_rapide": "ABC RAPIDE",
                    "pf_lente": "ABC LENT",
                    "actif": True,
                    "lent_avec_pourcentage": False,
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["pf_rapide"] == "ABC RAPIDE"
    assert response.json()["pf_lente"] == "ABC LENT"


def test_platforms_resolve_endpoint_refuses_inactive_platform_by_default() -> None:
    response = client.post(
        "/platforms/resolve",
        json={
            "code_erp": "TLS",
            "plateformes": [
                {
                    "code_erp": "TLS",
                    "pf_rapide": "TOULOUSE",
                    "pf_lente": "TOULOUSE LENT",
                    "actif": False,
                    "lent_avec_pourcentage": True,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "inactive" in response.json()["detail"]
