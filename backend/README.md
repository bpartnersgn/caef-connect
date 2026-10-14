# CAEF Connect, backend

Monolithe modulaire Django 5.2 et Django REST framework, PostgreSQL 16, Celery et Redis, stockage compatible S3. Il suit le DAT (doc 06), le modèle de données (doc 05), le SFD (doc 03) et la Matrice des rôles (doc 04).

## Démarrer en local

```bash
cp .env.example .env            # puis remplir les secrets (jamais dans le dépôt)
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py generer_donnees_fictives
```

L'API est servie sous `http://localhost:8080/api/v1/`, et son schéma OpenAPI sous `/api/v1/schema/`.

La commande `generer_donnees_fictives` crée des données **entièrement fictives** :
- deux centres, CAEF Cameroun (CMR) et un « Centre de test B » marqué fictif ;
- un compte par rôle (`rc.cmr`, `aa.cmr`, `cpt.cmr`, `vb.cmr`, `dg.direction`…).

Elle est refusée en production. Aucune donnée réelle de bénéficiaire ne doit se trouver hors production : ni sur un poste, ni dans le dépôt, ni dans un échange avec une IA.

## Tests

```bash
pip install -r requirements-dev.txt
pytest            # PostgreSQL requis (variables POSTGRES_*)
ruff check caef config conftest.py
```

`caef/habilitations/tests/test_matrice.py` vérifie deux choses :
- `matrice.yaml` reproduit le document 04 ;
- chaque cellule rôle × objet × action est appliquée par le moteur de droits, dans le centre de l'utilisateur et dans un autre centre.

`caef/commun/tests/test_scenarios.py` couvre les règles transverses :
- séparation des tâches ;
- refus hors périmètre journalisés ;
- mois verrouillé ;
- idempotence de la synchronisation ;
- notifications Mobile Money signées et idempotentes ;
- valeurs « non renseigné ».

## Organisation

| Application | Rôle |
| --- | --- |
| `habilitations` | Matrice (`matrice.yaml`, seule source des droits), affectations, intérims, modules par centre |
| `identite` | Comptes nominatifs, Argon2, double authentification TOTP |
| `journal` | Journal d'audit en ajout seul, écrit dans la transaction de l'action |
| `beneficiaires`, `formations`, `documents` | Dossiers, candidatures, doublons, sessions, présences, attestations, pièces jointes |
| `partenaires`, `conventions` | Pipeline, propositions et circuit de validation, conventions, engagements, contributions |
| `boutique`, `facturation`, `paiements` | Ventes, caisse, inventaire, reversements, échéances, Mobile Money |
| `pilotage` | Clôture mensuelle et verrouillage, indicateurs, rapports |
| `synchronisation` | Appareils, opérations hors ligne rejouées par les services, journal des changements |

Dans chaque application, `services.py` porte les règles métier, `api.py` les vues REST et `taches.py` les tâches Celery. Les choix faits là où les spécifications se taisent sont dans [DECISIONS.md](DECISIONS.md).
