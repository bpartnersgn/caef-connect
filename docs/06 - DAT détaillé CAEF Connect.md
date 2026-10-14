# DAT détaillé CAEF Connect

Oct 12, 2026 · @Bangoura · mis à jour le 14/10/2026 (mise en œuvre du backend du lot 1)

## 1. Objet, statut et sources

Ce DAT détaille l'architecture cible du DAT v1.0 pour le MVP et propose une solution technique argumentée ; il ne fixe aucun fournisseur et n'atteste d'aucune infrastructure existante. Les choix marqués « proposé » restent soumis à la décision du comité de pilotage (section 10) et à la comparaison des offres des prestataires.

| Élément | Valeur |
| --- | --- |
| Référence proposée | CAEF-CONNECT-DAT-002, version 0.3 (13/10/2026 : hors ligne d'abord et paiements Mobile Money ; 14/10/2026 : mise en œuvre du backend du lot 1, sections 3.3, 4.2, 4.6 et 7.3) |
| Documents d'entrée | DAT v1.0 (architecture cible) ; PRD (exigences non fonctionnelles, section 7) ; SFD du MVP ; Modèle et dictionnaire des données ; Matrice des rôles ; demandes du porteur de projet du 13/10/2026 (hors ligne d'abord, paiements Mobile Money) |
| Périmètre | Lot 1 du pilote, qui comprend le socle, la RSE et le module boutique (A14 et H14 tranchées par le porteur de projet le 12/10/2026, à formaliser par la Direction Générale des CAEF), pour un seul centre pilote, le CAEF Cameroun (Dixinn, Conakry), qui part aujourd'hui du papier ; l'architecture accueille les lots 2 et 3 sans refonte |
| Principes repris du DAT v1.0 | Centralisation maîtrisée, modularité, sécurité dès la conception, sobriété technique, interopérabilité justifiée, traçabilité, réversibilité, évolutivité nationale, adaptation au contexte, indépendance raisonnable vis-à-vis des fournisseurs |

**Quatre contraintes guident toutes les décisions de ce document :**

1. **Hors ligne d'abord.** Le réseau et l'électricité ne sont pas garantis au centre : les opérations de terrain (présences, dossiers, ventes, encaissements) se font sans connexion sur l'appareil et se synchronisent automatiquement dès que le réseau revient ; le serveur reste la seule référence des données (OFF-01 à OFF-08, section 4.5). Les pages restent légères (NET-01).
2. **Compétences locales.** La solution doit pouvoir être maintenue par une équipe guinéenne de taille modeste, ce qui privilégie des technologies répandues et documentées en français.
3. **Coût récurrent.** Le budget d'exploitation n'est pas encore arrêté (PRD H8) ; le pilote serait financé par une offre de TIKA, à confirmer, mais les coûts récurrents devront avoir un financeur identifié avant la fin du pilote ; l'architecture doit fonctionner sur une infrastructure modeste et grandir par paliers.
4. **Argent réel.** Les paiements Mobile Money de la scolarité et des services associés passent par une passerelle d'opérateur ; CAEF Connect ne détient jamais les fonds, et seule la confirmation de l'opérateur fait d'un paiement un encaissement (PAY-01 à PAY-11, section 4.6).

## 2. Architecture cible

CAEF Connect est une seule application web, découpée en modules métier, servie derrière un proxy HTTPS et adossée à une seule base PostgreSQL ; ses écrans de terrain s'installent sur les téléphones et tablettes comme une application web progressive (PWA) qui travaille d'abord hors ligne. Ce choix vise une équipe réduite et une exploitation simple : un seul déploiement, une seule base à sauvegarder, des frontières de modules nettes qui permettront d'extraire un service plus tard si le volume l'exige.

&#91;embedded content: architecture cible · composants et flux principaux\]

Les flux principaux sont les suivants.

- **Requête utilisateur.** Le navigateur appelle Nginx en HTTPS ; Nginx termine le TLS, applique les en-têtes de sécurité et la limitation de débit, puis transmet à l'application. Chaque requête passe par le contrôle du rôle et du périmètre (centre, pays, programme) avant d'atteindre un module.
- **Écriture métier.** Le module concerné écrit dans le schéma opérationnel, dans la même transaction que l'entrée du journal d'audit.
- **Pièces jointes et PDF.** Les fichiers vont dans le stockage d'objets ; la base ne garde que les métadonnées. Le téléchargement se fait par une URL signée à durée courte, délivrée après contrôle des droits.
- **Pilotage.** Le worker recalcule chaque nuit les agrégats du schéma de pilotage à partir du schéma opérationnel ; les tableaux de bord lisent ce schéma et affichent la date du dernier calcul. Les générations de PDF et les notifications passent aussi par la file Redis, pour ne jamais bloquer une page.
- **Sauvegarde.** Les journaux de transactions PostgreSQL et les objets sont copiés en continu, chiffrés, vers un second site, pour tenir l'objectif de perte de données de 15 minutes (option 2, à valider).
- **Synchronisation.** L'application terrain enregistre chaque action dans une base locale chiffrée et un journal d'opérations ; dès que le réseau revient, elle envoie ces opérations à l'API de synchronisation, qui les applique par les mêmes services métier qu'une saisie en ligne, puis elle reçoit les changements de son périmètre (section 4.5).
- **Paiement.** Le module paiements demande un paiement à la passerelle Mobile Money ou reçoit la notification d'un paiement fait par la payeuse ; la notification signée de l'opérateur, vérifiée par le serveur, confirme l'encaissement, puis le reçu est émis et le rapprochement quotidien contrôle le tout (section 4.6).

## 3. Proposition technologique et hébergement

La proposition est une application web unique, structurée en modules, à rendu côté serveur pour le back-office et en application web progressive hors ligne pour les écrans de terrain, adossée à PostgreSQL et à un stockage d'objets compatible S3, déployée en conteneurs. Elle répond aux hypothèses H12 et H13 du PRD et reste ouverte à une offre équivalente argumentée d'un prestataire.

### 3.1 Composants proposés

| Composant | Proposition | Pourquoi | Alternative acceptable |
| --- | --- | --- | --- |
| Application | Framework web mature à rendu serveur : Django (Python) ou Laravel (PHP), selon les compétences du prestataire retenu | Authentification, formulaires, protection CSRF, ORM et traduction française intégrés ; large vivier de développeurs ; pages légères sans application JavaScript lourde | NestJS (Node) avec rendu serveur, si l'équipe le maîtrise mieux |
| Interactivité du back-office | HTML rendu serveur enrichi par une bibliothèque légère (type HTMX ou Alpine.js) | Peu de JavaScript téléchargé, compatible téléphones d'entrée de gamme | Application monopage pour tout le back-office, à éviter pour le poids des pages |
| Client terrain hors ligne | Application web progressive installable : coquille mise en cache par un service worker, écrans de terrain en composants JavaScript légers (Preact, Svelte ou Vue, selon le prestataire), base locale IndexedDB chiffrée | Travail sans réseau et synchronisation automatique (OFF-01 à OFF-08), sans magasin d'applications ni application native à maintenir | Application Android native, seulement si une fonction du téléphone l'exige ; coût de maintenance plus élevé |
| Base de données | PostgreSQL 16 ou version stable plus récente | Relationnelle, open source, contraintes riches, réplication et sauvegarde continue éprouvées | MariaDB, avec un effort de contrôle d'intégrité supplémentaire |
| Documents | Stockage d'objets compatible S3 (service managé ou MinIO auto-hébergé), chiffré | Sépare fichiers et base (DAT v1.0 couche 3) ; liens signés de courte durée | Système de fichiers chiffré sur volume dédié, pour le seul pilote |
| Tâches de fond | File de tâches avec Redis et un processus de travail | Calcul nocturne des indicateurs, imports, PDF, notifications, sans ralentir la saisie (PERF-02) | Planificateur cron simple au pilote |
| Documents PDF | Génération côté serveur à partir de modèles HTML | Rapports R-01 à R-04, reçus de boutique, attestations en lot 2 | Bibliothèque PDF native du framework |
| Frontal | Nginx en proxy inverse, TLS par certificats automatiques | HTTPS obligatoire, compression, en-têtes de sécurité | Équilibreur du fournisseur cloud |
| Déploiement | Images de conteneurs ; Docker Compose au pilote | Environnements reproductibles (MNT-01) sans complexité de Kubernetes | Kubernetes managé, seulement à l'échelle nationale si la charge le justifie |
| Supervision | Sonde de disponibilité externe, suivi des erreurs applicatives (outil auto-hébergeable), journaux centralisés | OPS-01 à coût faible | Suite de supervision du fournisseur cloud |
| Synchronisation | API de synchronisation propre (envoi des opérations, réception des changements par curseur) et journal des changements en base | Simple et auditable ; réutilise les services métier et les droits existants ; aucun second moteur de base | Bibliothèque de synchronisation open source auto-hébergée, si l'équipe la maîtrise |
| Passerelle de paiement | Interface interne « passerelle Mobile Money » avec un adaptateur par agrégateur ou opérateur, plus un adaptateur déclaratif sans opérateur | Ajouter ou changer d'opérateur sans toucher les modules métier ; repli déclaratif tant que le contrat n'est pas signé | Intégration directe de l'API d'un seul opérateur, au prix d'une dépendance plus forte |

