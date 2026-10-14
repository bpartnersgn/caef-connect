# Brief de démarrage développeur CAEF Connect

Oct 12, 2026 · @Bangoura · à lire en premier, avant tout le reste · mis à jour le 14/10/2026 avec l'état du backend du lot 1

## 1. Ce que tu construis et où trouver chaque document

CAEF Connect est la plateforme de gestion des Centres d'Autonomisation et d'Entrepreneuriat de la Femme : dossiers des bénéficiaires, formations et présences, partenariats RSE et contributions, boutique où presque chaque centre vend sa production, tableaux de bord pour les centres et la Direction Générale. Le pilote se fera dans **un seul centre : le CAEF Cameroun**, quartier Cameroun de la commune de Dixinn, à Conakry (Guinée), avec des connexions parfois faibles ou absentes et beaucoup de saisie sur téléphone. Tout y est aujourd'hui sur papier (livrets, feuilles volantes), et les chiffres de la comptable diffèrent de ceux de la responsable du centre : c'est la raison des exigences SRC (une seule source pour chaque montant). TIKA est envisagée comme partenaire qui offrirait aux CAEF la réalisation et le démarrage du pilote (à confirmer).

Ta mission de départ est de construire le **lot 1** jusqu'à une version testable pour le pilote : d'abord le noyau, puis la RSE et la boutique, toutes deux dans le pilote et construites après le socle, avec la clôture mensuelle SRC. La crèche viendra plus tard. Deux exigences d'architecture s'ajoutent dès le lot 1, demandées le 13/10/2026 : le **hors ligne d'abord** (les écrans de terrain marchent sans Internet et se synchronisent seuls au retour du réseau) et le **paiement par Mobile Money** de la scolarité et des services associés. Respecte les règles de la section 2 ; tout le reste attend. Ces choix sont tranchés par le porteur de projet les 12 et 13/10/2026, à formaliser par la Direction Générale des CAEF.

