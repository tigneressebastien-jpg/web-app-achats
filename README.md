# Achats Fruits et Legumes - V1 Backend

V1 technique pour remplacer progressivement le fichier Excel/VBA d'achats fruits et legumes par une application web.

Cette premiere etape contient uniquement le backend FastAPI, les fonctions metier pures et les tests unitaires.  
Le frontend complet n'est pas encore cree.

## Perimetre V1

- Acheteur cible initial : Seb.
- Import ERP prevu depuis Excel ou CSV.
- Plateformes dynamiques via table de parametres.
- Application des consignes principales.
- Calcul simple du besoin rapide/lent.
- Projection camions en semaine glissante.
- Regle Lunes/Lundi/Monday validee.
- Logs de calcul prepares dans les resultats metier.

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
  conftest.py
  test_platforms.py
  test_consignes.py
  test_consignes_api.py
  test_besoins.py
  test_calculations_api.py
  test_camions.py
  test_fournisseur_constraints.py
  test_lunes_credit_lent.py
  test_lunes_imports.py
  test_lunes_rule_maj_2026_06_13.py
  test_lunes_api.py
  test_validation_metier_v1.py

data_samples/
.github/
  workflows/
    tests.yml

README.md
```

## Backend

Le backend est construit avec :

- Python 3.12
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- Pytest

## Tests

Les tests sont executes automatiquement par GitHub Actions avec :

```bash
python -m pytest -vv --tb=short
```

Le workflow GitHub Actions est defini dans :

```text
.github/workflows/tests.yml
```

Il installe les dependances depuis :

1. `requirements.txt` si present ;
2. sinon `backend/requirements.txt` si present ;
3. sinon un fallback minimal.

## API backend actuelle

Les routes FastAPI sont enregistrees dans :

```text
backend/app/main.py
```

### Statut

```http
GET /health
```

### Plateformes dynamiques

Les plateformes ERP sont gerees par les endpoints plateformes.

Objectifs couverts :

- lire les plateformes actives ;
- mapper un code ERP vers PF rapide/lente ;
- garder les plateformes dynamiques en base SQLite.

Exemples de mapping :

```text
SMT -> SAMATERRA / SAMATERRA LENT
CHA -> CHAPO / CHAPO LENT
SCY -> ST CYR / ST CYR LENT
NME -> SUD LOG / SUD LOG LENT
```

### Imports ERP

```http
POST /imports/erp/preview
POST /imports/erp/save
GET /imports/batches
GET /imports/batches/{batch_id}
```

- `preview` lit un fichier ERP sans l'enregistrer.
- `save` lit le fichier ERP et enregistre un batch exploitable ensuite.
- Les imports supportent CSV et Excel selon le service d'import.
- Les anomalies d'import sont renvoyees dans la reponse.

### Calculs Seb

```http
POST /calculations/seb/simple
POST /calculations/seb/from-erp-import
POST /calculations/seb/from-import-batch/{batch_id}
GET /calculations/runs
GET /calculations/runs/{run_id}
```

- `simple` calcule a partir de lignes JSON.
- `from-erp-import` importe un fichier puis calcule directement.
- `from-import-batch/{batch_id}` calcule depuis un batch ERP deja sauvegarde.
- L'option `persist=true` permet de sauvegarder un run de calcul.
- Les erreurs metier de calcul sont renvoyees en HTTP 400 avec l'article concerne.

### Consignes

```http
POST /consignes/apply
POST /consignes/saved
GET /consignes/saved
POST /consignes/import/csv/preview
POST /consignes/import/csv
```

- `apply` applique une consigne sur un solde import donne.
- `saved` permet de saisir ou mettre a jour une consigne sauvegardee.
- `GET /consignes/saved` liste les consignes, avec filtres `acheteur`, `code_article`, `plateforme`.
- `import/csv/preview` lit un CSV de consignes sans enregistrer les lignes.
- `import/csv` enregistre les lignes valides et renvoie les anomalies.

Colonnes CSV consignes reconnues :

```text
code_article;plateforme;texte_consigne;valeur_consigne;acheteur
```

Aliases acceptes par le parseur :

```text
code_article / code article / article / C
plateforme / pf / plateforme cible
texte_consigne / texte consigne / consigne
valeur_consigne / valeur consigne / valeur
acheteur / buyer
```

### Exports

```http
POST /exports/calculation-results.csv
POST /exports/calculation-results.xlsx
GET /exports/calculation-runs/{run_id}.csv
GET /exports/calculation-runs/{run_id}.xlsx
```

- Les exports CSV/XLSX fonctionnent sur des resultats transmis ou sur un run persiste.
- Les exports XLSX utilisent `openpyxl`.

### Camions

```http
POST /camions/projection
GET /camions/platforms/excel
```

- `projection` applique la semaine glissante sans arrondir les jours intermediaires.
- `platforms/excel` expose le mapping equivalent aux cellules M8:M14 du fichier Excel.

### Fournisseurs

Les endpoints fournisseurs couvrent le remplissage simple en respectant les contraintes metier deja testees :

- ne pas remplir une plateforme dont `COMMANDES = 0` ;
- respecter `PF_INTERDITE` strictement ;
- utiliser `PAS_COLIS` si renseigne, sinon la palettisation ;
- ne pas depasser le besoin sur les plateformes lentes.

## Regle Lunes / Lundi / Monday

La regle Lunes finale validee dans Excel/VBA est implementee dans une fonction metier pure.

Fonction officielle :

```python
compute_lunes_credit_from_week_lent
```

Chemin :

```text
backend/app/services/lunes_service.py
```

Cette fonction est la source de verite pour la regle Lunes.

### Formule metier

Pour les imports Lunes/Lundi/Monday, le besoin rapide ne vient pas directement du besoin ERP rapide brut.

Il est recalcule depuis le besoin lent de l'onglet Semaine, reconstitue a 100 %, puis diminue des achats deja faits en lent sur l'onglet Semaine.

```text
besoin_100 = commandes_lent_semaine / taux_lent
rapide_lunes_final = max(0, besoin_100 - achats_lent_semaine)
```

Si les achats lents semaine depassent le besoin reconstitue a 100 % :

```text
surplus_lent_semaine = achats_lent_semaine - besoin_100
lent_lunes_final = max(0, lent_lunes_initial - surplus_lent_semaine)
```

Sinon :

```text
surplus_lent_semaine = 0
lent_lunes_final = lent_lunes_initial
```

Le champ `besoin_erp_rapide_brut` peut etre transmis mais il est ignore dans ce calcul.

## Endpoint API - Credit Lent Lunes

La regle Lunes est exposee par l'endpoint suivant :

```http
POST /lunes/credit-lent
```

Chemin de la route :

```text
backend/app/api/routes_lunes.py
```

Cette route ne duplique pas la logique metier. Elle appelle uniquement :

```python
compute_lunes_credit_from_week_lent
```

## Exemple de requete

```json
{
  "pf_lente": "ST CYR LENT",
  "commandes_lent_semaine": 163,
  "achats_lent_semaine": 110,
  "taux_lent": 1.0,
  "lent_lunes_initial": 0,
  "besoin_erp_rapide_brut": 71
}
```

## Exemple de reponse

```json
{
  "pf_lente": "ST CYR LENT",
  "besoin_100": 163,
  "rapide_lunes_final": 53,
  "surplus_lent_semaine": 0,
  "lent_lunes_initial": 0,
  "lent_lunes_final": 0,
  "detail_calcul": "besoin_100=163.0/1.0; rapide_lunes_final=max(0,163.0-110.0); surplus_lent_semaine=max(0,110.0-163.0); lent_lunes_final=max(0,0.0-0); besoin_erp_rapide_brut ignored"
}
```

## Exemple avec surplus

Requete :

```json
{
  "pf_lente": "CHAPO LENT",
  "commandes_lent_semaine": 100,
  "achats_lent_semaine": 250,
  "taux_lent": 0.5,
  "lent_lunes_initial": 80,
  "besoin_erp_rapide_brut": 71
}
```

Resultat attendu :

```json
{
  "pf_lente": "CHAPO LENT",
  "besoin_100": 200,
  "rapide_lunes_final": 0,
  "surplus_lent_semaine": 50,
  "lent_lunes_initial": 80,
  "lent_lunes_final": 30,
  "detail_calcul": "..."
}
```

## Cas metier valides

### ST CYR LENT

```text
commandes_lent_semaine = 163
achats_lent_semaine = 110
taux_lent = 1.00

