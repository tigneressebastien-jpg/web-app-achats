# Achats Fruits et Legumes - V1 Backend

V1 technique pour remplacer progressivement le fichier Excel/VBA d'achats fruits
et legumes par une application web. Cette premiere etape contient uniquement le
backend FastAPI, les fonctions metier pures et les tests unitaires.

## Perimetre V1

- Acheteur cible initial : Seb.
- Import ERP prevu depuis Excel ou CSV.
- Plateformes dynamiques via table de parametres.
- Application des consignes principales.
- Calcul simple du besoin rapide/lent.
- Projection camions en semaine glissante.
- Logs de calcul prepares dans les resultats metier.

Le frontend complet n'est pas encore cree.

## Structure

```text
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    api/
    services/
    seed/
  requirements.txt

tests/
  test_platforms.py
  test_consignes.py
  test_besoins.py
  test_camions.py

data_samples/
  plateformes_sample.csv
  erp_sample.csv
  consignes_sample.csv
```

## Hypotheses metier encodees

- Le besoin import de base convertit `solde_previsionnel_j1`, equivalent a la
  colonne ERP I, avec la formule `max(-I, 0)`. Un solde negatif represente un
  manque a couvrir.
- Si le solde corrige est negatif, `besoin_rapide = ABS(solde_corrige)`.
- Si le solde corrige est positif, `besoin_rapide = 0` et
  `surplus_positif = solde_corrige`.
- Le besoin lent semaine vaut `G * coeff_lent`, puis est multiplie par
  `pct_lent` uniquement si `lent_avec_pourcentage` est vrai.
- Le surplus positif reduit le lent final :
  `besoin_lent_final = MAX(0, besoin_lent_brut - surplus_positif)`.
- Les consignes sont appliquees avant le calcul rapide/surplus/lent.
- Les coefficients camions ne sont jamais arrondis entre les jours ; seul
  `camions_affichage` est arrondi au superieur pour l'affichage final.
- Pour les imports Lunes/Lundi/Monday, le rapide est recalcule depuis le lent
  semaine reconstitue a 100 % :
  `besoin_100 = COMMANDES_PF_LENTE_SEMAINE / taux_lent`, puis
  `rapide_lunes = MAX(0, besoin_100 - ACHATS_PF_LENTE_SEMAINE)`.
  Cette regle est la source de verite alignee sur Excel/VBA `Module5`,
  `Module6` et `Module11`. `ST CYR LENT` utilise `taux_lent = 1.00`,
  `CHAPO LENT` et `SUD LOG LENT` utilisent `pct_lent`, et les PF lentes
  dynamiques doivent fournir leur `taux_lent` parametre.

## Installation backend

```powershell
cd "C:\Users\stigneres\OneDrive - PROSOL GESTION\Documents\web app"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

## Lancer les tests

```powershell
pytest
```

Si Python est bloque localement, les tests sont executes par GitHub Actions via
`.github/workflows/tests.yml` a chaque `push`, `pull_request` ou lancement manuel
`workflow_dispatch`.

## Lancer l'API

```powershell
cd backend
uvicorn app.main:app --reload
```

Endpoints initiaux :

- `GET /health`
- `GET /platforms/defaults`
- `POST /calculations/seb/simple`
