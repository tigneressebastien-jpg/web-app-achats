from __future__ import annotations

from app.services.export_service import calculation_results_to_csv


def test_calculation_results_to_csv_uses_excel_friendly_semicolon_format() -> None:
    csv_content = calculation_results_to_csv(
        [
            {
                "code_article": "ART-SMT-001",
                "libelle_article": "Article test SMT",
                "code_plateforme_erp": "SMT",
                "pf_rapide": "SAMATERRA",
                "pf_lente": "SAMATERRA LENT",
                "solde_corrige": -1000,
                "besoin_rapide": 1000,
                "besoin_lent": 0,
                "besoin_lent_brut": 0,
                "surplus_positif": 0,
                "besoin_total": 1000,
                "consigne_regle": None,
                "logs": ["log 1", "log 2"],
            }
        ]
    )

    lines = csv_content.splitlines()

    assert lines[0] == (
        "code_article;libelle_article;code_plateforme_erp;pf_rapide;"
        "pf_lente;solde_corrige;besoin_rapide;besoin_lent;"
        "besoin_lent_brut;surplus_positif;besoin_total;consigne_regle;logs"
    )
    assert lines[1] == (
        "ART-SMT-001;Article test SMT;SMT;SAMATERRA;SAMATERRA LENT;"
        "-1000;1000;0;0;0;1000;;log 1 | log 2"
    )


def test_calculation_results_to_csv_writes_only_header_for_empty_results() -> None:
    csv_content = calculation_results_to_csv([])

    assert csv_content == (
        "code_article;libelle_article;code_plateforme_erp;pf_rapide;"
        "pf_lente;solde_corrige;besoin_rapide;besoin_lent;"
        "besoin_lent_brut;surplus_positif;besoin_total;consigne_regle;logs\n"
    )
