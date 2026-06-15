from __future__ import annotations

from app.services.fournisseur_service import (
    calculer_remplissage_fournisseur,
    choisir_pas_remplissage,
)


def test_fournisseur_ne_remplit_jamais_une_pf_commandes_zero() -> None:
    chapo = calculer_remplissage_fournisseur(
        plateforme="CHAPO",
        commandes=0,
        besoin=100,
        palettisation=10,
    )
    st_cyr = calculer_remplissage_fournisseur(
        plateforme="ST CYR",
        commandes=100,
        besoin=100,
        palettisation=10,
    )

    assert chapo.quantite == 0
    assert chapo.raison == "COMMANDES_ZERO"
    assert st_cyr.quantite > 0


def test_fournisseur_respecte_pf_interdite_stricte() -> None:
    result = calculer_remplissage_fournisseur(
        plateforme="CHAPO",
        commandes=100,
        besoin=100,
        palettisation=10,
        pf_interdite="CHAPO",
    )

    assert result.quantite == 0
    assert result.raison == "PF_INTERDITE"


def test_fournisseur_pas_colis_prioritaire_sur_palettisation() -> None:
    pas = choisir_pas_remplissage(palettisation=144, pas_colis=48)
    result = calculer_remplissage_fournisseur(
        plateforme="CHAPO",
        commandes=100,
        besoin=100,
        palettisation=144,
        pas_colis=48,
    )

    assert pas == 48
    assert result.pas_utilise == 48
    assert result.quantite == 96
