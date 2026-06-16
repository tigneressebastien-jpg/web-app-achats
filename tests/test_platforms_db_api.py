from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_platforms_saved_endpoint_upserts_dynamic_platform_in_sqlite() -> None:
    response = client.post(
        "/platforms/saved",
        json={
            "code_erp": "zzz",
            "pf_rapide": "ZONE TEST",
            "pf_lente": "ZONE TEST LENT",
            "actif": True,
            "lent_avec_pourcentage": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "code_erp": "ZZZ",
        "pf_rapide": "ZONE TEST",
        "pf_lente": "ZONE TEST LENT",
        "actif": True,
        "lent_avec_pourcentage": True,
    }

    list_response = client.get("/platforms/saved")

    assert list_response.status_code == 200
    saved_platforms = {
        platform["code_erp"]: platform
        for platform in list_response.json()
    }
    assert saved_platforms["ZZZ"]["pf_rapide"] == "ZONE TEST"


def test_platforms_saved_endpoint_updates_existing_platform() -> None:
    first_response = client.post(
        "/platforms/saved",
        json={
            "code_erp": "upd",
            "pf_rapide": "AVANT",
            "pf_lente": "AVANT LENT",
            "actif": True,
            "lent_avec_pourcentage": False,
        },
    )
    second_response = client.post(
        "/platforms/saved",
        json={
            "code_erp": "UPD",
            "pf_rapide": "APRES",
            "pf_lente": "APRES LENT",
            "actif": False,
            "lent_avec_pourcentage": True,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == {
        "code_erp": "UPD",
        "pf_rapide": "APRES",
        "pf_lente": "APRES LENT",
        "actif": False,
        "lent_avec_pourcentage": True,
    }


def test_platforms_saved_endpoint_rejects_empty_code() -> None:
    response = client.post(
        "/platforms/saved",
        json={
            "code_erp": "   ",
            "pf_rapide": "VIDE",
            "pf_lente": "VIDE LENT",
            "actif": True,
            "lent_avec_pourcentage": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "code_erp est obligatoire"