Critères de choix appliqués (DAT v1.0 § 11) : maturité, compétences disponibles en Guinée, coût total sur cinq ans, sécurité, facilité de maintenance, documentation, portabilité des données, capacité de reporting, dépendance au fournisseur. Tous les composants proposés sont open source et remplaçables.

### 3.3 Composants mis en œuvre au lot 1 (14/10/2026)

Le backend du lot 1 (dépôt `bpartnersgn/caef-connect`, dossier `backend/`) applique la proposition de la section 3.1 avec Django. Les versions sont figées dans `backend/requirements.txt`.

| Composant | Mise en œuvre |
| --- | --- |
| Application | Python 3.13, Django 5.2, Django REST framework 3.18, servis par Gunicorn (3 processus) dans une image Docker à utilisateur non privilégié |
| Base de données | PostgreSQL 16 (pilote psycopg 3) ; schéma `pilotage` pour la table de synthèse des indicateurs |
| Documents | django-storages et boto3 vers un stockage compatible S3 (MinIO en local) ; disque local seulement si aucun compartiment n'est configuré |
| Tâches de fond | Celery 5.6 avec Redis 7 : un processus de travail et un planificateur (beat) |
| Sécurité | Mots de passe Argon2, double authentification TOTP (PyOTP) avec codes de secours, champs restreints chiffrés (Fernet), sessions de 30 minutes d'inactivité et 8 heures au plus |
| API | Schéma OpenAPI 3 généré par drf-spectacular, servi sous `/api/v1/schema/` |
| Exports | Tableur (openpyxl) |
| Frontal | Nginx 1.27 en proxy inverse ; TLS terminé en amont en production |
| Écrans | Gabarits HTMX du back-office et application terrain PWA : non commencés |

Les tâches planifiées sont les suivantes (heure du serveur) :

| Tâche | Fréquence |
| --- | --- |
| Calcul des indicateurs (mois courant et mois précédent) | Chaque nuit à 1 h 00 |
| Recalcul des paires de doublons | Chaque nuit à 1 h 30 |
| Import et rapprochement des relevés de l'opérateur | Chaque nuit à 2 h 00 |
| Suspension des comptes inactifs | Chaque nuit à 3 h 00 |
| Engagements en retard, démarrage des sessions | Chaque nuit à 0 h 10 et 0 h 05 |
| Création des clôtures mensuelles | Le 1er du mois à 0 h 30 |
| Paiements « non retrouvés » | Toutes les heures, au quart |
| Alerte des appareils en retard de synchronisation | Toutes les heures |

### 3.2 Options d'hébergement

Le lieu d'hébergement reste à décider (PRD H7) ; trois options sont comparées sur les critères du DAT v1.0, sans chiffrage, qui relève des offres.

| Critère | A. Hébergeur ou centre de données en Guinée | B. Cloud international, région en Afrique | C. Cloud international, région en Europe |
| --- | --- | --- | --- |
| Souveraineté et résidence des données | Forte | Moyenne, selon le droit applicable | Plus faible, transfert hors d'Afrique à encadrer |
| Latence depuis Conakry | Faible si l'accès local est bon | Moyenne | Moyenne à élevée |
| Disponibilité et redondance | À vérifier par audit du site | Élevée, multi-zones | Élevée, multi-zones |
| Services managés (base, stockage, sauvegardes) | Souvent limités ; plus d'exploitation interne | Larges | Larges |
| Dépendance au fournisseur | Faible à moyenne | Moyenne | Moyenne |
| Compétences d'exploitation requises | Élevées | Moyennes | Moyennes |

**Recommandation de travail.** Retenir l'option qui satisfait d'abord l'avis juridique sur la résidence des données ; à conformité égale, préférer des services managés pour la base et les sauvegardes, qui réduisent le risque d'exploitation. Dans tous les cas, les sauvegardes sont copiées dans un second site ou une seconde région, et l'architecture conteneurisée permet de changer d'hébergeur sans réécriture (MNT-03). L'hébergement initial du pilote pourrait être pris en charge par TIKA dans son offre aux CAEF (option à confirmer, PRD H8) ; ce choix ne dispense pas des critères ci-dessus.

## 4. Modules applicatifs, API et intégrations

L'application est découpée en douze modules métier et cinq services transverses ; un module n'accède aux données d'un autre que par ses services publics, ce qui permettra d'en extraire un plus tard si la charge l'exige (ARC-01). Le socle est toujours actif ; les modules boutique (avec la salle d'exposition), facturation et paiements, ainsi que le volet RSE du centre, peuvent être désactivés pour un centre (section 4.7).

| Module | Responsabilité | Lot |
| --- | --- | --- |
| identite | Comptes, sessions, double authentification, réinitialisation | 1 |
| habilitations | Rôles, permissions, affectations, intérims (USR-09), modules activés par centre (ADM-08), filtre de périmètre appliqué à chaque requête | 1 |
| referentiels | Centres, zones, valeurs de référence, périodes | 1 |
| beneficiaires | Dossiers, candidatures, doublons, transferts, import | 1 |
| formations | Catalogue, sessions, séances, formateurs, inscriptions, présences, résultats | 1 |
| partenaires | Partenaires, interlocuteurs, interactions, opportunités, pipeline, fiches projet | 1 (RSE) |
| conventions | Programmes, propositions, validations, conventions, engagements, contributions | 1 (RSE) |
| pilotage | Indicateurs, tableaux de bord, rapports, exports ; clôture mensuelle du centre et état de rapprochement (SRC-01, SRC-02, SRC-04), avec verrouillage du mois validé | 1 |
| documents | Stockage, versions, liens signés, contrôle d'accès | 1 |
| boutique | Points de vente, catalogue et prix, dépôts-ventes, ventes et reçus, stock, caisse, inventaires, reversements aux productrices ; dépend de referentiels (centres), beneficiaires (productrices déposantes) et documents (pièces de reversement) ; fournit ses totaux de ventes, caisses et reversements à la clôture mensuelle (SRC-02) | 1, après le socle, en parallèle de la RSE (H14 tranchée) |
| facturation | Services payants et tarifs par centre (scolarité, examens, services associés), échéances et échéanciers, exonérations et prises en charge (section 4.6) | 1 (socle) ; mise en service avec H15 |
| paiements | Encaissements espèces et Mobile Money, passerelles, affectation aux échéances, reçus, rapprochement quotidien, remboursements ; sert aussi la boutique ; fournit ses totaux à la clôture mensuelle (SRC-02) | 1 ; parcours Mobile Money A et B avec H16 |
| Services transverses | Journal d'audit, notifications, tâches de fond, génération PDF, synchronisation hors ligne (appareils, opérations, journal des changements, conflits) | 1 |
| Réservés | parcours, insertion, entrepreneuriat, communication, creches, portails | 2 et 3 |

### 4.1 Flux et règles d'appel

Utilisateur, puis navigateur, puis proxy HTTPS, puis application (contrôleurs, puis services métier, puis accès aux données), puis PostgreSQL et stockage d'objets (DAT v1.0 § 4).

1. Le navigateur ne parle qu'à l'application ; aucune base ni aucun stockage n'est exposé sur Internet (ARC-02).
2. Chaque requête passe par un intergiciel d'authentification puis par le service habilitations, qui injecte le filtre de périmètre dans toutes les requêtes de données ; un développeur ne peut pas oublier le filtre, car l'accès aux tables métier passe par des gestionnaires de requêtes filtrés par défaut. En défense complémentaire, la sécurité au niveau des lignes de PostgreSQL est activée sur les tables nominatives.
3. Les règles de gestion (RG-\*) sont dans les services métier, jamais seulement dans l'interface.
4. Les exports et rapports appellent les mêmes services que les écrans (SEC-10).
5. Les opérations venues de l'application terrain passent par les mêmes contrôles d'accès, filtres de périmètre et services métier qu'une saisie en ligne ; aucune règle n'est appliquée seulement sur l'appareil (OFF-04).
6. Avant le filtre de périmètre, le service habilitations vérifie que le module visé est activé pour le centre concerné (table `module_centre`) ; sinon, la requête ou l'opération synchronisée est refusée avec le motif « Module non activé » et journalisée (ADM-08, RG-ADM-19).

### 4.2 API

