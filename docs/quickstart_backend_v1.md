# Quickstart Backend V1

## Objectif

Tester rapidement le flux V1 sans frontend :

1. importer ou saisir des consignes ERP ;
2. importer un fichier ERP ;
3. calculer les besoins Seb ;
4. exporter le resultat.

## Fichiers d'exemple

```text
data_samples/consignes_seb_v1.csv
data_samples/erp_seb_v1.csv
```

## Lancer l'API

Depuis le dossier `backend/` :

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger sera disponible sur :

```text
http://127.0.0.1:8000/docs
```

## Flux minimal recommande

### 1. Importer les consignes ERP

Utiliser :

```http
POST /consignes/import/csv
```

Fichier conseille :

```text
data_samples/consignes_seb_v1.csv
```

Rappel : la consigne est normalisee sur la cle ERP :

```text
acheteur + code_article + plateforme_erp
```

Exemple :

```text
CHAPO ou CHAPO LENT -> CHA
SAMATERRA -> SMT
ST CYR -> SCY
```

### 2. Importer le fichier ERP

Utiliser :

```http
POST /imports/erp/save
```

Fichier conseille :

```text
data_samples/erp_seb_v1.csv
```

La reponse renvoie un `batch_id`.

### 3. Calculer depuis le batch ERP

Utiliser :

```http
POST /calculations/seb/from-import-batch/{batch_id}
```

Avec par exemple :

```text
buyer=Seb
coeff_lent=1
pct_lent=1
persist=true
```

Effet attendu sur `ART-FLOW-001` :

```text
ERP source = CHA
I_IMPORT = -100
Consigne ERP = +150 stock
I_CONSIGNES = 20
solde_corrige = -100 + (150 - 20) = 30
besoin rapide CHAPO = 0
surplus positif = 30
besoin lent CHAPO LENT reduit selon la regle validee
```

### 4. Exporter le resultat

Si le calcul a ete lance avec `persist=true`, la reponse renvoie un `run_id`.

Utiliser ensuite :

```http
GET /exports/calculation-runs/{run_id}.csv
GET /exports/calculation-runs/{run_id}.xlsx
```

## Endpoints utiles

```text
POST /consignes/saved
GET /consignes/saved
POST /consignes/import/csv/preview
POST /consignes/import/csv
POST /imports/erp/preview
POST /imports/erp/save
POST /calculations/seb/simple
POST /calculations/seb/from-erp-import
POST /calculations/seb/from-import-batch/{batch_id}
GET /calculations/runs
GET /calculations/runs/{run_id}
GET /exports/calculation-runs/{run_id}.csv
GET /exports/calculation-runs/{run_id}.xlsx
```

## Ce qui est deja verrouille

- normalisation des consignes sur `plateforme_erp` ;
- application unique de la consigne sur la ligne ERP source ;
- pas de double application sur PF rapide + PF lente ;
- split rapide/lent seulement apres correction du solde ERP.