| Document | Quand l'ouvrir | Lien |
| --- | --- | --- |
| Index des livrables | Vue d'ensemble et état de chaque document | [Index](https://claude.ai/code/artifact/8972db71-ff51-4f8f-b3f9-db4dd5ed26d2) |
| PRD | Pourquoi et quoi : exigences avec identifiant, priorité et lot | [PRD](https://claude.ai/code/artifact/035a2318-82b8-4a50-8f38-7dc9d9afd6ac) |
| SFD du MVP | Ta référence au quotidien : écrans E-xxx, règles RG-xxx, statuts, scénarios et critères d'acceptation | [SFD](https://claude.ai/code/artifact/cdf7bc38-c41b-4c5d-86b4-199c6cc0b1a8) |
| Modèle et dictionnaire des données | Avant d'écrire une table ou un champ | [Modèle](https://claude.ai/code/artifact/79209dfa-9f14-4b89-9f46-313fea0b2044) |
| Matrice des rôles et permissions | Avant d'écrire un contrôle d'accès | [Matrice](https://claude.ai/code/artifact/8003870c-82da-4846-8792-ff5691f82549) |
| DAT détaillé | Architecture, sécurité, sauvegarde, déploiement | [DAT](https://claude.ai/code/artifact/3498888f-f2dd-4793-8acc-f9ab385e2f15) |
| Référentiel des indicateurs | Avant de calculer un chiffre de tableau de bord | [Référentiel](https://claude.ai/code/artifact/fbf60b80-9db4-465d-a3da-0c4deb4a4048) |
| Plan de tests et de recette | Pour savoir comment ton travail sera vérifié | [Plan de tests](https://claude.ai/code/artifact/7dd1d811-41ff-46ce-bb8d-51a2cac267c0) |
| Dépôt de code | Le code, ses consignes pour les assistants IA et les choix faits là où les documents se taisent | Dépôt `bpartnersgn/caef-connect` : `AGENTS.md` à la racine, `backend/README.md` et `backend/DECISIONS.md` |

**État au 14/10/2026.** Le backend du lot 1 existe : un monolithe modulaire Django avec ses services métier, son API REST `/api/v1`, le moteur de droits tiré de la Matrice, la synchronisation hors ligne, les paiements Mobile Money en mode déclaratif ou simulé, un générateur de données fictives, les tests de la Matrice, Docker Compose et l'intégration continue (branche `backend-lot1`, demande de fusion n° 1, en relecture). Les écrans (pages HTMX et application terrain PWA) restent à construire. La section 4 donne le détail de l'avancement, et la section 5 le nom du paramètre de chaque position d'attente.

Les identifiants (BEN-03, RG-FOR-06, E-TDB-01, IND-07…) sont les mêmes dans tous les documents. Reprends-les dans tes noms de branches, tes messages de commit et tes tests : c'est ce qui permettra de prouver qu'une exigence est couverte.

## 2. Les règles non négociables

Ces règles protègent des femmes dont les données personnelles sont confiées au réseau, et l'argent des partenaires. Une fonctionnalité qui en viole une n'est pas livrée, même si elle marche en démonstration.

1. **Cloisonnement côté serveur.** Chaque requête vérifie le rôle et le périmètre (centre, programme) avant de lire ou d'écrire quoi que ce soit (SEC-01). Masquer un bouton ne suffit pas : un utilisateur qui change l'identifiant dans l'adresse doit recevoir un refus, et la tentative est journalisée. Filtre par centre dans la couche d'accès aux données, une fois pour toutes, plutôt que dans chaque vue.
2. **Les droits viennent de la Matrice, pas de l'intuition.** Encode la Matrice dans un fichier de données (rôle, objet, action, périmètre) et fais-en dériver les contrôles et les tests. En cas de doute, refuse.
3. **Tout ce qui est sensible est tracé.** Consultation d'un dossier nominatif, export, modification de droit, fusion de doublons, validation d'une contribution : une entrée au journal d'audit avec auteur, date, objet, écrite dans la même transaction que l'action (SEC-04). Le journal n'est jamais modifiable par l'application.
4. **Promis, signé, reçu et exécuté sont quatre choses différentes.** Une proposition n'est pas une convention, une convention n'est pas un encaissement, un encaissement n'est pas une preuve d'exécution (DM § 9.3). Quatre statuts, quatre totaux, jamais additionnés. Les contributions financières et en nature ont des totaux séparés.
5. **Déclaratif et vérifié restent séparés.** Chaque chiffre affiche son niveau de validation et sa date de calcul (TDB-03). Une contribution passe « reçue » seulement avec un justificatif, et la personne qui la saisit ne peut pas la valider (RG-CTR-04).
6. **Une donnée manquante n'est pas un zéro.** Un champ vide reste vide ; un centre qui n'a rien saisi s'affiche « non renseigné » (TDB-09). Ne remplis jamais une valeur par supposition, ni à la saisie, ni à l'import (MIG-01).
7. **Pas de données réelles hors production.** Développement et recette utilisent uniquement des données fictives (DM § 11.5). Aucun fichier réel de bénéficiaires sur ton poste, dans un dépôt ou dans une conversation avec un assistant IA.
8. **Comptes nominatifs, rien de partagé.** Un compte par personne (USR-01), double authentification pour les rôles privilégiés, aucun document confidentiel accessible par un lien public : téléchargement par lien signé de courte durée après contrôle des droits.
9. **Aucune donnée sensible collectée par défaut.** Pas de champ santé, religion, ethnie ou situation familiale détaillée sans décision explicite (BEN-01). Les rapports pour les partenaires ne contiennent aucun nom de bénéficiaire (REP-06).
10. **Pas de secret dans le code.** Clés, mots de passe et chaînes de connexion dans des variables d'environnement, jamais dans le dépôt.
11. **Une seule source pour chaque montant.** Vente, encaissement de caisse, reversement, contribution financière reçue : saisi une seule fois dans CAEF Connect ; la vue du CPT, le tableau de bord du RC et les rapports lisent les mêmes enregistrements, sans ressaisie ni tableur parallèle (SRC-01, RG-SRC-01). Clôture mensuelle : le CPT vérifie l'état de rapprochement, le RC (ou le RA en intérim) valide, chaque écart avec les pièces est motivé ; le mois validé est verrouillé, et toute correction passe par une écriture de régularisation datée du mois courant, référencée au mois corrigé (SRC-02, RG-SRC-02, RG-SRC-03).
12. **L'appareil propose, le serveur décide.** Hors ligne, chaque action devient une opération immuable avec un identifiant UUID généré sur l'appareil ; le serveur la rejoue par les mêmes services métier qu'une saisie en ligne (droits, périmètre, règles, journal d'audit) et ignore un envoi en double (OFF-03, OFF-04). Pas de logique métier propre au client : il affiche, met en file et explique les rejets. Aucun champ restreint ni pièce d'identité sur l'appareil, base locale chiffrée (OFF-06).
13. **Seul l'opérateur confirme un paiement.** Un paiement Mobile Money devient un encaissement uniquement sur confirmation de l'opérateur (notification signée ou consultation de statut), jamais sur la parole de l'appareil ni d'une saisie ; notifications vérifiées et idempotentes sur l'identifiant de transaction ; montant jamais pris du client ; aucun code secret de payeuse dans CAEF Connect ; CAEF Connect ne détient jamais les fonds (PAY-08, SEC-14).

## 3. Pile technique et architecture de départ

Le DAT détaillé propose une architecture volontairement simple, pour une petite équipe et des connexions faibles. Ces choix sont à valider (DAT § 10), mais tu peux démarrer dessus. Pour le backend du lot 1, le choix de **Django** est fait et noté dans le dépôt ; la colonne « Choix de départ » indique ce qui est en place.

| Brique | Choix de départ | Pourquoi |
| --- | --- | --- |
| Application | Un seul monolithe modulaire : **retenu, Django 5.2 et Django REST framework sous Python 3.13**, servi par Gunicorn | Un seul déploiement ; modules aux frontières nettes |
| Back-office | Pages rendues côté serveur, avec HTMX et Alpine.js pour l'interactivité ; pas d'application monopage | Pages légères, utilisables sur téléphone et réseau lent |
| Base | PostgreSQL 16 : un schéma opérationnel et un schéma `pilotage` pour les agrégats (table `pilotage.valeur_indicateur`) | Les tableaux de bord ne ralentissent pas la saisie |
| Fichiers | Stockage d'objets compatible S3, chiffré ; la base ne garde que les métadonnées ; MinIO en local | Pas de fichier sur le disque du serveur |
| Tâches de fond | Redis 7 et Celery (worker et beat) : calcul nocturne des indicateurs, doublons, clôtures du mois, rapprochement opérateur, alertes | Aucune page ne bloque sur un calcul |
| Exposition | Nginx en proxy HTTPS | TLS, en-têtes de sécurité, limitation de débit |
| Déploiement | Docker Compose, même configuration en préproduction et en production | Reproductible |
| Authentification | Comptes nominatifs, double authentification TOTP pour les rôles privilégiés | SEC |
| Référence de sécurité | OWASP ASVS niveau 2 | Grille de la recette de sécurité |
| Sauvegarde | Journaux de transactions et objets copiés, chiffrés, sur un second site ; objectif 15 minutes de perte au plus, reprise en 8 heures ouvrées | Option 2 du DAT, à valider |
| Client terrain | Application web progressive (PWA) installable : service worker, écrans en composants JavaScript légers (Preact, Svelte ou Vue), base locale IndexedDB chiffrée, journal d'opérations | Travail sans réseau, synchronisation automatique au retour du réseau (DAT § 4.5) |
| Synchronisation | API propre : envoi des opérations par lots, réception des changements par curseur, journal des changements par centre | Réutilise les services métier et les droits ; un seul moteur de base |
| Paiements | Interface interne « passerelle Mobile Money », un adaptateur par agrégateur ou opérateur, plus un adaptateur déclaratif sans opérateur | Changer d'opérateur sans toucher les modules ; repli tant que le contrat n'est pas signé (DAT § 4.6) |

Découpe le code selon les modules du DAT : identité, habilitations, référentiels, bénéficiaires, formations, partenaires, conventions, boutique, facturation, paiements, pilotage, documents, services transverses (dont la synchronisation hors ligne). Un module n'accède pas directement aux tables d'un autre ; il passe par ses services. Les noms de tables et de champs sont ceux du Modèle de données (beneficiaire, session\_formation, inscription, contribution…).

C'est ainsi que le backend est organisé : une application Django par module sous `backend/caef/` (`identite`, `habilitations`, `referentiels`, `journal`, `beneficiaires`, `formations`, `documents`, `partenaires`, `conventions`, `boutique`, `facturation`, `paiements`, `pilotage`, `synchronisation`, `notifications`, et `commun` pour les briques partagées). Dans chacune, `services.py` porte les règles métier, `api.py` les vues REST, qui lisent la requête, appellent un service et sérialisent la réponse, et `taches.py` les tâches Celery. Les droits viennent du seul fichier `caef/habilitations/matrice.yaml`, transcrit de la Matrice ; le filtre de centre est appliqué une fois pour toutes dans la couche d'accès aux données (`caef/commun/api.py`). La liste des routes de l'API est dans le DAT, § 4.2.

**Rôles.** La Matrice compte désormais onze rôles internes au MVP : les huit d'origine, plus **RA** (responsable adjoint de centre : mêmes droits que le RC sur son centre, mais droits de validation seulement pendant un intérim déclaré, USR-09) et **CPT** (comptable de centre : boutique et rapprochement des contributions financières, CTR-09, sans accès aux dossiers des bénéficiaires). S'y ajoute **VB** (vendeur ou vendeuse de boutique), actif au pilote, la boutique étant dans le lot 1. Ces trois rôles sont des ajouts du porteur de projet, absents du DM et du CDC. Pour la scolarité, l'AA et le CPT encaissent ; le CPT affecte les paiements, rapproche les relevés de l'opérateur et demande les remboursements, que valide le RC ou le RA en intérim. Le mode hors ligne est réservé aux rôles de terrain du centre ; ADM, DG, RSE et SE travaillent en ligne seulement. Le 13/10/2026, le porteur de projet a fourni l'organigramme des centres : les écrans affichent ses titres (responsable du centre, adjoint, assistante, chef comptable, chef matériels, moniteurs, gérante de la salle d'exposition et de la boutique) sur des codes de rôle inchangés, et **CMT** (chef matériels) s'ajoute en consultation, sans donnée nominative et en ligne seulement ; la cheffe de classe est une élève sans compte, désignée sur son inscription (Matrice § 2.1).

## 4. Ordre de construction du lot 1

Le lot 1 couvre, selon le PRD : ADM, USR, BEN-01 à BEN-13, FOR, TDB-01 à TDB-04, TDB-09, REP-01 à REP-03, DOC-01, MIG-01, la RSE (PAR, CNV, CTR, TDB-05), la boutique (BOU-01 à BOU-06 en P0, BOU-07 à BOU-11 et BOU-15, salle d'exposition, en P1, attendus au pilote), la source unique SRC-01 à SRC-04, le hors ligne d'abord (OFF-01 à OFF-08), la scolarité et les paiements (PAY-01 à PAY-11, SEC-14 ; facturation de la scolarité et parcours Mobile Money avec passerelle mis en service après H15 et H16) et les exigences non fonctionnelles P0. Construis-le dans cet ordre : chaque étape s'appuie sur la précédente, et la sécurité vient en premier parce qu'elle est très difficile à ajouter après coup.

| Étape | Contenu | Exigences | Terminée quand |
| --- | --- | --- | --- |
| 0. Socle | Dépôt, Docker Compose, intégration continue qui lance les tests à chaque modification, environnements développement et recette, générateur de données fictives (Plan de tests § 3.3) ; coquille PWA, base locale chiffrée, journal d'opérations, API de synchronisation et enrôlement des appareils (DAT § 4.5) | Exigences non fonctionnelles P0, dont OFF-01 à OFF-08 | Une page « bonjour » déployée en recette par la chaîne automatique, installée sur un téléphone et ouverte en mode avion |
| 1. Identité et habilitations | Centres, zones, périodes, référentiels ; comptes, rôles, affectations par centre, double authentification ; Matrice en fichier de données (onze rôles, dont RA, CPT et CMT) ; modules activés par centre, vérifiés côté serveur, synchronisation comprise (ADM-08, DAT § 4.7) ; intérim du RC au profit du RA (USR-09) ; journal d'audit | ADM, USR, SEC | Les tests de droits générés depuis la Matrice passent ; un accès inter-centres est refusé et journalisé |
| 2. Bénéficiaires | Recherche obligatoire avant création, détection des doublons, candidature, complétude, validation ou rejet motivé, liste d'attente, transfert, fusion tracée, fiche bénéficiaire | BEN-01 à BEN-13 | Scénario SC-01 et ses critères CA-01a à CA-01d passent |
| 3. Formations | Formations, sessions, séances, formateurs, inscriptions, saisie des présences sur téléphone, évaluations, clôture, attestations PDF | FOR | Scénario SC-02 et ses critères CA-02a à CA-02e passent, y compris à 360 pixels de large |
| 4. Documents | Pièces jointes rattachées aux dossiers, formats et taille contrôlés, liens signés | DOC-01 | Aucun document accessible sans droit, même avec le lien |
| 5. Pilotage et rapports | Calcul nocturne des indicateurs du lot 1 (IND-01 à IND-10, IND-30 à IND-33, IND-35, IND-40), tableau de bord national et de centre, exports et rapports journalisés | TDB-01 à TDB-04, TDB-09, REP-01 à REP-03 | Les résultats sur le jeu de référence sont exactement ceux attendus ; « non renseigné » s'affiche au lieu de 0 |
| 6. RSE | Après le socle (étapes 0 à 5) : partenaires, opportunités, propositions, conventions, contributions (financières et en nature, totaux par devise), tableau de bord RSE | PAR, CNV, CTR, TDB-05 | Scénarios SC-03 à SC-05 passent ; promis, signé, reçu et exécuté ne sont jamais additionnés |
| 7. Boutique | En parallèle de la RSE : catalogue et prix historisés, stock, dépôts-ventes, vente et reçu numéroté, clôture de caisse quotidienne, inventaire, reversements aux productrices, tableau de bord et exports ; salle d'exposition comme second emplacement de stock ; rôle VB | BOU-01 à BOU-11, BOU-15 | Scénario SC-06 et les cas de test boutique passent ; reçus sans trou, stock = somme des mouvements |
| 8. Clôture mensuelle (SRC) | État de rapprochement du mois (ventes, caisses, reversements, contributions financières reçues), vérification CPT, validation RC, écarts motivés, verrouillage du mois, régularisation datée ; statut de la dernière clôture sur le tableau de bord de centre (E-SRC-01, cloture\_mensuelle, ligne\_rapprochement) | SRC-01, SRC-02, SRC-04 | TF-SRC-01 à 04 et le cas de séparation des tâches passent ; CPT et RC voient les mêmes totaux, paiements de scolarité compris ; un mois verrouillé refuse toute modification |
| 9. Scolarité et paiements | Services payants et tarifs datés, échéances et références de paiement, exonérations, encaissements en espèces et Mobile Money, affectation, adaptateur déclaratif et déclaration hors ligne (parcours C), rapprochement quotidien, remboursements ; adaptateur de l'agrégateur dans son environnement de test ; règlements Mobile Money de la boutique par ce module | PAY-01 à PAY-11, SEC-14 | Scénario SC-09 et les cas TF-PAY passent sur la passerelle simulée ; seul un paiement confirmé par l'opérateur compte comme encaissement |
| 10. Reprise des registres papier | Inventaire des livrets et feuilles volantes, saisie ou numérisation contrôlée avec rapport d'anomalies, d'abord sur échantillon ; les divergences entre comptable et responsable sont importées avec le statut « à vérifier », jamais arbitrées | BEN-08, MIG-01, SRC-03 | Répétition réussie selon le Plan de tests § 7.2 |
| 11. Durcissement | Revue de sécurité ASVS, tests de charge, sauvegarde et restauration testées, supervision | PERF, DISP, OPS | Version testable remise pour les campagnes C2 à C5 |

Montre une démo au client à la fin de chaque étape, sur des données fictives. Ne passe pas à l'étape suivante si les tests de droits de l'étape 1 ne sont plus verts.

**Avancement au 14/10/2026.** Le backend couvre les étapes 0 à 9 côté serveur ; les écrans et l'application terrain restent à faire, ainsi que les étapes 10 et 11.

| Étape | Fait côté serveur | Reste à faire |
| --- | --- | --- |
| 0. Socle | Dépôt, Docker Compose (web, worker, beat, PostgreSQL, Redis, MinIO, Nginx), intégration continue GitHub Actions, générateur de données fictives, API de synchronisation et enrôlement des appareils | Environnement de recette déployé ; coquille PWA, base locale chiffrée et journal d'opérations côté appareil |
| 1. Identité et habilitations | Comptes nominatifs, Argon2, TOTP et codes de secours, affectations, intérims, modules par centre, Matrice en fichier de données et tests générés, journal d'audit en ajout seul | Écrans d'administration |
| 2 à 4. Bénéficiaires, formations, documents | Services et API : recherche réseau, doublons et fusion réversible 30 jours, candidatures, transferts, sessions, présences, évaluations, attestations, pièces jointes par lien signé | Écrans, PDF des attestations, essais à 360 pixels |
| 5. Pilotage et rapports | Calcul nocturne de 29 indicateurs, fiches d'indicateurs, rapports R-01 à R-04, exports journalisés | Tableaux de bord à l'écran |
| 6 à 8. RSE, boutique, clôture mensuelle | Services et API complets, dont reçus numérotés par série d'appareil, caisse, inventaire, reversements, état de rapprochement et verrouillage du mois | Écrans |
| 9. Scolarité et paiements | Services payants, tarifs, échéances, exonérations, paiements en espèces et Mobile Money, passerelles déclarative et simulée, notifications signées, relevés opérateur, remboursements | Adaptateur de l'agrégateur, quand H16 sera tranchée ; écrans |
| 10 et 11. Reprise et durcissement | Rien | Tout |

**Module boutique (BOU, ajout du porteur de projet).** Dans le lot 1 (H14 tranchée), construit après le socle en parallèle de la RSE ; le rôle VB est actif au pilote. Tables du Modèle : PointDeVente, Produit, PrixProduit, Depot, MouvementStock, Vente, LigneVente, Reglement, SessionCaisse, Inventaire, Reversement, IntérimResponsable, et pour la clôture mensuelle cloture\_mensuelle et ligne\_rapprochement. Règles à respecter :

- Numéro de reçu continu, unique et sans trou par série : chaque appareil enrôlé sur le point de vente a sa série et attribue ses numéros lui-même, en ligne comme hors ligne (ex. CMR-B-000127) ; unicité sur (point de vente, série, numéro) ; un numéro dont la vente échoue est consigné comme annulé (BOU-06, OFF-08).
- Le stock est la somme des mouvements (MouvementStock), écrits dans la même transaction que la vente ; jamais un champ modifiable.
- Aucune suppression : une vente ou un mouvement s'annule par contre-écriture motivée et tracée.
- Le Mobile Money passe par le module paiements : confirmé par l'opérateur, ou déclaré avec l'identifiant de transaction puis rapproché ; virement et chèque sont déclarés avec leur référence ; aucun autre paiement électronique (PAY-13).
- Montants en GNF entiers ; aucune donnée sur l'acheteur.
- Séparation des tâches : qui a saisi les ventes du jour ne valide pas la clôture de caisse ; qui a compté un inventaire ne valide pas son ajustement ; un reversement est préparé par le CPT et validé par le RC ou le RA.
- Double authentification obligatoire pour le CPT ; le VB ne voit aucune fiche bénéficiaire.
- Le RA ne valide ce que valide le RC que pendant un intérim déclaré (USR-09, dates de début et de fin) ; refus après la date de fin.
- Un seul point de vente par centre au MVP, mais l'entité PointDeVente existe dès le départ.
- Clôture mensuelle : le CPT vérifie, le RC (ou le RA en intérim) valide, jamais la même personne ; après validation, le mois est verrouillé et une correction passe par une écriture de régularisation datée du mois courant, référencée au mois corrigé (RG-SRC-02, RG-SRC-03).

**Hors ligne d'abord et paiements Mobile Money (demandes du 13/10/2026, à formaliser par la Direction Générale).** Le détail est dans le DAT (§ 4.5, 4.6 et 5.6), la SFD (sections 2.3 et 12) et le Modèle de données (sections 8 et 9). Règles à respecter :

- Chaque écran de terrain est conçu hors ligne dès sa première version : il lit la base locale, écrit dans le journal d'opérations et affiche l'état de synchronisation ; jamais un appel réseau bloquant.
- Conflits : écritures en ajout seul sans conflit ; présence la plus récente retenue ; fiches fusionnées champ par champ, un même champ modifié des deux côtés part dans la file « À résoudre » ; opération datée d'un mois verrouillé placée en « Écriture tardive ».
- Codes lisibles attribués par le serveur à la synchronisation ; l'appareil affiche un code provisoire.
- Appareil enrôlé par le RC ou l'ADM ; code personnel de 6 chiffres au moins, verrouillage après 15 minutes d'inactivité, reconnexion en ligne exigée après 72 heures, effacement après 5 codes erronés ; alerte au RC après 48 heures d'opérations en attente ; horloge décalée de plus de 5 minutes signalée.
- Paiements : montants en GNF entiers, commission de l'opérateur stockée à part (brut, commission, net) ; consultation du statut à 1, 5, 15 et 60 minutes si la notification manque ; déclaration hors ligne « Non retrouvé » après 24 heures ; rapprochement nocturne avec le relevé de l'opérateur.
- Remboursement demandé par le CPT, validé par le RC ou le RA en intérim, jamais par la même personne ; clés de la passerelle dans le coffre de secrets, aucun appel réel hors production.

## 5. Positions d'attente sur les points encore ouverts

Plusieurs décisions appartiennent à la Direction Générale et au comité de pilotage. Ne les tranche pas dans le code : construis sur la position d'attente ci-dessous et rends la valeur **paramétrable** quand c'est indiqué, pour qu'un changement de décision ne coûte qu'un réglage.

| Point ouvert | Position d'attente | Comment le coder | Référence |
| --- | --- | --- | --- |
| Comptabilité | Aucune gestion comptable dans l'outil ; la boutique fournit seulement des exports (BOU-10) | Simple champ texte « référence comptable » sur la contribution | PRD, H6 |
| Travail hors ligne | Hors ligne d'abord pour les écrans de terrain ; identification locale valable 72 heures sans connexion en ligne ; alerte au RC après 48 heures d'opérations en attente | Paramètres ; durée à confirmer par le comité de pilotage | PRD, H11, OFF-06, OFF-07 ; DAT § 4.5 |
| Tarifs de la scolarité et des services | Non arrêtés : construire le module, ne pas mettre en service la facturation de la scolarité | Tarifs saisis par l'ADM, datés, par centre ; aucune valeur codée en dur | PRD, H15 |
| Passerelle Mobile Money | Non choisie : adaptateur déclaratif et parcours C d'abord ; adaptateur de l'agrégateur ensuite, dans son environnement de test | Interface interne unique, un adaptateur par fournisseur | PRD, H16 ; DAT § 4.6 |
| Modules activés au pilote | Tous les modules optionnels activés au CAEF Cameroun ; vente directe possible depuis la salle d'exposition | Activation lue dans la table module\_centre ; aucune condition codée sur un centre ; « Module non activé » au lieu de 0 dans les chiffres | SFD, PO-12 ; PRD, ADM-08 |
| Hébergement | Non décidé | Rester portable : Docker, S3 compatible, aucun service propre à un fournisseur | DAT § 10 |
| Pile technique | Django ou Laravel, rendu serveur | Ton choix, écrit dans le dépôt | DAT § 10 |
| Objectifs de sauvegarde | 15 minutes de perte au plus, reprise en 8 heures ouvrées | Sauvegarde continue des journaux de transactions | DAT, option 2 |
| Seuil de doublon probable | Score de 60 ou plus bloque la création | Paramètre ; critères de rapprochement isolés dans une fonction | SFD, CA-01a ; PRD, BEN-05 |
| Bénéficiaire active | Inscription en cours ou achevée depuis moins de 90 jours | Paramètre | Référentiel, R1 |
| Devises : franc guinéen (GNF) de travail ; USD ou EUR possibles pour les contributions | Totaux par devise (GNF, USD, EUR), aucun total multi-devises sans taux daté | Montant, devise, taux et source du taux stockés sur chaque contribution | Référentiel, R2 ; RG-CTR-06 |
| Petits effectifs | Masqués sous cinq personnes hors du centre | Paramètre | Référentiel, R3 |
| Circuit de validation RSE | Avis du centre, validation Direction Générale | Circuit paramétrable par type de document | PRD, H5 |
| Indicateurs nationaux | Seuls les indicateurs à fiche validée s'affichent | Statut de fiche par indicateur ; non validé = invisible au national | PRD, H10 ; TDB-01 |
| Seuil de présence pour l'achèvement | 80 % par défaut | Réglable par formation | SFD |

La liste complète des hypothèses (H1 à H16) et des écarts (A1 à A16) est dans le PRD. Si tu tombes sur une question qu'aucun document ne tranche, choisis l'option la plus restrictive pour les données, note-la dans un fichier DECISIONS.md du dépôt et signale-la au client.

**Où se règlent ces positions dans le backend.** Chaque point ouvert est un paramètre de `settings.CAEF`, lu dans une variable d'environnement (`backend/.env.example`) ; aucune valeur n'est codée en dur. Les principaux :

| Point ouvert | Variable d'environnement | Valeur par défaut |
| --- | --- | --- |
| Champs obligatoires du dossier (H4) | `CHAMPS_REQUIS_DOSSIER` (paramètre interne) | nom, prénoms, sexe, zone, consentement (date et mode), naissance |
| Seconde validation DG d'une proposition (H5) | `CAEF_SEUIL_SECONDE_VALIDATION_PROPOSITION` | vide : pas de seconde validation |
| Tarifs de la scolarité (H15) | table `tarif_service`, saisie par l'ADM sur décision DG | aucun tarif, donc aucune échéance créée |
| Passerelle Mobile Money (H16) | `CAEF_PASSERELLE_MOBILE_MONEY` | `declaratif` ; `simulateur` possible hors production |
| Centre des paiements sans référence valide (H16) | `CAEF_CENTRE_PAIEMENTS_NON_REFERENCES` | vide : transaction orpheline, rattachée à la déclaration |
| Travail hors ligne (H11) | `CAEF_HORS_LIGNE_VALIDITE_HEURES`, `CAEF_ALERTE_SYNCHRO_HEURES`, `CAEF_ECART_HORLOGE_SECONDES` | 72 heures, 48 heures, 300 secondes |
| Seuils de doublon | `CAEF_SEUIL_DOUBLON_BLOQUANT`, `CAEF_SEUIL_DOUBLON_INFORMATIF` | 60 et 40 |
| Bénéficiaire active (R1) | `CAEF_JOURS_BENEFICIAIRE_ACTIVE` | 90 jours |
| Petits effectifs (R3) | `CAEF_SEUIL_PETITS_EFFECTIFS` | 5 |
| Seuil de présence pour l'achèvement | `CAEF_SEUIL_PRESENCE_DEFAUT` | 80 %, réglable par formation |
| Inactivité d'un dossier | `CAEF_JOURS_INACTIVITE_DOSSIER` | 365 jours |
| Limite de la clôture mensuelle | `CAEF_CLOTURE_MENSUELLE_JOUR_LIMITE` | le 10 du mois suivant |

Le fichier `backend/DECISIONS.md` liste aussi les lectures restrictives retenues là où la SFD et la Matrice divergent (reprises dans la Matrice, § 5) et les choix de mise en œuvre (numérotation des reçus, écriture tardive, arrondi des reversements).

## 6. Définition de terminé, tests et méthode de travail

### 6.1 Une fonctionnalité est terminée quand

- [ ] Ses critères d'acceptation de la SFD passent, en test automatisé quand c'est possible.
- [ ] Ses règles RG-xxx et ses transitions de statut, autorisées et interdites, ont un test unitaire.
- [ ] Les tests de droits générés depuis la Matrice passent pour les objets qu'elle touche.
- [ ] Les actions sensibles qu'elle contient écrivent au journal d'audit.
- [ ] Elle marche sur téléphone (360 pixels) et sur une connexion lente simulée.
- [ ] Les messages d'erreur sont en français clair.
- [ ] L'intégration continue est verte, sans vulnérabilité critique ou haute dans les dépendances.
- [ ] Si c'est un écran de terrain : il s'ouvre et s'utilise en mode avion, et ses opérations se synchronisent au retour du réseau sans perte ni doublon (OFF-01 à OFF-03).

Le détail des campagnes de vérification qui suivront ton travail est dans le Plan de tests et de recette.

### 6.2 Travailler avec un assistant de code IA

Le vibe coding va vite, mais un assistant ne connaît pas ces règles tant qu'on ne les lui donne pas. Quelques précautions évitent l'essentiel des dérives.

- **Un fichier d'instructions à la racine du dépôt** (par exemple CLAUDE.md ou AGENTS.md), qui reprend les règles de la section 2, la pile, le découpage en modules et le fait que les noms de tables viennent du Modèle de données. L'assistant le relit à chaque session. Il existe : `AGENTS.md`, que `CLAUDE.md` renvoie, reprend les treize règles et la façon de travailler (règles métier dans `services.py`, `ruff check` puis `pytest` avant de pousser).
- **Une tâche à la fois, avec son identifiant.** Donne à l'assistant l'extrait de la SFD concerné (écran, règles, critères d'acceptation) plutôt qu'une consigne vague.
- **Les tests d'abord.** Demande-lui d'écrire le test du critère d'acceptation avant le code, puis de faire passer le test.
- **Relis toi-même chaque contrôle d'accès et chaque requête.** C'est là que les assistants se trompent le plus souvent : un filtre par centre oublié suffit à exposer des dossiers d'un autre centre.
- **Jamais de vraies données dans la conversation** avec l'assistant, ni dans les captures que tu lui montres.
- **Des petites livraisons.** Une branche par tâche, une revue avant fusion, l'intégration continue comme garde-fou.

## 7. Ce qu'il ne faut pas construire maintenant

Le premier risque du projet est un périmètre trop ambitieux (DM § 19). Ces fonctions sont hors du lot 1, et certaines hors du MVP : ne les commence pas, même si elles semblent rapides à ajouter.

| Hors lot 1 | Quand |
| --- | --- |
| Entrepreneuriat, insertion professionnelle, programmes complets, mesure d'impact (IND-11, IND-12, IND-29) | Lot 3, après le bilan du pilote |
| Crèche et garde d'enfants | Plus tard (lot 3 ou cycle suivant), après validation préalable des données d'enfants (A3) |
| Portail partenaire externe | Phase ultérieure (DM § 7.9) |
| Comptabilité générale, paie | Hors produit (H6) ; la facturation des services payants (scolarité) est au lot 1, mise en service après H15 |
| Dérive vers un logiciel de caisse ou de comptabilité : paiement électronique autre que le Mobile Money (PAY-13), comptabilité générale, coût de revient et marge, vente en ligne, terminal de caisse dédié, codes-barres, plusieurs points de vente par centre | Hors produit (A6, BOU-14) ; codes-barres et plusieurs points de vente en P2 (BOU-13) |
| Application mobile native | Hors MVP ; l'application web progressive installable suffit, y compris hors ligne (H11, H12) |
| Commissions ou classement des personnes sur l'activité commerciale | Exclu |
| Ventilation territoriale fine des tableaux de bord | P2 (TDB-08) |
| Gestion des fiches d'indicateurs dans l'outil | P1 (TDB-07) ; le Référentiel fait foi d'ici là |

Si le client te demande l'une de ces fonctions en cours de route, note la demande et renvoie-la au comité de pilotage plutôt que de l'ajouter au lot en cours.