besoin_100 = 163 / 1.00 = 163
rapide_lunes_final = 163 - 110 = 53
```

### CHAPO LENT

```text
commandes_lent_semaine = 110
achats_lent_semaine = 110
taux_lent = 0.50

besoin_100 = 110 / 0.50 = 220
rapide_lunes_final = 220 - 110 = 110
```

### SUD LOG LENT

```text
commandes_lent_semaine = 85
achats_lent_semaine = 55
taux_lent = 0.50

besoin_100 = 85 / 0.50 = 170
rapide_lunes_final = 170 - 55 = 115
```

## Tests de validation

La fonction metier pure est couverte par :

```text
tests/test_lunes_credit_lent.py
tests/test_lunes_rule_maj_2026_06_13.py
```

L'endpoint API est couvert par :

```text
tests/test_lunes_api.py
```

Les tests verifient notamment :

- ST CYR LENT : resultat rapide Lunes = 53.
- CHAPO LENT : resultat rapide Lunes = 110.
- SUD LOG LENT : resultat rapide Lunes = 115.
- Gestion du surplus achats lents semaine.
- Normalisation du taux : `50` devient `0.50`.
- Refus d'un taux inferieur ou egal a `0`.
- Anti-regression : le besoin ERP rapide brut est ignore.

## Plateformes dynamiques V1

Exemples de mapping ERP prevus :

```text
2C1 -> 2C LOG
CHA -> CHAPO / CHAPO LENT
SCY -> ST CYR / ST CYR LENT
NME -> SUD LOG / SUD LOG LENT
TLS -> TOULOUSE / TOULOUSE LENT
SMT -> SAMATERRA / SAMATERRA LENT
```

## Semaine glissante camions

Les projections camions utilisent les coefficients valides :

```text
Lundi -> Mardi : 0.840
Mardi -> Mercredi : 0.935
Mercredi -> Jeudi : 1.467
Jeudi -> Vendredi : 1.216
Vendredi -> Samedi : 0.664
Samedi -> Lundi : 0.894
```

Regle importante :

```text
Ne pas arrondir entre les jours.
Arrondir seulement l'affichage final des camions.
```

Exemple :

```text
Base samedi = 40
Lundi = 40 * 0.894 = 35.76
Mardi = 35.76 * 0.840 = 30.0384
```

## Etat actuel

- Backend : en cours, avec routes FastAPI principales disponibles.
- Imports ERP : preview, sauvegarde en batch, calcul depuis batch.
- Consignes : application, saisie sauvegardee, preview CSV, import CSV.
- Calculs : Seb simple, depuis fichier ERP, depuis batch persiste.
- Exports : CSV et XLSX pour resultats et runs persistants.
- Tests unitaires/API : actifs.
- GitHub Actions : actif.
- Endpoint Lunes : cree.
- Frontend : non commence.