- **Style :** REST et JSON, préfixe `/api/v1`, décrite au format OpenAPI 3 publié avec chaque version (ARC-05).
- **Usage au MVP :** interne (synchronisation de l'application terrain, listes dynamiques), outils d'import et réception des notifications des passerelles de paiement ; aucune autre ouverture à un tiers sans décision (H9).
- **Authentification :** session navigateur pour l'interface ; jetons à durée limitée liés à l'utilisateur et à l'appareil enrôlé pour l'application terrain (section 4.5) ; jetons de portée restreinte pour un futur client tiers ; signature vérifiée pour les notifications de paiement entrantes.
- **Protection :** validation de schéma des entrées, limitation du débit par utilisateur et par adresse, pagination obligatoire, clé d'idempotence sur les créations.
- **Versions :** une rupture de contrat crée `/api/v2` ; la version précédente est maintenue six mois au moins après annonce.
- **Environnement de test :** l'API de préproduction, avec données fictives, sert aux intégrateurs.

**Mise en œuvre au lot 1 (14/10/2026).** L'API est servie sous `/api/v1/`, son schéma OpenAPI 3 sous `/api/v1/schema/`. Deux authentifications sont acceptées : la session du navigateur (cookie sécurisé, protection CSRF) et le jeton d'appareil enrôlé, qui n'ouvre que les routes de synchronisation et est refusé partout ailleurs. Le débit est limité à 600 requêtes par minute et par utilisateur, 60 par adresse non authentifiée et 10 tentatives de connexion par minute (paramètres `CAEF_DEBIT_*`). Les listes sont paginées par 25. Chaque vue déclare l'objet de la Matrice qu'elle expose ; le filtre de périmètre s'applique à toute lecture, et un identifiant hors périmètre renvoie un refus journalisé plutôt qu'un simple « introuvable ». Les vues ne portent aucune règle : elles lisent la requête, appellent le service métier et sérialisent la réponse.

Routes hors ressources :

| Route | Usage |
| --- | --- |
| `auth/connexion/`, `auth/deconnexion/`, `auth/moi/` | Session de l'utilisateur |
| `auth/double-auth/<etape>/`, `auth/mot-de-passe/` | Enrôlement et vérification TOTP ; changement du mot de passe |
| `documents/telecharger/<jeton>/` | Téléchargement par lien signé de courte durée (300 secondes par défaut), après contrôle des droits |
| `paiements/notifications/<fournisseur>/` | Notifications des passerelles : signature invalide refusée (401) et journalisée, doublon accepté (200) sans effet |
| `synchronisation/operations/` | Envoi des opérations de l'appareil par lots |
| `synchronisation/changements/` | Réception des changements par curseur |
| `synchronisation/rejets/` | « Mes rejets » de l'appareil |

Ressources : toutes offrent la lecture en liste (`GET`), et en détail sauf `matrice`, `notifications` et `documents`, dans la limite des droits et du périmètre ; la colonne « Écriture » indique la création ou la modification directe, et la dernière colonne les actions métier, appelées en `POST` sauf mention contraire.

| Ressource | Écriture | Actions métier |
| --- | --- | --- |
| **Administration** | | |
| `/api/v1/utilisateurs/` | POST (création) | sur un objet : `statut` (POST), `reinitialiser-mot-de-passe` (POST) |
| `/api/v1/centres/` | — | sur un objet : `modules` (GET) |
| `/api/v1/referentiels/` | — | — |
| `/api/v1/zones/` | — | — |
| `/api/v1/periodes/` | — | — |
| `/api/v1/affectations/` | POST (création) | sur un objet : `retirer` (POST) |
| `/api/v1/interims/` | POST (création) | sur un objet : `interrompre` (POST) |
| `/api/v1/modules-centre/` | POST (création) | sur la liste : `operations-en-cours` (GET); sur un objet : `valider` (POST) |
| `/api/v1/matrice/` | — | — |
| `/api/v1/journal/` | — | — |
| `/api/v1/notifications/` | — | sur un objet : `lue` (POST) |
| **Bénéficiaires** | | |
| `/api/v1/beneficiaires/` | PATCH (modification) | sur la liste : `recherche-reseau` (POST), `export` (GET); sur un objet : `donnees-restreintes` (GET), `cloturer` (POST), `parcours` (GET) |
| `/api/v1/candidatures/` | POST (création) | sur un objet : `soumettre` (POST), `demander-complement` (POST), `valider` (POST), `rejeter` (POST), `mettre-en-attente` (POST), `annuler` (POST), `lever-doute-doublon` (POST) |
| `/api/v1/transferts/` | POST (création) | sur un objet : `decider` (POST) |
| `/api/v1/doublons/` | — | sur un objet : `distinctes` (POST), `fusionner` (POST) |
| `/api/v1/fusions/` | POST (création) | sur un objet : `annuler` (POST) |
| **Formations** | | |
| `/api/v1/formations/` | POST (création) | — |
| `/api/v1/formateurs/` | — | — |
| `/api/v1/sessions/` | POST (création); PATCH (modification) | sur un objet : `ouvrir` (POST), `cloturer` (POST), `annuler` (POST), `rouvrir` (POST), `seances` (POST), `inscrire` (POST), `propositions-cloture` (GET), `feuille-presence` (GET), `export` (GET) |
| `/api/v1/seances/` | — | sur un objet : `presences` (POST) |
| `/api/v1/inscriptions/` | — | sur un objet : `participation` (POST), `cheffe-de-classe` (POST), `statut-final` (POST), `evaluations` (POST), `attestation` (POST) |
| `/api/v1/presences/` | — | — |
| `/api/v1/evaluations/` | PATCH (modification) | — |
| `/api/v1/attestations/` | — | sur un objet : `annuler` (POST) |
| **Documents** | | |
| `/api/v1/documents/` | POST (création) | sur un objet : `lien` (POST) |
| **Partenariats** | | |
| `/api/v1/partenaires/` | POST (création); PATCH (modification) | sur la liste : `proches` (GET); sur un objet : `interlocuteurs` (POST), `interactions` (POST) |
| `/api/v1/interlocuteurs/` | — | — |
| `/api/v1/interactions/` | — | — |
| `/api/v1/opportunites/` | POST (création) | sur un objet : `etape` (POST), `clore` (POST), `fiches-projet` (POST), `historique` (GET) |
| `/api/v1/fiches-projet/` | POST (création) | sur un objet : `qualifier` (POST) |
| `/api/v1/programmes/` | POST (création) | — |
| `/api/v1/propositions/` | POST (création); PATCH (modification) | sur un objet : `soumettre` (POST), `circuit` (GET et POST), `marquer-soumise` (POST), `reponse` (POST) |
| `/api/v1/conventions/` | POST (création) | sur un objet : `approuver` (POST), `signer` (POST), `engagements` (POST), `contributions` (POST), `cloturer` (POST) |
| `/api/v1/engagements/` | — | sur un objet : `realise` (POST), `valider` (POST), `abandonner` (POST) |
| `/api/v1/contributions/` | — | sur la liste : `totaux` (GET); sur un objet : `reception` (POST), `valider` (POST), `rapprocher` (POST), `annuler` (POST) |
| **Boutique** | | |
| `/api/v1/points-de-vente/` | — | sur un objet : `tableau-de-bord` (GET), `montant-du` (GET) |
| `/api/v1/produits/` | POST (création) | sur un objet : `prix` (GET et POST), `entree` (POST), `sortie` (POST), `transfert` (POST) |
| `/api/v1/mouvements-stock/` | — | — |
| `/api/v1/ventes/` | POST (création) | sur la liste : `export` (GET); sur un objet : `annuler` (POST) |
| `/api/v1/caisses/` | POST (création) | sur un objet : `theoriques` (GET), `compter` (POST), `valider` (POST), `renvoyer` (POST) |
| `/api/v1/inventaires/` | POST (création) | sur un objet : `comptage` (POST), `valider` (POST), `recompter` (POST) |
| `/api/v1/reversements/` | POST (création) | sur un objet : `valider` (POST), `payer` (POST) |
| **Scolarité et paiements** | | |
| `/api/v1/services-payants/` | POST (création) | sur un objet : `tarifs` (GET et POST) |
| `/api/v1/echeances/` | — | sur un objet : `exonerations` (POST) |
| `/api/v1/exonerations/` | — | sur un objet : `decider` (POST) |
| `/api/v1/situations/` | — | — |
| `/api/v1/paiements/` | — | sur la liste : `especes` (POST), `demander` (POST), `declarer` (POST), `a-affecter` (GET), `totaux` (GET), `export` (GET); sur un objet : `affecter` (POST), `confirmer-manuellement` (POST), `remboursements` (POST) |
| `/api/v1/releves-operateur/` | POST (création) | sur un objet : `motiver` (POST) |
| `/api/v1/remboursements/` | — | sur un objet : `valider` (POST), `executer` (POST) |
| **Pilotage** | | |
| `/api/v1/clotures/` | POST (création) | sur un objet : `lignes` (GET), `pieces` (POST), `deroger-appareils` (POST), `verifier` (POST), `valider` (POST), `renvoyer` (POST) |
| `/api/v1/indicateurs/` | — | — |
| `/api/v1/fiches-indicateurs/` | — | sur un objet : `statut` (POST) |
| `/api/v1/rapports/` | POST (création) | sur un objet : `valider` (POST), `transmettre` (POST) |
| **Hors ligne** | | |
| `/api/v1/appareils/` | POST (création) | sur un objet : `revoquer` (POST), `jeton` (POST) |
| `/api/v1/conflits/` | — | sur un objet : `resoudre` (POST), `regulariser` (POST) |

### 4.3 Intégrations

Une seule intégration externe est retenue au MVP : la passerelle Mobile Money (section 4.6, PRD H9 et H16), en plus de l'import initial par fichier et des exports tableur. Toute autre intégration (messagerie SMS, courriel transactionnel, systèmes publics, bancaires ou d'identité) exigera : finalité écrite, accord institutionnel, spécifications, authentification, minimisation des données, journalisation et gestion d'erreurs (DM § 11.4, DAT v1.0 § 9) ; la passerelle Mobile Money les respecte toutes. Le module de notifications prévoit déjà une interface de canal pour brancher courriel et SMS sans modifier les modules métier ; les reçus de paiement par SMS l'utiliseront s'ils sont retenus.

