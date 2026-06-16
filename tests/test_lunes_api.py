from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_lunes_credit_endpoint_returns_validated_result() -> None:
    response = client.post(
        "/lunes/credit-lent",
        json={
            "pf_lente": "ST CYR LENT",
            "commandes_lent_semaine": 163,
            "achats_lent_semaine": 110,
            "taux_lent": 1.0,
            "lent_lunes_initial": 0,
            "besoin_erp_rapide_brut": 71,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "pf_lente": "ST CYR LENT",
        "besoin_100": 163,
        "rapide_lunes_final": 53,
        "surplus_lent_semaine": 0,
        "lent_lunes_initial": 0,
        "lent_lunes_final": 0,
        "detail_calcul": (
            "besoin_100=163.0/1.0; "
            "rapide_lunes_final=max(0,163.0-110.0); "
            "surplus_lent_semaine=max(0,110.0-163.0); "
            "lent_lunes_final=max(0,0.0-0); "
            "besoin_erp_rapide_brut ignored"
        ),
    }


def test_lunes_credit_endpoint_returns_400_for_invalid_rate() -> None:
    response = client.post(
        "/lunes/credit-lent",
        json={
            "pf_lente": "CHAPO LENT",
            "commandes_lent_semaine": 110,
            "achats_lent_semaine": 110,
            "taux_lent": 0,
            "lent_lunes_initial": 0,
        },
    )

    assert response.status_code == 400
    assert "taux_lent" in response.json()["detail"]
