from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_v1_flow_saved_erp_consigne_import_batch_calculation_and_export() -> None:
    save_consigne_response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": "ART-FLOW-001",
            "plateforme_erp": "CHAPO",
            "texte_consigne": "+150 stock",
            "valeur_consigne": 20,
        },
    )

    assert save_consigne_response.status_code == 200
    assert save_consigne_response.json()["plateforme_erp"] == "CHA"

    erp_csv = "C;D;F;G;I\nART-FLOW-001;Article flux complet;CHA;100;-100\n"
    save_import_response = client.post(
        "/imports/erp/save",
        files={"file": ("erp.csv", erp_csv, "text/csv")},
    )

    assert save_import_response.status_code == 200
    batch_id = save_import_response.json()["batch_id"]

    calculation_response = client.post(
        f"/calculations/seb/from-import-batch/{batch_id}",
        params={"buyer": "Seb", "coeff_lent": 1, "pct_lent": 1, "persist": True},
    )

    assert calculation_response.status_code == 200
    calculation_payload = calculation_response.json()
    assert calculation_payload["batch_id"] == batch_id
    assert calculation_payload["run_id"] is not None
    assert len(calculation_payload["results"]) == 1

    result = calculation_payload["results"][0]
    assert result["code_article"] == "ART-FLOW-001"
    assert result["code_plateforme_erp"] == "CHA"
    assert result["pf_rapide"] == "CHAPO"
    assert result["pf_lente"] == "CHAPO LENT"
    assert result["solde_corrige"] == 30
    assert result["besoin_rapide"] == 0
    assert result["surplus_positif"] == 30
    assert result["besoin_lent_brut"] == 100
    assert result["besoin_lent"] == 70
    assert result["besoin_total"] == 70
    assert result["consigne_regle"] == "AJOUT_STOCK"
    assert result["logs"] == ["Consigne AJOUT_STOCK appliquee: -100.0 -> 30.0"]

    run_id = calculation_payload["run_id"]
    run_detail_response = client.get(f"/calculations/runs/{run_id}")
    assert run_detail_response.status_code == 200
    run_detail = run_detail_response.json()
    assert run_detail["results"][0]["consigne_regle"] == "AJOUT_STOCK"
    assert run_detail["results"][0]["pf_rapide"] == "CHAPO"
    assert run_detail["results"][0]["pf_lente"] == "CHAPO LENT"

    export_response = client.get(f"/exports/calculation-runs/{run_id}.csv")
    assert export_response.status_code == 200
    assert "ART-FLOW-001;Article flux complet;CHA;CHAPO;CHAPO LENT" in export_response.text
    assert ";0.0;70.0;" in export_response.text


def test_v1_flow_saved_erp_consigne_direct_file_calculation() -> None:
    save_consigne_response = client.post(
        "/consignes/saved",
        json={
            "acheteur": "Seb",
            "code_article": "ART-FLOW-002",
            "plateforme_erp": "CHA",
            "texte_consigne": "+150 stock",
            "valeur_consigne": 20,
        },
    )

    assert save_consigne_response.status_code == 200
    assert save_consigne_response.json()["plateforme_erp"] == "CHA"

    erp_csv = "C;D;F;G;I\nART-FLOW-002;Article flux direct;CHA;100;-100\n"
    calculation_response = client.post(
        "/calculations/seb/from-erp-import",
        data={"buyer": "Seb", "coeff_lent": "1", "pct_lent": "1", "persist": "true"},
        files={"file": ("erp.csv", erp_csv, "text/csv")},
    )

    assert calculation_response.status_code == 200
    calculation_payload = calculation_response.json()
    assert calculation_payload["filename"] == "erp.csv"
    assert calculation_payload["source_type"] == "csv"
    assert calculation_payload["import_row_count"] == 1
    assert calculation_payload["import_anomalies"] == []
    assert calculation_payload["run_id"] is not None

    result = calculation_payload["results"][0]
    assert result["code_article"] == "ART-FLOW-002"
    assert result["code_plateforme_erp"] == "CHA"
    assert result["pf_rapide"] == "CHAPO"
    assert result["pf_lente"] == "CHAPO LENT"
    assert result["solde_corrige"] == 30
    assert result["besoin_rapide"] == 0
    assert result["surplus_positif"] == 30
    assert result["besoin_lent_brut"] == 100
    assert result["besoin_lent"] == 70
    assert result["besoin_total"] == 70
    assert result["consigne_regle"] == "AJOUT_STOCK"
