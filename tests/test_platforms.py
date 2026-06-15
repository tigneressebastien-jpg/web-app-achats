from __future__ import annotations

import pytest

from app.services.platform_service import (
    PlatformNotFoundError,
    PlatformParam,
    lire_plateformes_dynamiques,
    mapper_code_erp_plateformes,
)


def test_lire_plateformes_dynamiques_depuis_defaults() -> None:
    plateformes = lire_plateformes_dynamiques()

    deux_c = mapper_code_erp_plateformes("2C1", plateformes)
    scy = mapper_code_erp_plateformes("SCY", plateformes)

    assert deux_c.pf_rapide is None
    assert deux_c.pf_lente == "2C LOG"
    assert mapper_code_erp_plateformes("CHA", plateformes).pf_lente == "CHAPO LENT"
    assert scy.pf_rapide == "ST CYR"
    assert scy.lent_avec_pourcentage is False


def test_lire_plateformes_dynamiques_depuis_lignes_metier() -> None:
    plateformes = lire_plateformes_dynamiques(
        [
            {
                "Code ERP": "NME",
                "PF rapide": "SUD LOG",
                "PF lente": "SUD LOG LENT",
                "Actif": "oui",
                "Lent avec %": "x",
            }
        ]
    )

    plateforme = mapper_code_erp_plateformes("nme", plateformes)

    assert plateforme == PlatformParam(
        code_erp="NME",
        pf_rapide="SUD LOG",
        pf_lente="SUD LOG LENT",
        actif=True,
        lent_avec_pourcentage=True,
    )


def test_mapper_code_erp_refuse_une_plateforme_inactive() -> None:
    plateformes = [
        PlatformParam(
            code_erp="TLS",
            pf_rapide="TOULOUSE",
            pf_lente="TOULOUSE LENT",
            actif=False,
            lent_avec_pourcentage=True,
        )
    ]

    with pytest.raises(PlatformNotFoundError):
        mapper_code_erp_plateformes("TLS", plateformes)
