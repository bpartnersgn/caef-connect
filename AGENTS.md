# Consignes pour les agents (Claude, Codex, etc.)

Les spécifications sont dans `docs/` (03 SFD, 04 Matrice, 05 modèle de données, 06 DAT, 08 plan de tests). Le backend est dans `backend/` : voir `backend/README.md` et `backend/DECISIONS.md`.

## Règles non négociables

1. **Périmètre :**
   - le filtre de centre est appliqué côté serveur, dans la couche d'accès aux données (`caef/commun/api.py`, `q_perimetre`) ;
   - tout refus est journalisé.
2. **Droits :**
   - ils viennent uniquement de `caef/habilitations/matrice.yaml`, transcrit du doc 04 ;
   - pas de droit en dur ;
   - dans le doute, refuser.
3. **Journal :**
   - toute action sensible est journalisée dans la même transaction ;
   - le journal est immuable.
4. **Montants :**
   - promis, signé, reçu et exécuté sont des montants distincts ;
   - le financier et le « en nature » ne s'additionnent jamais.
5. **Déclaratif et vérifié :**
   - ils restent séparés ;
   - une contribution n'est « reçue » qu'avec un justificatif ;
   - qui saisit ne valide pas.
6. **Valeur manquante :** elle s'affiche « non renseigné », jamais 0.
7. **Données réelles :**
   - aucune hors production ;
   - en développement et en test, données fictives seulement (`caef/commun/fictif.py`) ;
   - jamais de dossier réel sur un poste, dans le dépôt ou dans une conversation avec une IA.
8. **Comptes et documents :**
   - comptes nominatifs ;
   - TOTP pour les rôles privilégiés ;
   - documents servis par lien signé de courte durée, après contrôle des droits.
9. **Collecte et rapports :**
   - pas de donnée sensible collectée par défaut ;
   - aucun nom de bénéficiaire dans les rapports partenaires.
10. **Secrets :**
    - aucun dans le code ;
    - clés et mots de passe en variables d'environnement seulement.
11. **Clôture mensuelle :**
    - une seule source par montant ;
    - la clôture est vérifiée par le CPT et validée par le RC, ou par le RA en intérim ;
    - un mois validé est verrouillé ;
    - les corrections sont des régularisations datées du mois courant.
12. **Hors ligne :**
    - l'appareil propose, le serveur décide ;
    - les opérations sont immuables (UUID d'appareil) et rejouées par les mêmes services ;
    - les doublons sont ignorés ;
    - aucun champ restreint (R) n'est envoyé à un appareil.
13. **Paiements :**
    - seul l'opérateur confirme un paiement ;
    - les notifications sont signées et idempotentes ;
    - le montant ne vient jamais du client ;
    - aucun code PIN n'est manipulé ;
    - CAEF ne détient jamais de fonds.

## Façon de travailler

- Les règles métier vivent dans `services.py`. Les vues `api.py` lisent la requête, appellent un service, puis sérialisent la réponse.
- Avant de pousser : `ruff check caef config conftest.py` puis `pytest` dans `backend/`.
- Un point ouvert devient un paramètre (`settings.CAEF`), et la décision est notée dans `backend/DECISIONS.md`.
- Langue du code, des messages et de la documentation : français.