### 4.4 Module boutique

Le module boutique enregistre ce que le centre vend dans sa boutique : ventes, stock, caisse et reversements aux productrices en dépôt-vente. Demandé par le porteur de projet, il est absent du DM et du CDC ; il fait partie du lot 1 livré pour le pilote (H14 tranchée par le porteur de projet le 12/10/2026, à formaliser par la Direction Générale), construit après le socle en parallèle de la RSE. Isolé derrière ses services publics, il n'a pas d'effet sur les autres modules ; le modèle prévoit l'entité point de vente dès le départ, un par centre au MVP.

| Sujet | Règle d'architecture |
| --- | --- |
| Dépendances | Lit les centres (referentiels) et les productrices déposantes (beneficiaires) ; dépose les pièces de reversement dans documents ; uniquement par leurs services publics |
| Numérotation des reçus | Une série par appareil enrôlé sur le point de vente (ex. CMR-B-000127), numérotée sur l'appareil, en ligne comme hors ligne ; unicité (point de vente, série, numéro) ; aucun trou dans une série : un numéro attribué à une vente qui échoue ou est abandonnée est consigné comme annulé (BOU-06, section 4.5) |
| Stock | Les mouvements de stock s'écrivent dans la même transaction que la vente, l'entrée, la sortie ou l'ajustement ; le stock courant est une vue ou un cache matérialisé, recalculable à tout moment depuis les mouvements, jamais un champ modifiable (BOU-04) |
| Annulation | Contre-écriture motivée et tracée (vente d'annulation liée, mouvements inverses) ; aucune suppression physique |
| Reçu | Page imprimable légère, au format A4 et ticket 80 mm, par l'impression du navigateur, et PDF ; aucun pilote d'imprimante spécifique ni terminal de caisse dédié |
| Salle d'exposition | Emplacement de stock du point de vente, à côté de la boutique : le stock est calculé par produit et par emplacement, un transfert écrit deux mouvements liés dans la même transaction, et une vente depuis la salle d'exposition suit la même série de reçus et la même caisse ; activable séparément (BOU-15, RG-BOU-16) |
| Montants | En francs guinéens (GNF), stockés en entiers |
| Règlements | Espèces, Mobile Money, virement ou chèque ; le Mobile Money passe par le module paiements (section 4.6) et n'est compté encaissé qu'une fois confirmé par l'opérateur ; sans passerelle active, il reste déclaré avec sa référence, au statut « Déclaré » |
| Connectivité | Ventes, entrées en stock et comptage de caisse fonctionnent hors ligne (section 4.5) ; le carnet de reçus papier numérotés ne sert plus que si l'appareil lui-même est hors service, avec saisie différée le jour même et le numéro papier en référence |
| Sécurité | Double authentification obligatoire pour le comptable (CPT) ; exports du journal des ventes, des clôtures et des reversements journalisés (BOU-10) |
| Source unique | Chaque montant (vente, encaissement, reversement, contribution financière reçue) est écrit une seule fois ; la vue du comptable, le tableau de bord du responsable de centre et les rapports lisent les mêmes enregistrements, sans ressaisie ni tableur parallèle (SRC-01) |
| Clôture mensuelle et verrouillage du mois | L'état de rapprochement du mois (ventes, caisses, encaissements de scolarité et de services, paiements Mobile Money rapprochés, reversements, contributions financières reçues) est généré par l'outil, vérifié par CPT puis validé par RC (ou RA en intérim), jamais par la même personne (SRC-02). Après validation, le mois est verrouillé : les services métier refusent toute écriture datée d'un mois verrouillé, et la base l'interdit aussi (déclencheur ou contrainte sur la période). Toute correction passe par une écriture de régularisation datée du mois courant, référencée au mois corrigé (RG-SRC-03) |

### 4.5 Hors ligne d'abord et synchronisation automatique

La plateforme reste utilisable sans accès à Internet et se synchronise seule dès que le réseau revient (demande du porteur de projet du 13/10/2026, à formaliser par la Direction Générale). Les écrans de terrain travaillent d'abord sur l'appareil ; le serveur reste la seule référence des données (SRC-01). Ce principe remplace la position précédente (pas de hors ligne complet, H11) et se construit dès le lot 1, car l'ajouter après coup obligerait à réécrire les écrans de saisie.

| Domaine | Possible hors ligne | En ligne seulement |
| --- | --- | --- |
| Bénéficiaires | Consulter les dossiers actifs du centre (champs utiles au rôle), créer une candidature, mettre à jour les coordonnées, photographier une pièce (envoyée plus tard) | Valider ou rejeter une candidature, fusionner, transférer, détection définitive des doublons entre centres |
| Formations | Mes sessions et séances, feuille de présence, résultats | Créer, ouvrir ou clôturer une session, dérogations |
| Boutique | Ventes et reçus, entrées en stock, sorties motivées, ouverture et comptage de caisse, comptage d'inventaire | Annulation de vente, validation de clôture de caisse et d'inventaire, reversements |
| Scolarité et paiements | Consulter les échéances d'une bénéficiaire, encaisser en espèces avec reçu, déclarer un paiement Mobile Money avec son identifiant de transaction | Demande de paiement envoyée au téléphone de la payeuse, exonération, remboursement |
| Pilotage | Tableau de bord du centre en lecture, figé et daté à la dernière synchronisation | Tableau de bord national, rapports, exports, clôture mensuelle |
| Administration et RSE | Aucun | Tout |

**Composants.**

1. **Application terrain installable (PWA).** La coquille et les écrans de terrain sont mis en cache par un service worker ; l'application s'installe sur l'écran d'accueil Android sans magasin d'applications. Le back-office reste rendu par le serveur.
2. **Base locale chiffrée (IndexedDB).** Elle contient le jeu de travail de l'utilisateur, limité à son rôle et à son périmètre, et le journal des opérations en attente ; la clé est protégée par le code personnel de l'utilisateur (section 5.6).
3. **Journal d'opérations.** Chaque action de l'utilisateur devient une opération immuable : identifiant UUID généré sur l'appareil, type, objet, données, version de base, horodatage de l'appareil, appareil et utilisateur.
4. **Service de synchronisation.** Côté serveur, deux points d'API (envoi des opérations, réception des changements) et un journal des changements par centre, numéroté de façon croissante.

**Cycle de synchronisation.**

1. **Déclenchement automatique** au retour du réseau, à l'ouverture de l'application, puis toutes les 5 minutes tant que des opérations attendent (espacement progressif jusqu'à 30 minutes), et en arrière-plan quand le navigateur le permet ; un bouton « Synchroniser maintenant » reste disponible.
2. **Envoi** par lots ordonnés et compressés. Le serveur applique chaque opération par les mêmes services métier qu'une saisie en ligne (droits, périmètre, règles RG, journal d'audit), dans une transaction, et ignore une opération déjà reçue grâce à son identifiant. Chaque opération reçoit un résultat : appliquée, rejetée avec un motif lisible, ou en conflit.
3. **Réception** des changements survenus depuis le dernier curseur de l'appareil, filtrés par droits et périmètre ; un objet archivé ou un droit retiré efface la copie locale.
4. **Pièces jointes** envoyées après les données, compressées, avec reprise après coupure et option « Wi-Fi seulement ».
5. **État visible** en permanence : à jour, nombre d'opérations en attente, heure de la dernière synchronisation, opérations rejetées ou en conflit à traiter.

**Règles de résolution des conflits.**

| Type de donnée | Règle |
| --- | --- |
| Écritures en ajout seul (ventes, règlements, mouvements de stock, encaissements) | Aucun conflit possible : chaque opération crée un enregistrement ; une correction passe par une contre-écriture |
| Présences | Une présence par séance et par inscription ; si deux appareils la saisissent, la plus récente selon l'horodatage de l'appareil est retenue, l'autre reste à l'historique, et le formateur est averti si les valeurs diffèrent |
| Fiches modifiables (bénéficiaire, produit) | Fusion champ par champ depuis la version de base ; un même champ modifié des deux côtés crée un conflit : la valeur du serveur est conservée et le conflit attend une décision dans la file « À résoudre » du centre |
| Changements de statut et validations | Revérifiés au serveur ; une transition devenue impossible est rejetée avec son motif |
| Création de candidature | Recherche des doublons sur le jeu local, puis détection complète au serveur ; un score de 60 ou plus crée la candidature au statut « À vérifier, doublon probable » au lieu de la refuser, pour ne rien perdre de la saisie |
| Mois verrouillé | Une opération datée d'un mois verrouillé est refusée et placée en file « Écriture tardive » ; le comptable la transforme en régularisation datée du mois courant (RG-SRC-03) |
| Codes lisibles | Attribués par le serveur à la synchronisation ; l'appareil affiche un code provisoire jusque-là |

**Clôtures.** Le comptage de caisse d'une journée exige que tous les appareils du point de vente aient synchronisé leurs ventes du jour ; à défaut, l'écran liste les appareils en retard. La vérification de la clôture mensuelle exige une synchronisation de chaque appareil enrôlé du centre postérieure à la fin du mois ; le responsable de centre peut lever ce blocage par une décision motivée et tracée qui nomme l'appareil manquant.

**Numérotation des reçus.** Chaque appareil enrôlé sur un point de vente reçoit une série ; le numéro de reçu est la série suivie d'un numéro continu propre à l'appareil (ex. CMR-B-000127), attribué sur l'appareil, en ligne comme hors ligne. L'unicité porte sur (point de vente, série, numéro) et la continuité sans trou s'apprécie par série (BOU-06).

**Horloge et durée hors ligne.** Chaque opération garde l'horodatage de l'appareil et celui du serveur ; si l'horloge de l'appareil s'écarte de plus de 5 minutes de celle du serveur à la synchronisation, ses opérations sont signalées « horloge à vérifier » et l'application demande de corriger l'heure. L'identification locale reste valable 72 heures après la dernière connexion en ligne (paramétrable) ; au-delà, l'application se verrouille, conserve les saisies et les envoie à la prochaine connexion. Un appareil qui garde des opérations en attente depuis plus de 48 heures est signalé au responsable du centre.

### 4.6 Paiements Mobile Money : scolarité et services associés

Les bénéficiaires, ou un tiers payeur, règlent par Mobile Money la scolarité et les services associés (demande du porteur de projet du 13/10/2026, à formaliser par la Direction Générale). Cette demande lève, pour le seul Mobile Money, l'exclusion du paiement électronique intégré (PRD A6) et la position « aucune intégration » (H9). CAEF Connect orchestre et enregistre les paiements, mais ne détient jamais les fonds : ils arrivent directement sur le compte marchand des CAEF ouvert chez l'opérateur ou l'agrégateur. Seule la confirmation de l'opérateur fait d'un paiement un encaissement.

| Module | Responsabilité |
| --- | --- |
| facturation | Catalogue des services payants et tarifs par centre et par période : frais d'inscription, scolarité d'une session de formation, examen ou attestation, services associés (matériel, garde d'enfants quand le module crèches existera) ; échéances et échéanciers par bénéficiaire ; exonérations et prises en charge (bourse, réduction motivée, partenaire ou programme) |
| paiements | Encaissements de tous canaux (espèces, Mobile Money), passerelles, affectation aux échéances, reçus, rapprochement quotidien, remboursements ; utilisé aussi par la boutique pour ses règlements Mobile Money |

**Passerelle.** Le module paiements parle à une interface interne unique (initier un paiement, consulter son statut, recevoir une notification, rembourser, lire le relevé), avec un adaptateur par fournisseur : un agrégateur agréé couvrant plusieurs opérateurs (recommandé : un contrat, une intégration) ou l'API directe d'un opérateur. Les opérateurs retenus sont ceux qu'utilisent les payeuses, établis au diagnostic. Un adaptateur « déclaratif », sans opérateur, sert de repli tant que le contrat marchand n'est pas signé : le Mobile Money est alors déclaré avec sa référence, dans les mêmes tables.

| Parcours | Déroulement | Connexion du centre |
| --- | --- | --- |
| A. Demande de paiement | L'agent choisit l'échéance et saisit le numéro de la payeuse ; le serveur envoie la demande à la passerelle ; la payeuse valide sur son téléphone avec son code secret, jamais saisi dans CAEF Connect ; la notification de l'opérateur confirme le paiement et le reçu est émis | Requise |
| B. Paiement à l'initiative de la payeuse | La payeuse paie le compte marchand des CAEF en indiquant la référence de paiement imprimée sur son avis d'échéance ; la notification arrive au serveur, qui affecte le paiement à l'échéance ; sans référence valide, il entre dans la file « Paiements à affecter » du comptable | Non requise |
| C. Déclaration hors ligne | L'agent enregistre l'identifiant de transaction lu sur le SMS de confirmation de la payeuse et remet un reçu provisoire ; à la synchronisation, le serveur rapproche la déclaration des transactions de l'opérateur : « Confirmé » ou « Non retrouvé », signalé au comptable après 24 heures | Non requise |

Statuts d'un paiement : initié, en attente de la payeuse, confirmé, échoué, expiré, déclaré, non retrouvé, remboursé partiellement, remboursé. Seuls les paiements confirmés entrent dans les encaissements ; les paiements déclarés s'affichent à part, avec le badge « Déclaré » (TDB-03).

| Sujet | Règle d'architecture |
| --- | --- |
| Source de vérité | La confirmation de l'opérateur, par notification signée ou consultation de statut ; jamais l'appareil ni une saisie |
| Notifications entrantes | Point d'API dédié ; signature vérifiée (HMAC ou certificat) et adresses d'origine filtrées si l'opérateur les publie ; idempotence sur l'identifiant de transaction de l'opérateur ; réponse immédiate, traitement dans la file de tâches |
| Notification manquante | Consultation du statut à 1, 5, 15 et 60 minutes, puis passage à « expiré » |
| Montants | GNF entiers ; un montant confirmé différent du montant attendu crée un paiement partiel ou un trop-perçu, jamais un arrondi ; commission de l'opérateur enregistrée à part (brut, commission, net) quand la passerelle la communique |
| Rapprochement | Relevé de l'opérateur importé chaque nuit (API ou fichier) et rapproché transaction par transaction ; écarts signalés au comptable ; totaux repris par la clôture mensuelle (SRC-02) |
| Remboursement | Demandé et motivé par le comptable, validé par le responsable de centre (ou le RA en intérim), jamais par la même personne ; exécuté par la passerelle si elle le permet, sinon hors outil avec pièce justificative |
| Secrets et environnements | Clés de la passerelle dans le coffre de secrets, rotation annuelle ; environnement de test de l'opérateur en développement et en préproduction ; aucun appel réel hors production |
| Données personnelles | Numéro de la payeuse conservé avec la transaction (donnée nominative), jamais utilisé comme identifiant de personne (DAT-01) ; ni code secret ni solde du compte de la payeuse |
| Réglementation | Compte marchand au nom de l'entité CAEF ; vérification d'identité des payeuses à la charge de l'opérateur ; avis juridique sur la réglementation de la Banque centrale de la République de Guinée applicable aux paiements marchands, avant la mise en service |

**Mise en œuvre au lot 1 (14/10/2026).** L'interface interne est en place avec deux adaptateurs : `declaratif`, par défaut, et `simulateur`, une passerelle fictive signée par HMAC-SHA256 (en-tête `X-Signature`) pour les tests et la recette, interdite en production. L'adaptateur est choisi par la variable `CAEF_PASSERELLE_MOBILE_MONEY`. Les relevés de l'opérateur sont importés par fichier (CSV ou JSON) ; la tâche nocturne `importer_releves` attend le contrat de la passerelle (H16). Une transaction reçue sans référence d'échéance valide reste orpheline, puis est rattachée quand le paiement est déclaré avec son identifiant, sauf si `CAEF_CENTRE_PAIEMENTS_NON_REFERENCES` désigne un centre dont le comptable la reçoit. Le montant retenu est toujours celui de l'opérateur, et un identifiant de transaction ne sert qu'une fois.

**Mise en service.** Le module paiements, son modèle de données, l'adaptateur déclaratif et le parcours C sont construits dans le lot 1. La facturation de la scolarité et les parcours A et B sont mis en service dès que la politique tarifaire (PRD H15) et le choix de la passerelle (H16) sont arrêtés, au plus tôt pendant le pilote, sans migration de données.

### 4.7 Modules activables par centre

Le porteur de projet a demandé le 13/10/2026 que certains modules, comme la boutique ou la salle d'exposition, puissent être désactivés pour un centre (ADM-08). L'activation est une donnée, pas un paramètre de déploiement : une seule version de l'application sert tous les centres.

| Sujet | Règle d'architecture |
| --- | --- |
| Socle et modules optionnels | Socle toujours actif : identite, habilitations, referentiels, beneficiaires, formations, documents, pilotage, journal. Modules optionnels : boutique, salle d'exposition (dans la boutique), facturation et paiements, volet RSE du centre, puis les modules réservés, qui arrivent désactivés |
| Donnée | Table `module_centre` en ajout seul (Modèle de données, section 3) ; statut en vigueur mis en cache par centre, invalidé à chaque nouvelle ligne validée |
| Contrôle côté serveur | Le service habilitations vérifie le module avant le périmètre, pour les écrans, l'API, les exports, les tâches de fond et les opérations synchronisées (section 4.1) ; refus « Module non activé » journalisé |
| Client et appareils | La session et le flux de synchronisation transmettent la liste des modules actifs du centre ; l'interface masque les menus des modules inactifs ; à la synchronisation suivante, l'appareil efface les données locales d'un module désactivé et refuse d'en saisir de nouvelles |
| Données existantes | Conservées en lecture seule pour la DG, le RC, le RA, le CPT et le SE ; affectations au rôle VB suspendues ; aucune suppression |
| Indicateurs | Un indicateur d'un module inactif pour un centre vaut « Module non activé », jamais 0 ; les totaux nationaux indiquent le nombre de centres où le module est actif (Référentiel des indicateurs, règle commune) |
| Garde-fous | Désactivation refusée tant que le module a des opérations en cours (caisse ou inventaire non validé, reversement non payé, paiement en attente, article encore exposé) ; saisie par l'ADM, validation par la DG (RG-ADM-18, RG-ADM-19) |

## 5. Sécurité

Le référentiel de vérification retenu est l'OWASP ASVS niveau 2, adapté à une application qui traite des données personnelles ; la recette de sécurité vérifie ses exigences applicables avant la mise en service (DAT v1.0 § 12).

### 5.1 Identités et sessions

| Mesure | Détail | Exigence |
| --- | --- | --- |
| Mots de passe | 10 caractères minimum, refus des mots de passe connus compromis, hachage Argon2id ou bcrypt avec sel | SEC-08 |
| Anti-force brute | Blocage 15 minutes après 5 échecs, suspension après 10 dans l'heure, limitation du débit par adresse | SEC-08 |
| Double authentification | Code à usage unique par application d'authentification (TOTP) ; obligatoire pour ADM, DG et CPT, recommandée pour RC, RA, RSE, SE ; codes de secours | SEC-11 |
| Sessions | Cookie sécurisé, HttpOnly, SameSite ; expiration après 30 minutes d'inactivité (8 heures au plus) ; déconnexion de toutes les sessions à la désactivation | SEC-02, SEC-06 |
| Réinitialisation | Lien unique valable 30 minutes ; notification à l'utilisateur après changement | USR-05 |

### 5.2 Autorisations

- Modèle : contrôle d'accès par rôle et par périmètre (affectation), table `permission` alimentée depuis la Matrice des rôles et versionnée avec le code.
- Application : vérification dans chaque service métier, filtre de périmètre par défaut dans l'accès aux données, sécurité au niveau des lignes en base pour les tables nominatives (section 4.1).
- Rôles de centre : RA (adjoint du responsable), CPT (chef comptable), VB (gérante de la salle d'exposition et de la boutique) et CMT (chef matériels, en consultation) entrent dans la table des rôles avec leurs permissions issues de la Matrice ; les écrans affichent les titres de l'organigramme des centres (Matrice § 2.1) ; VB n'accède à aucune fiche bénéficiaire, CPT seulement à l'identité minimale des productrices déposantes, CMT à aucune donnée nominative.
- Intérim : les droits de validation du RC ne s'appliquent au RA que pendant un intérim déclaré (USR-09) ; le service habilitations vérifie au moment de chaque autorisation qu'un intérim est en cours, sans copie de droits qui survivrait à sa date de fin.
- Séparation des tâches : contrôlée dans les services métier ; nul ne valide une opération qu'il a saisie, la clôture de caisse d'une journée où il a vendu l'ajustement d'un inventaire qu'il a compté, ou la clôture mensuelle qu'il a vérifiée.
- Identifiants : les adresses d'écran utilisent des UUID, jamais des numéros séquentiels devinables.
- Tests automatisés : un test par cellule de la Matrice, exécuté à chaque livraison (Plan de tests, C3).

### 5.3 Protection des données

| Couche | Mesure |
| --- | --- |
| Transit | TLS 1.2 au minimum, TLS 1.3 de préférence ; HSTS ; aucun service en clair |
| Base | Chiffrement du volume ; champs restreints (pièce d'identité, secrets) chiffrés au niveau applicatif avec une clé distincte |
| Documents | Stockage chiffré ; téléchargement par lien signé valable 5 minutes, après contrôle des droits ; aucun lien public permanent |
| Sauvegardes | Chiffrées avant envoi, clés conservées hors du site de sauvegarde |
| Secrets | Coffre de secrets ou variables chiffrées de la plateforme ; jamais dans le dépôt de code ; rotation annuelle et après tout départ |
| Fichiers déposés | Formats et tailles limités, analyse antivirus, renommage, aucun exécutable |
| Navigateur | En-têtes CSP, X-Content-Type-Options, Referrer-Policy ; protection CSRF du framework |

### 5.4 Journalisation et détection

- Journal métier (`journal_audit`) en ajout seul, décrit au Dictionnaire ; copie quotidienne vers un stockage séparé pour empêcher toute altération (SEC-04).
- Journaux techniques (accès, erreurs) centralisés, conservés 12 mois, sans données personnelles dans les messages d'erreur.
- Alertes automatiques : pic d'échecs de connexion, export nominatif volumineux, accès refusés répétés, connexion d'un compte privilégié hors horaires habituels.

### 5.5 Gestion des incidents

Tout incident significatif est enregistré selon les rubriques du DM § 12.4 (date de détection, nature, systèmes et données touchés, confinement, correction, responsable, notifications). La procédure désigne un responsable d'astreinte côté prestataire et un responsable côté CAEF (référent données et protection), et prévoit la désactivation immédiate des comptes compromis. Les obligations de notification sont à confirmer avec l'avis juridique (DAT v1.0 § 6.3).

### 5.6 Appareils, données locales et paiements

Le travail hors ligne place des données personnelles sur les téléphones et tablettes du centre, et les paiements exposent de l'argent réel ; les mesures ci-dessous s'ajoutent à celles des sections 5.1 à 5.4.

| Mesure | Détail | Exigence |
| --- | --- | --- |
| Enrôlement des appareils | Un appareil n'accède au mode hors ligne qu'après enrôlement par le responsable de centre ou l'administrateur ; il porte un identifiant, un centre, une série de reçus et un statut ; révocable à tout moment | OFF-06 |
| Rôles hors ligne | Réservé aux rôles de terrain du centre (RC, RA, AA, RP, FO, VB, CPT) ; ADM, DG, RSE, SE et CMT travaillent en ligne seulement | OFF-06 |
| Identification locale | Code personnel de 6 chiffres au moins, défini après une connexion en ligne complète (double authentification comprise pour les rôles qui l'exigent) ; verrouillage après 15 minutes d'inactivité ; valable 72 heures sans reconnexion en ligne | OFF-06, SEC-02 |
| Données locales | Base locale chiffrée (AES-GCM par l'API de chiffrement du navigateur), clé protégée par le code personnel ; jeu limité au rôle et au périmètre ; aucune pièce d'identité ni champ restreint (R) sur l'appareil | OFF-06, SEC-03 |
| Effacement | Après 5 codes erronés, effacement des données consultables ; les opérations non envoyées restent chiffrées et partent à la prochaine connexion en ligne ; un appareil révoqué efface tout au premier contact | OFF-06, SEC-06 |
| Opérations reçues | Chaque opération est rattachée à l'utilisateur et à l'appareil, revérifiée au serveur (droits, périmètre, règles) et journalisée ; une opération hors périmètre est refusée et signalée | OFF-04, SEC-01, SEC-04 |
| Paiements | Notifications de la passerelle authentifiées et rejouées sans effet ; montant jamais pris du client ; remboursement soumis à séparation des tâches ; alertes sur paiements non retrouvés et écarts de rapprochement | SEC-14, PAY-08, PAY-10 |

## 6. Données, reporting et continuité

Les données métier vivent dans une seule base PostgreSQL, les fichiers dans un stockage d'objets, et les indicateurs dans des tables de synthèse recalculées la nuit ; les objectifs RPO et RTO sont proposés ici mais restent à décider (DISP-01).

### 6.1 Organisation des données

- **Schéma opérationnel :** les entités du Modèle et dictionnaire, dont celles du module boutique, de l'intérim, de la clôture mensuelle, de la synchronisation (appareils, opérations reçues, journal des changements, conflits), de la scolarité et des paiements ajoutées à la demande du porteur de projet, migrations versionnées avec le code ; aucune modification manuelle du schéma en production.
- **Schéma de pilotage :** tables de synthèse par indicateur, période et centre, calculées par une tâche nocturne et figées à la clôture d'une période (RG-TDB-01, RG-TDB-04). Elles isolent le reporting de la saisie (PERF-02).
- **Entrepôt analytique :** non nécessaire au MVP ; à réévaluer quand le nombre de centres ou de rapports le justifiera (DAT v1.0 § 3).
- **Index :** sur les champs de recherche (noms normalisés, codes, statuts, centre, dates) et sur toutes les clés étrangères (PERF-01).
- **Documents :** un compartiment par environnement, arborescence par type d'objet et identifiant, versions conservées, métadonnées dans la table `document`.

### 6.2 Sauvegardes

| Élément | Fréquence | Conservation | Emplacement |
| --- | --- | --- | --- |
| Base, sauvegarde complète | Quotidienne | 30 jours, puis une par mois pendant 12 mois | Site ou région distincts, chiffrée |
| Base, journal des transactions | Continu | 7 jours | Idem, permet la restauration à un instant donné |
| Documents | Versions et réplication quotidienne | 30 jours pour les versions supprimées | Idem |
| Configuration et secrets | À chaque changement | 12 mois | Coffre distinct |
| Copie hors ligne | Mensuelle | 12 mois | Support non connecté en permanence, contre les rançongiciels |

La protection contre la suppression accidentelle repose sur le verrouillage des sauvegardes en écriture seule pendant leur durée de conservation (DAT v1.0 § 7). Une restauration complète est testée avant le pilote puis chaque trimestre, avec procès-verbal (SEC-05).

### 6.3 RPO et RTO : options à décider

| Option | RPO, perte maximale | RTO, délai de rétablissement | Moyens nécessaires | Adaptée à |
| --- | --- | --- | --- | --- |
| 1. Minimale | 24 heures | 2 jours ouvrés | Sauvegarde quotidienne seule, restauration manuelle | Pilote seulement |
| 2. Recommandée | 15 minutes | 8 heures ouvrées | Journal des transactions continu, procédure de restauration documentée et répétée, astreinte en heures ouvrées | Pilote et premières vagues |
| 3. Renforcée | Quasi nulle | 1 heure | Base répliquée en attente active sur un second site, bascule testée, astreinte étendue | Réseau national, si la criticité le justifie |

Une interruption d'une journée retarde la saisie sans perte de service essentiel pour les bénéficiaires ; la perte de données saisies est plus coûteuse que l'interruption. C'est pourquoi l'option 2 privilégie un RPO court à un RTO très court. La décision revient au comité de pilotage, après chiffrage par le prestataire (DAT v1.0 § 7).

**Données des appareils.** Une opération saisie hors ligne n'est protégée par le RPO qu'après sa synchronisation. Pour couvrir aussi une restauration du serveur, chaque appareil garde ses opérations acquittées pendant 7 jours ; après une restauration à un instant donné, le serveur demande aux appareils de renvoyer les opérations postérieures à cet instant et les réapplique sans doublon grâce à leur identifiant (section 4.5).

## 7. Environnements, livraison et supervision

Trois environnements isolés, une chaîne de livraison automatisée et une supervision minimale sont requis avant le pilote (ARC-03, MNT-01, MNT-02, OPS-01).

| Environnement | Usage | Données | Accès |
| --- | --- | --- | --- |
| Développement | Réalisation, tests automatisés | Fictives générées | Équipe technique |
| Préproduction | Recette, formation, tests d'import sur échantillon, démonstrations | Fictives ou anonymisées (SEC-07) | Équipe projet, référents des centres |
| Production | Service réel | Réelles | Utilisateurs habilités ; équipe technique par accès d'urgence tracé |

### 7.1 Chaîne de livraison

1. Code dans un dépôt Git dont les CAEF sont propriétaires ou co-titulaires ; branche principale protégée, revue de code obligatoire.
2. À chaque modification : tests unitaires et d'intégration, tests de permissions, analyse statique, analyse des dépendances vulnérables, construction de l'image.
3. Déploiement automatique en préproduction ; déploiement en production sur décision, après recette, avec numéro de version.
4. Avant chaque mise en production : sauvegarde vérifiée, migrations testées en préproduction, plan de retour arrière (image précédente et procédure de réversion des migrations), responsables identifiés (DAT v1.0 § 10).
5. Fenêtre de maintenance proposée : en soirée ou le week-end, annoncée 48 heures à l'avance dans l'application.

### 7.2 Supervision

| Objet | Seuil d'alerte proposé | Destinataire |
| --- | --- | --- |
| Disponibilité de la page de connexion | 2 échecs consécutifs à 1 minute d'intervalle | Astreinte prestataire |
| Erreurs applicatives | Nouvelle erreur, ou plus de 1 % des requêtes en erreur sur 15 minutes | Équipe technique |
| Temps de réponse | 95 % des requêtes au-dessus de 2 secondes pendant 15 minutes | Équipe technique |
| Espace disque, mémoire, processeur | 80 % | Astreinte prestataire |
| Sauvegardes | Une sauvegarde manquante ou en échec | Astreinte et référent technique CAEF |
| Certificats TLS | Expiration dans moins de 14 jours | Équipe technique |
| Tâche nocturne des indicateurs | Échec ou durée anormale | Équipe technique, Suivi-évaluation informé |
| Synchronisation | Appareil avec des opérations en attente depuis plus de 48 heures ; plus de 2 % d'opérations rejetées ou en conflit sur une journée | Responsable du centre (tableau de bord) et équipe technique |
| Passerelle de paiement | Notifications en échec, paiement « en attente » depuis plus d'une heure, passerelle indisponible | Équipe technique et comptable du centre |
| Rapprochement Mobile Money | Écart entre les transactions de l'opérateur et les paiements confirmés, ou relevé non reçu | Comptable du centre, responsable du centre informé |

Un tableau de bord technique mensuel (disponibilité mesurée, incidents, temps de réponse, volumétrie) est remis au comité de pilotage.

### 7.3 Mise en œuvre au lot 1 (14/10/2026)

**Environnement local.** `backend/docker-compose.yml` lance sept services : `web` (Gunicorn), `worker` et `beat` (Celery), `postgres` (16), `redis` (7), `minio` (stockage S3) et `nginx`, exposé sur le port 8080. La configuration vient d'un fichier `.env` copié de `backend/.env.example`, sans aucune valeur réelle dans le dépôt ; le démarrage refuse de se lancer sans `DJANGO_SECRET_KEY`, `CAEF_CLE_CHIFFREMENT_CHAMPS`, ni mots de passe de la base et du stockage. La variable `CAEF_ENVIRONNEMENT` vaut `developpement`, `recette`, `preproduction` ou `production` ; le jeu de données fictives et le simulateur de paiement sont refusés en production.

```bash
cp .env.example .env            # puis remplir les secrets
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py generer_donnees_fictives
```

**Intégration continue.** Le flux GitHub Actions `.github/workflows/backend.yml` s'exécute à chaque poussée sur la branche principale et à chaque demande de fusion qui touche `backend/`, la Matrice (`docs/04*`) ou le flux lui-même. Sur Python 3.13 et un service PostgreSQL 16, il enchaîne : analyse statique (`ruff check`), `manage.py check`, contrôle qu'aucune migration ne manque, puis la suite `pytest`. Les secrets de la CI sont des valeurs jetables, sans donnée réelle.

**Reste à faire avant le pilote.** Les étapes 2 et 3 de la section 7.1 qui manquent encore : analyse des dépendances vulnérables, construction et publication de l'image, déploiement automatique en préproduction. S'y ajoutent l'environnement de préproduction lui-même, la terminaison TLS, la sauvegarde continue (section 6.2) et la supervision (section 7.2).

## 8. Performance, capacité et connectivité

Le dimensionnement repose sur des hypothèses écrites, à remplacer par les chiffres du diagnostic ; elles sont volontairement hautes pour le pilote, qui ne compte qu'un centre, le CAEF Cameroun à Dixinn : les valeurs prévues pour deux centres sont conservées par prudence, afin que la recette de charge ait de la marge (DAT v1.0 § 8).

### 8.1 Hypothèses de volumétrie à valider

| Grandeur | Pilote (1 centre, CAEF Cameroun ; hypothèses prudentes conservées) | Réseau à 3 ans (hypothèse 30 centres) |
| --- | --- | --- |
| Utilisateurs nommés | 40 | 500 |
| Utilisateurs simultanés en pointe | 20 | 150 |
| Bénéficiaires enregistrés par an | 2 000 | 40 000 |
| Sessions par an | 80 | 1 500 |
| Présences saisies par an | 60 000 | 1 200 000 |
| Documents déposés par an | 5 000, 1 Go | 100 000, 25 Go |
| Partenaires et opportunités | 150 | 1 500 |
| Appareils enrôlés | 10 | 300 |
| Paiements par an (scolarité, services, boutique) | 6 000 | 150 000 |
| Opérations synchronisées par jour en pointe | 3 000 | 60 000 |

Avec ces volumes, une seule base PostgreSQL et un serveur d'application de taille moyenne suffisent ; l'architecture monte en charge en ajoutant des instances d'application derrière le proxy, sans changer de conception (ARC-01).

### 8.2 Objectifs de performance proposés

| Opération | Objectif, 95 % des cas, sur une connexion mobile 3G de référence | Exigence |
| --- | --- | --- |
| Affichage d'une liste ou d'une fiche | 3 secondes | PERF-01 |
| Enregistrement d'un formulaire | 2 secondes | PERF-01 |
| Recherche de doublons à la création | 2 secondes | BEN-05 |
| Ouverture d'un tableau de bord | 4 secondes, grâce aux tables de synthèse | PERF-02 |
| Génération d'un rapport national | En tâche de fond, moins de 5 minutes, notification à la fin | REP-03 |
| Poids d'un écran de saisie | Moins de 500 Ko au premier chargement, moins de 100 Ko ensuite ; application terrain : moins de 1 Mo compressé à l'installation, puis seulement les données | NET-01 |
| Enregistrement d'une vente de 10 lignes et affichage du reçu | 2 secondes, numérotation correcte sous saisies concurrentes | BOU-03, BOU-06 |
| Ouverture d'un écran de terrain sans réseau | 2 secondes | OFF-01 |
| Synchronisation de 500 opérations après 3 jours hors ligne | Moins de 2 minutes sur 3G, sans perte ni doublon | OFF-02, OFF-03 |
| Confirmation d'une demande de paiement Mobile Money | Statut affiché dans les 5 secondes qui suivent la notification de l'opérateur | PAY-05 |

Les tests de charge simulent la pointe du réseau à 3 ans (150 utilisateurs simultanés) sur la préproduction dimensionnée comme la production, et les objectifs sont vérifiés aussi depuis un téléphone d'entrée de gamme sur le réseau mobile réel du centre pilote (PERF-03).

### 8.3 Connectivité

1. Ressources statiques compressées, mises en cache longue durée et versionnées ; images optimisées ; aucune police ou bibliothèque chargée depuis un serveur tiers.
2. Back-office : pagination côté serveur, jamais de liste complète téléchargée.
3. Application terrain installable : coquille et écrans mis en cache à l'installation et mis à jour en arrière-plan ; ensuite, seules les données circulent.
4. Jeu de travail local limité au rôle et au périmètre de l'utilisateur (dossiers actifs du centre, ses sessions, catalogue et prix de la boutique, échéances en cours), de l'ordre de 20 Mo au plus par appareil, chiffré.
5. Synchronisation automatique au retour du réseau, par lots compressés, avec reprise après coupure et clé d'idempotence (NET-02, section 4.5) ; pièces jointes envoyées après les données, avec option « Wi-Fi seulement ».
6. Indicateur d'état (à jour, opérations en attente, dernière synchronisation) et liste des opérations rejetées ou en conflit.
7. Boutique : ventes hors ligne dans l'application ; reçu papier de secours seulement si l'appareil est hors service (section 4.4).

## 9. Exploitation, support, réversibilité et coûts récurrents

L'exploitation doit être définie et financée avant la mise en production ; le contrat du prestataire doit garantir que les CAEF peuvent reprendre leurs données, leur code et leur exploitation à tout moment (Plan § 12, DAT v1.0 § 13).

### 9.1 Support proposé

| Niveau | Qui | Rôle |
| --- | --- | --- |
| Niveau 1 | Référent de chaque centre | Aide aux utilisateurs, première qualification, fiches réflexes |
| Niveau 2 | Administrateur national CAEF | Comptes, droits, paramétrage, diagnostic fonctionnel, ouverture des tickets |
| Niveau 3 | Prestataire technique | Anomalies, incidents, sécurité, mises à jour |

| Priorité | Exemple | Prise en charge proposée | Résolution ou contournement proposé |
| --- | --- | --- | --- |
| P1 bloquant | Service indisponible, fuite de données suspectée | 2 heures ouvrées | 1 jour ouvré |
| P2 majeur | Une fonction prioritaire inutilisable dans un centre | 1 jour ouvré | 3 jours ouvrés |
| P3 mineur | Gêne avec contournement | 3 jours ouvrés | Prochaine version |

Ces délais sont des propositions à contractualiser selon les moyens disponibles (Plan § 12).

### 9.2 Réversibilité

- Export complet de la base dans un format documenté (dump PostgreSQL et fichiers CSV par table avec le dictionnaire) et des documents avec leurs métadonnées, livré sur demande sous 10 jours ouvrés et testé une fois par an (MNT-03).
- Code source, scripts de déploiement, configuration des environnements et documentation remis à chaque version majeure ; inventaire des composants et licences tenu à jour.
- Transfert de compétences à une équipe désignée par les CAEF, avec rapport (DAT v1.0 § 13, livrable 12).
- Aucune dépendance propriétaire sans alternative documentée ; les services managés utilisés doivent avoir un équivalent open source.

### 9.3 Postes de coûts récurrents à chiffrer

Les montants relèvent des offres et du modèle économique ; ce DAT liste seulement les postes, pour que le coût total sur cinq ans soit comparable entre offres (DM § 20, risque 8). Les estimations et le rôle envisagé de TIKA sont traités dans le document « Budget et modèle économique CAEF Connect ».

| Poste | Facteur de coût |
| --- | --- |
| Hébergement (calcul, base, stockage) | Option d'hébergement, volumes, nombre d'environnements ; hébergement initial du pilote pouvant être financé par TIKA (option à confirmer, PRD H8) |
| Sauvegardes et second site | Option RPO et RTO retenue |
| Noms de domaine et certificats | Faible |
| Supervision et suivi des erreurs | Outils auto-hébergés ou services payants |
| Maintenance corrective et évolutive | Volume de jours par an |
| Support et astreinte | Niveaux de service retenus |
| Sécurité (audit annuel, tests d'intrusion) | Fréquence |
| Courriel et SMS (lot 3 ; SMS de reçu de paiement si retenu) | Volume de messages |
| Formation des nouveaux utilisateurs | Rythme des vagues de déploiement |
| Connectivité et équipements des centres | Hors plateforme, à évaluer par centre ; condition d'entrée du pilote : le CAEF Cameroun part du papier (livrets, feuilles volantes) et doit être équipé avant l'ouverture (ordinateurs, tablettes ou téléphones, imprimante, imprimante de reçus, connectivité, onduleur) |
| Passerelle Mobile Money | Mise en service et abonnement de l'agrégateur ; commission par transaction, supportée selon la politique tarifaire (PRD H15) |
| Gestion des appareils de terrain | Enrôlement, révocation et renouvellement des téléphones et tablettes ; outil de gestion de flotte optionnel |

## 10. Décisions techniques à valider

Quinze décisions du DAT v1.0 § 14 restent à prendre ; pour chacune, ce document propose une position, qui ne vaut décision qu'après validation par le comité de pilotage. La place du module boutique (PRD H14) est déjà tranchée par le porteur de projet, à formaliser par la Direction Générale (dernière ligne). Le 13/10/2026, le porteur de projet a demandé le fonctionnement hors ligne d'abord et les paiements Mobile Money : ces demandes changent les positions sur le type d'application et le hors connexion, et ajoutent deux décisions (passerelle de paiement, politique tarifaire), à formaliser elles aussi.

| Décision | Position proposée | Référence | Instance |
| --- | --- | --- | --- |
| Hébergement et localisation | Option issue de l'avis juridique ; services managés à conformité égale ; sauvegardes sur un second site | 3.2 ; PRD H7 | Direction Générale |
| Style d'architecture | Monolithe modulaire | 4 ; PRD H13 | Comité de pilotage |
| Technologies et langages | Django ou Laravel selon le prestataire, rendu serveur pour le back-office ; application terrain en PWA avec un framework JavaScript léger. Le backend du lot 1 est écrit en Django (section 3.3) | 3.1, 3.3 | Comité, sur offres |
| Base de données | PostgreSQL | 3.1 | Comité |
| Stockage documentaire | Stockage d'objets compatible S3, chiffré | 3.1, 6.1 | Comité |
| Gestion des identités | Intégrée au framework, double authentification TOTP ; annuaire externe seulement si les CAEF en ont un | 5.1 | Comité |
| Web responsive, PWA ou natif | Web responsive pour le back-office ; application web progressive installable, hors ligne d'abord, pour les écrans de terrain | 3.1, 8.3 ; PRD H12 | Comité |
| Fonctionnement hors connexion | Demandé par le porteur de projet le 13/10/2026 : hors ligne d'abord pour les opérations de terrain, synchronisation automatique au retour du réseau, dès le lot 1 ; durée maximale hors ligne et contenu du jeu local à valider | 4.5, 8.3 ; PRD H11 | Porteur de projet ; formalisation attendue de la Direction Générale |
| RPO et RTO | Option 2 : 15 minutes et 8 heures ouvrées | 6.3 | Comité, après chiffrage |
| Disponibilité et performance | 99 % mesuré sur le mois en heures ouvrées pour le pilote ; objectifs de la section 8.2 | 8.2 | Comité |
| Canaux de notification | Application seule au MVP ; courriel puis SMS après chiffrage | 4.3 ; PRD écart A5 | Direction Générale |
| Migration des registres existants | Saisie ou numérisation des registres papier du centre pilote, rapprochement des chiffres de la comptable et de la responsable, divergences chargées avec le statut « à vérifier » (SRC-03), échantillon en préproduction, validation métier, chargement final tracé | SFD 4.6 ; Plan § 7 | Responsable métier |
| Supervision et journalisation | Sonde externe, suivi des erreurs auto-hébergé, journaux centralisés 12 mois | 5.4, 7.2 | Comité |
| Remise du code source | Dépôt détenu ou co-détenu par les CAEF dès le début, remise complète à chaque version majeure | 9.2 | Direction Générale, au contrat |
| Budget d'exploitation et maintenance | Postes de la section 9.3 chiffrés sur cinq ans dans chaque offre ; pilote financé par une offre de TIKA, à confirmer, et financeur des coûts récurrents identifié avant la fin du pilote | 9.3 ; PRD H8 | Direction Générale |
| Place du module boutique | Tranché par le porteur de projet le 12/10/2026 : module boutique dans le lot 1 du pilote, après le socle, en parallèle de la RSE ; BOU-01 à BOU-06 en P0, BOU-07 à BOU-11 attendus au pilote ; module isolé, sans effet sur les autres modules | 4.4 ; PRD H14 | Porteur de projet ; formalisation attendue de la Direction Générale des CAEF |
| Passerelle Mobile Money et compte marchand | Agrégateur agréé couvrant les opérateurs des payeuses, compte marchand au nom des CAEF, adaptateur déclaratif en attendant le contrat ; avis juridique sur la réglementation de la BCRG | 4.6 ; PRD H16 | Direction Générale, après comparaison des offres |
| Politique tarifaire de la scolarité et des services | Services payants, tarifs par centre, exonérations et prise en charge de la commission de l'opérateur, arrêtés avant la mise en service des parcours A et B | 4.6 ; PRD H15 | Direction Générale |
