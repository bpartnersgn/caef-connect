# Plan de tests et de recette CAEF Connect

Oct 12, 2026 · @Bangoura · version 0.2, à valider par le comité de pilotage · mis à jour le 14/10/2026 (état de C1 et des données de test, sections 3.4 et 4.1)

## 1. Objet, périmètre et références

Ce plan décrit comment CAEF Connect sera vérifié avant le pilote, puis avant chaque extension. Il applique la règle du DM § 17 : une fonctionnalité n'est pas livrée parce qu'elle marche en démonstration, mais parce qu'elle satisfait des critères d'acceptation documentés. Il répond au livrable 7 du DM § 1 (cahier de tests et plan de recette) et au livrable 12 du DM § 21.

**Périmètre.** Le MVP tel que défini par le PRD : exigences P0 et P1 des lots 1 et 2, exigences non fonctionnelles comprises. Les exigences P2 (lot 3) recevront un complément de ce plan avant leur développement.

**Module boutique et nouveaux rôles.** Le module boutique (BOU) et les rôles de responsable adjoint de centre (RA), de comptable de centre (CPT) et de vendeur ou vendeuse de boutique (VB) sont des ajouts du porteur de projet, absents du DM et du CDC. Les cas propres à la boutique (TF-BOU, SC-06, TS-12, TS-13, TS-15, TS-16, TP-08, TP-09, TM-07) sont obligatoires pour la recette du pilote : le module boutique est dans le lot 1 (H14 tranchée). Les cas sur l'adjoint, le comptable, l'intérim (USR-09), le rapprochement (CTR-09) et la source unique des chiffres (SRC : TF-SRC-01 à TF-SRC-04, SC-07, TS-18, TM-08) sont joués dès le lot 1, comme la RSE (A14 tranchée). Les cas du hors ligne d'abord et des paiements, demandés le 13/10/2026 (TF-OFF, TF-PAY, SC-08, SC-09, TS-19 à TS-23, TP-10 à TP-12, TE-07, TE-08), sont aussi joués dès le lot 1, comme ceux de l'organigramme, des modules par centre et de la salle d'exposition, demandés le même jour (TF-ORG-01, TF-MOD-01 à TF-MOD-04, TF-BOU-12, TS-24, TS-25).

**Références.** Chaque cas de test renvoie à un identifiant stable d'un document de conception, ce qui permet de prouver la couverture exigence par exigence.

| Document | Ce qu'on y teste | Identifiants repris |
| --- | --- | --- |
| PRD CAEF Connect | Exigences fonctionnelles et non fonctionnelles | ADM, USR, BEN, FOR, PAR, CNV, CTR, TDB, REP, BOU, SRC, PAY, OFF, SEC, DAT, UX, PERF, DISP, MIG… |
| SFD du MVP | Scénarios, critères d'acceptation, règles de gestion, écrans | SC-01 à SC-09, CA-xx, CA-T1 à CA-T3, RG-xxx, E-xxx |
| Matrice des rôles et permissions | Une cellule = un cas de test de sécurité | Rôle × objet × action |
| Modèle et dictionnaire des données | Contrôles de champs, unicité, statuts | Entités et champs |
| DAT détaillé | Sécurité technique, performance, sauvegarde, déploiement | ARC, OPS, objectifs RPO et RTO |
| Référentiel des indicateurs | Formules, exclusions, niveau de validation | IND-01 à IND-50 |
| Plan de déploiement | Pilote, reprise des données, bilan d'adoption | Phases, jalons |

Une matrice de traçabilité (exigence, cas de test, résultat, anomalie) est tenue dans l'outil de suivi des tests ; elle est la preuve présentée au comité de pilotage à chaque jalon.

## 2. Stratégie : cinq campagnes

Les quatre volets du DM § 17 (fonctionnel, sécurité, performance, utilisateur) deviennent quatre campagnes successives, C2 à C5, précédées d'une campagne automatique, C1, qui tourne à chaque modification du code. L'ordre compte : on ne demande pas aux utilisateurs des centres de juger un outil qui laisse encore voir les dossiers d'un autre centre.

&#91;embedded content: stratégie de test · cinq campagnes (DM § 17)\]

| Campagne | Question à laquelle elle répond | Qui exécute | Où | Quand |
| --- | --- | --- | --- | --- |
| C1 Tests automatisés | Le code respecte-t-il les règles et les droits, sans régression ? | Équipe de développement | Intégration continue | À chaque modification |
| C2 Recette fonctionnelle | Les processus marchent-ils comme la SFD le décrit, y compris dans les cas d'erreur ? | Testeur fonctionnel et responsable suivi-évaluation | Recette | Fin de chaque lot |
| C3 Recette de sécurité | Chacun ne voit-il et ne fait-il que ce que la matrice autorise ? | Testeur sécurité, puis prestataire d'intrusion | Préproduction | Après C2, avant toute donnée réelle |
| C4 Performance et exploitation | L'outil tient-il sur les connexions des centres, et sait-on le restaurer ? | Équipe technique et exploitation | Préproduction et centre pilote | Après C3 |
| C5 Recette utilisateur | Les responsables métier reconnaissent-ils leurs pratiques validées ? | Utilisateurs clés du centre pilote | Préproduction avec données fictives | Après C4 ; se termine par le PV |

Après le procès-verbal, le pilote (phase 4 du DM, phase 5 du Plan de déploiement) prolonge la vérification sur les données réelles ; ses mesures d'adoption et de qualité sont décrites à la section 8.

## 3. Environnements, comptes de test et jeux de données

### 3.1 Environnements

| Environnement | Usage | Données | Particularités |
| --- | --- | --- | --- |
| Développement | C1 en local et dans l'intégration continue | Jeu synthétique généré | Base recréée à chaque exécution |
| Recette | C2 | Jeu de référence fictif (3.3) | Mise à jour à chaque livraison de lot ; bandeau « Recette » permanent |
| Préproduction | C3, C4, C5, répétition de la reprise | Jeu de référence, puis échantillon de reprise pseudonymisé | Configuration identique à la production (DAT) : mêmes versions, mêmes règles de pare-feu, double authentification active |
| Production | Pilote, contrôles après mise en service | Données réelles | Aucun test destructif ; seuls les tests de fumée et la restauration sur une copie isolée |

Aucune donnée réelle de bénéficiaire n'est copiée en recette ou en développement (DM § 11.5). L'échantillon de reprise utilisé en préproduction est pseudonymisé (noms, téléphones et adresses remplacés) et supprimé après la répétition, avec un procès-verbal de suppression.

### 3.2 Comptes de test

Chaque environnement de test dispose d'au moins un compte par rôle et par centre, pour que chaque cellule de la matrice soit jouable : administrateur national, Direction Générale, responsable de centre, agent administratif, responsable pédagogique, formateur, responsable RSE, responsable suivi-évaluation, responsable adjoint de centre (RA), comptable de centre (CPT), chef matériels (CMT), plus un vendeur ou une vendeuse de boutique (VB) dans chacun des deux centres de test, tous deux dotés d'une boutique. Les deux centres portent des données fictives : « CAEF Cameroun (Dixinn) » reproduit le centre pilote, et « Centre de test B », sans aucun droit pour les comptes du premier, sert de cible aux tests de cloisonnement. La devise de travail est le franc guinéen (GNF) ; quelques contributions en USD et en EUR testent les totaux par devise. Des comptes à rôles multiples (par exemple responsable pédagogique et formateur, agent administratif et vendeur de boutique, ou comptable affecté à deux centres) testent le cumul de droits.

Deux comptes RA sont préparés pour le centre pilote : l'un sans intérim, l'autre bénéficiaire d'un intérim du responsable de centre déclaré à dates connues, pour jouer USR-09 avant, pendant et après la période. Chaque compte CPT a la double authentification active dès sa création.

Chaque compte de terrain dispose d'au moins un appareil enrôlé : deux téléphones Android d'entrée de gamme et une tablette pour la boutique au CAEF Cameroun (Dixinn), plus un appareil révoqué ; les comptes ADM, DG, RSE, SE et CMT n'en ont pas, car ils travaillent en ligne seulement. Un compte marchand de test de l'opérateur ou de l'agrégateur, avec des numéros de payeuses fictifs, sert aux paiements Mobile Money.

### 3.3 Jeu de données de référence

Le jeu de référence est un fichier versionné avec le code. Pour chaque indicateur, le résultat attendu est calculé à la main à l'avance, ce qui permet de tester les formules du Référentiel des indicateurs sans débat sur le bon chiffre.

| Contenu | Volume | Cas pièges inclus |
| --- | --- | --- |
| Bénéficiaires | 300 réparties sur les deux centres de test | Paires de quasi-doublons (accent, inversion nom et prénom, année voisine) ; dossier transféré ; dossier fusionné ; champs facultatifs vides |
| Sessions et présences | 12 sessions, 150 séances | Session pleine ; session annulée ; séance non validée ; saisie tardive ; absence justifiée |
| Inscriptions | 400 | Chaque statut de participation ; inscription sans statut final ; dérogation au seuil de présence ; une cheffe de classe par session |
| Partenaires et RSE | 15 partenaires, 25 opportunités | Les montants des scénarios SC-04 et SC-05 ; opportunité perdue ; engagement à échéance dépassée ; contribution en devise étrangère ; don en nature sans valeur |
| Documents | 50 fichiers | Fichier de 10 Mo et de 10 Mo plus un octet ; format refusé ; fichier confidentiel |
| Boutique | Une boutique au CAEF Cameroun (Dixinn), une seconde au Centre de test B (cible du cloisonnement) ; 4 productrices déposantes, dont un groupement, toutes bénéficiaires du jeu ; 20 produits ; 60 ventes sur un mois | Produit en dépôt-vente avec part du centre de 20 % ; prix modifié en cours de mois ; remise motivée ; vente annulée ; règlement mobile money avec référence ; clôture de caisse avec écart ; stock sous le seuil ; reversement partiel ; inventaire d'ouverture |
| Registres papier (reprise) | Jeu fictif du CAEF Cameroun (Dixinn), sur 3 mois : 2 livrets d'inscription, 1 cahier de présences, 1 carnet de reçus de la boutique, 30 feuilles volantes de caisse ; le tableau de la comptable et le cahier de la responsable couvrent les mêmes mois | Un mois où les ventes diffèrent entre la comptable (1 250 000 GNF) et la responsable (1 180 000 GNF) ; bénéficiaire inscrite dans un livret et absente de l'autre ; page illisible ; date manquante ; reçu en double ; feuille volante sans auteur |
| Clôture mensuelle | Un mois complet au CAEF Cameroun (Dixinn) : ventes, 20 clôtures de caisse, 2 reversements, 1 contribution financière reçue | Écart de caisse de 15 000 GNF à motiver ; reversement sans pièce ; contribution en USD ; correction demandée après verrouillage du mois |
| Scolarité et paiements | 3 services payants (inscription, scolarité de deux formations), dont un tarif modifié en cours de mois ; 120 échéances ; 80 paiements | Paiement partiel ; paiement sans référence ; paiement déclaré non retrouvé ; notification reçue deux fois ; notification à signature invalide ; trop-perçu ; exonération par bourse ; remboursement partiel ; relevé de l'opérateur avec une transaction absente de l'outil |
| Hors ligne | 3 appareils enrôlés et 1 révoqué ; journal de 500 opérations sur 3 jours | Même champ modifié sur deux appareils ; présence saisie deux fois ; candidature en doublon probable créée hors ligne ; opération datée d'un mois verrouillé ; horloge décalée de 10 minutes ; droit retiré pendant la coupure |
| Modules par centre | Tous les modules optionnels activés aux deux centres au départ ; salle d'exposition activée au CAEF Cameroun (Dixinn) seulement, avec 5 produits exposés | Désactivation de la boutique du Centre de test B jouée en fin de C2, après les tests de cloisonnement (TF-MOD-01) ; désactivation demandée pendant une caisse ouverte ; décision de la DG sans référence ; article encore exposé |

Un jeu de volume, généré par script à partir des hypothèses de capacité du DAT, sert à C4 (section 7).

### 3.4 Ce qui existe au 14/10/2026

Le backend fournit la commande `python manage.py generer_donnees_fictives`, refusée en production, qui passe par les services métier pour créer un jeu de démonstration entièrement fictif : les deux centres de test, CAEF Cameroun (code CMR) et Centre de test B (code TSB, marqué fictif, exclu des indicateurs nationaux), les zones, les référentiels, la période de l'année, les modules optionnels activés au CAEF Cameroun, une formation, une session, des bénéficiaires aux noms visiblement inventés et quelques opérations de boutique et de RSE. Le mot de passe des comptes vient de `CAEF_MOT_DE_PASSE_DEMO` ou est tiré au hasard et affiché une seule fois.

| Compte | Rôle | Centre |
| --- | --- | --- |
| `adm.national`, `dg.direction`, `rse.national`, `se.national` | ADM, DG, RSE, SE | National |
| `rc.cmr`, `ra.cmr`, `aa.cmr`, `rp.cmr`, `fo.cmr`, `cpt.cmr`, `vb.cmr`, `cmt.cmr` | RC, RA, AA, RP, FO, CPT, VB, CMT | CAEF Cameroun |
| `rc.tsb`, `aa.tsb` | RC, AA | Centre de test B |

Pour atteindre les sections 3.2 et 3.3, il reste à ajouter : le second compte RA avec un intérim daté, un VB et les autres rôles au Centre de test B, les comptes à rôles multiples, les appareils enrôlés, et surtout le jeu de référence lui-même (300 bénéficiaires, résultats d'indicateurs calculés à la main, registres papier fictifs), versionné avec le code.

## 4. C1 Tests automatisés

C1 protège contre la régression : chaque modification du code déclenche la suite complète dans l'intégration continue, et un échec bloque la fusion. Une petite équipe ne peut pas rejouer à la main toute la recette à chaque correction ; ces tests le font à sa place.

| Niveau | Ce qui est testé | Exigence de couverture |
| --- | --- | --- |
| Unitaire | Chaque règle de gestion RG-xxx de la SFD, chaque transition de statut autorisée et interdite, chaque formule d'indicateur | 100 % des RG et des transitions ; 80 % des lignes des modules métier |
| Droits | Pour chaque rôle et chaque action de la matrice, un appel autorisé réussit et un appel interdit renvoie un refus, y compris par adresse directe | 100 % des cellules (généré à partir de la matrice, voir 6.1) |
| Intégration | Base de données réelle (PostgreSQL), stockage d'objets, file de tâches, envoi de notifications simulé | Chaque module avec ses dépendances |
| Bout en bout | Les scénarios SC-01 à SC-09, rejoués dans un navigateur automatisé, en largeur ordinateur et téléphone (360 pixels) | Tous les scénarios du lot, chemins nominaux |
| Statique | Analyse de sécurité du code, dépendances vulnérables, secrets dans le code | Aucune vulnérabilité critique ou haute non traitée |
| Migrations | Chaque migration de schéma appliquée sur une copie du jeu de référence, puis annulée | Toutes les migrations |
| Synchronisation | Rejeu d'un journal d'opérations hors ligne : envoi en double, ordre perturbé, coupure en plein lot, conflit, rejet, mois verrouillé ; navigateur automatisé en mode hors ligne | Toutes les règles RG-OFF ; aucune perte ni doublon |
| Passerelle simulée | Simulateur de l'opérateur : notifications signées, en double, à signature invalide, en retard ou absentes ; relevé avec écarts | Tous les statuts et transitions de la SFD (12.3) ; aucun appel réel à l'opérateur hors production |

Les tests d'indicateurs comparent la sortie du calcul nocturne aux résultats attendus du jeu de référence (3.3), au chiffre près. Une modification de formule sans mise à jour du résultat attendu et de la version de la fiche fait échouer la suite.

Le rapport de C1 (tests passés, couverture, vulnérabilités) accompagne chaque livraison en recette ; une livraison sans rapport vert n'est pas acceptée en C2.

### 4.1 État de C1 au 14/10/2026

L'intégration continue tourne sur GitHub Actions (`.github/workflows/backend.yml`) à chaque poussée sur la branche principale et à chaque demande de fusion qui touche le backend ou la Matrice. Elle enchaîne l'analyse statique (`ruff check`), les contrôles de Django, la vérification qu'aucune migration ne manque, puis `pytest` sur une vraie base PostgreSQL 16. En local, la même suite se lance par `pytest` dans `backend/`, après `pip install -r requirements-dev.txt`.

| Niveau | Couvert aujourd'hui | Reste à faire |
| --- | --- | --- |
| Droits | `test_matrice.py` : le fichier `matrice.yaml` reproduit la Matrice ; chaque cellule rôle, objet et action est accordée dans le centre de l'utilisateur et refusée dans l'autre centre ; intérim du RA ; validation de caisse à défaut de CPT ; rôle suspendu quand son module est désactivé | Appel par l'API de synchronisation pour chaque cellule |
| Règles transverses | `test_scenarios.py` : qui saisit une candidature ne la valide pas ; journal écrit dans la transaction et en ajout seul ; refus hors périmètre journalisé, en service et par l'API ; le formateur ne voit que nom, prénom et code ; jeton d'appareil limité à la synchronisation ; prix et total calculés par le serveur ; mois validé verrouillé ; vente annulée par contre-écriture seulement | Une règle RG-xxx par test pour toute la SFD, transitions de statut interdites |
| Synchronisation | Opération reçue deux fois appliquée une fois ; opération dans un mois verrouillé placée en écriture tardive ; mode hors ligne refusé aux rôles en ligne | Ordre perturbé, coupure en plein lot, conflits champ par champ, navigateur en mode hors ligne |
| Passerelle simulée | Signature invalide refusée et journalisée ; montant confirmé pris chez l'opérateur ; notification idempotente ; identifiant de transaction à usage unique | Notifications en retard ou absentes, consultations à 1, 5, 15 et 60 minutes, relevé avec écarts |
| Indicateurs | Une valeur absente n'est pas zéro | Comparaison au jeu de référence, au chiffre près, pour chaque fiche |
| Bout en bout, statique, migrations | Contrôle des migrations manquantes | Scénarios SC-01 à SC-09 en navigateur (après les écrans), analyse des dépendances et des secrets, rejeu et annulation des migrations, mesure de la couverture |

La suite compte aujourd'hui vingt-deux fonctions de test, dont l'une est générée pour chaque cellule de la Matrice.

## 5. C2 Recette fonctionnelle

C2 vérifie les processus prioritaires de bout en bout, puis les neuf points du DM § 17.1 sur chaque module, puis les formules d'indicateurs. Chaque cas porte un identifiant TF-xx, l'exigence ou le critère couvert, les données d'entrée, le résultat attendu et le résultat obtenu.

### 5.1 Scénarios de bout en bout

Les neuf scénarios de la SFD (section 10) sont joués tels qu'écrits, avec les personnes et les montants indiqués. Chaque critère d'acceptation devient un cas de test.

Quatre scénarios couvrent les demandes du porteur de projet, tous obligatoires pour le pilote : SC-06 pour le module boutique, SC-07 pour la source unique des chiffres et la clôture mensuelle (SRC), SC-08 pour une journée sans réseau (OFF) et SC-09 pour le paiement de la scolarité par Mobile Money (PAY).

| Scénario | Cas de test | Points de contrôle principaux |
| --- | --- | --- |
| SC-01 Inscription d'une bénéficiaire | TF-01a à TF-01d (CA-01a à CA-01d) | Blocage sur doublon probable dans un autre centre ; bouton Soumettre inactif tant qu'un champ obligatoire manque ; liste d'attente sur session pleine ; historique complet |
| SC-02 Session, présences et clôture | TF-02a à TF-02e (CA-02a à CA-02e) | Ouverture impossible sans lieu, capacité ou séance ; présences conservées après coupure réseau, sans doublon ; formatrice limitée à ses sessions ; proposition Achevée ou Non achevée à la clôture ; réouverture motivée |
| SC-03 Suivi d'une opportunité RSE | TF-03a à TF-03d (CA-03a à CA-03d) | Alerte sur partenaire de nom proche ; historique et durée par étape ; alerte à J+7 sur action dépassée ; invisibilité pour le centre non concerné |
| SC-04 Proposition et convention | TF-04a à TF-04d (CA-04a à CA-04d) | Soumission impossible sans validation ; version 2 à la modification ; signature impossible sans document ; engagement en retard le lendemain de l'échéance |
| SC-05 Réception de contributions | TF-05a à TF-05d (CA-05a à CA-05d) | Réception impossible sans justificatif ; validation par une autre personne ; financier et nature jamais additionnés ; aucun nom de bénéficiaire dans R-04 |
| SC-06 De l'atelier à la vente et au reversement | TF-06a à TF-06f | Une productrice dépose des produits ; le vendeur vend ; clôture de caisse validée par la comptable, jamais par le vendeur ; inventaire validé par l'adjoint ; reversement préparé par la comptable, validé par le RC, puis payé ; IND-45 à IND-49 cohérents avec les ventes et le reversement |
| SC-07 Fin de mois : une seule vérité entre comptable et responsable | TF-07a à TF-07e (CA-07a à CA-07e) | Ventes, caisses, reversements et contributions saisis une seule fois ; vue du comptable et tableau de bord du responsable aux mêmes totaux ; état de rapprochement généré ; vérification par le CPT puis validation par le RC, écart motivé ; mois verrouillé, correction par régularisation datée du mois suivant ; statut de clôture au tableau de bord |
| Critères transverses | TF-T1 à TF-T3 (CA-T1 à CA-T3) | Refus et journalisation sur manipulation d'adresse ; export identique à la liste et journalisé ; saisie utilisable à 360 pixels |
| SC-08 Une journée sans réseau | TF-08a à TF-08e (CA-08a à CA-08e) | Présences, candidatures, encaissement et ventes saisis en mode avion ; synchronisation automatique au retour du réseau, sans perte ni doublon ; série de reçus de la tablette ; doublon probable ; champs différents fusionnés sans conflit ; Mobile Money déclaré puis confirmé |
| SC-09 Payer la scolarité par Mobile Money | TF-09a à TF-09e (CA-09a à CA-09e) | Échéances et références créées à l'inscription ; demande de paiement confirmée par l'opérateur ; paiement avec référence affecté seul ; paiement sans référence dans la file du CPT ; rapprochement sans écart, commission à part |

### 5.2 Points de contrôle du DM § 17.1 par module

Pour chaque module du MVP (administration, bénéficiaires, formations, partenaires, conventions, contributions, tableaux de bord, rapports, documents, boutique et clôture mensuelle), le testeur déroule la grille suivante. Les cas sont dérivés des règles RG-xxx et des contrôles de champs du Modèle de données.

| Point de contrôle | Ce qu'on fait | Résultat attendu |
| --- | --- | --- |
| Scénario normal | Chemin nominal de chaque écran E-xxx | Enregistrement conforme, message de confirmation, historique |
| Données manquantes | Laisser vide chaque champ obligatoire, puis chaque champ conditionnel dans sa condition | Refus ciblé sur le champ ; aucune valeur par défaut inventée |
| Données incorrectes | Dates incohérentes, montants négatifs, capacité nulle, téléphone mal formé, texte trop long | Refus avec message compréhensible en français |
| Doublons | Créer un quasi-doublon de bénéficiaire, de partenaire, d'inscription | Alerte ou blocage selon la règle ; fusion tracée |
| Changements de statut | Jouer chaque transition autorisée et tenter chaque transition interdite | Seules les transitions de la SFD sont possibles ; motif exigé quand la SFD le prévoit |
| Droits d'accès | Vérification rapide des boutons visibles par rôle | Conforme à la matrice (contrôle complet en C3) |
| Erreurs de saisie | Double clic sur Enregistrer, retour arrière du navigateur, session expirée pendant la saisie | Pas de doublon ; brouillon conservé ou message clair |
| Exports | Exporter chaque liste avec filtres | Contenu identique à l'écran, colonnes limitées aux droits, export journalisé |
| Rapports générés | Générer chaque rapport R-xx sur une période connue | Chiffres identiques aux indicateurs ; date de calcul et niveau de validation affichés |

### 5.3 Formules d'indicateurs

Chaque fiche du Référentiel des indicateurs reçoit au moins trois cas : un cas nominal, un cas d'exclusion (fusionné, annulé, brouillon) et un cas de donnée manquante. Les montants des scénarios servent de valeurs témoins.

| Cas | Situation | Résultat attendu |
| --- | --- | --- |
| TF-IND-21 | Après SC-04, proposition soumise de 150 000 000 GNF | IND-21 = 150 000 000 GNF |
| TF-IND-22 | Convention signée pour 120 000 000 GNF | IND-22 = 120 000 000 GNF ; IND-23 = 0 |
| TF-IND-23a | Tranche de 60 000 000 GNF reçue, non validée | IND-23 = 0 en vérifié ; 60 000 000 GNF affichés à part en déclaratif |
| TF-IND-23b | Même tranche validée par une autre personne | IND-23 = 60 000 000 GNF ; 60 000 000 GNF encore promis |
| TF-IND-24 | 15 ordinateurs valorisés 45 000 000 GNF sur facture | IND-24 = 45 000 000 GNF, sur une ligne distincte de IND-23 |
| TF-IND-07 | Session clôturée issue de la reprise de données : 20 inscrites, 15 achevées, 3 abandons, 2 sans statut final | IND-07 = 15 / 18 = 83,3 % ; 2 inscriptions signalées manquantes |
| TF-IND-02 | Deux dossiers fusionnés et un dossier transféré | Chaque personne comptée une fois au niveau national |
| TF-IND-ZERO | Un centre sans aucune saisie sur la période | « Non renseigné », jamais 0, et centre listé dans les données manquantes |
| TF-IND-SEUIL | Ventilation nationale d'un groupe de trois bénéficiaires | Valeur affichée « < 5 » |

### 5.4 Module boutique, intérim, rapprochement et source unique

Ces cas complètent les scénarios pour les ajouts du porteur de projet. Tous sont joués dans le lot 1, pour le pilote : TF-BOU (H14 tranchée), TF-USR-09, TF-CTR-09, TF-SRC, TF-ORG et TF-MOD. Les montants sont en GNF entiers.

| Cas | Situation | Résultat attendu |
| --- | --- | --- |
| TF-BOU-01 | Produit créé à 50 000 GNF et vendu, puis prix porté à 60 000 GNF (BOU-01, BOU-11) | Vente passée inchangée à 50 000 GNF ; nouvelle vente à 60 000 GNF ; changement de prix daté, avec son auteur |
| TF-BOU-02 | Dépôt de 10 paniers par une productrice, part du centre 20 % ; puis dépôt pour une personne absente des bénéficiaires (BOU-02) | Stock + 10, dépôt rattaché à la productrice ; second dépôt refusé ; part du centre exigée |
| TF-BOU-03 | Vente de 3 lignes, remise de 10 % sur une ligne, sans puis avec motif ; règlement mobile money sans puis avec référence (BOU-03) | Refus sans motif et sans référence ; total juste en GNF entiers ; aucune donnée sur l'acheteur demandée ; reçu imprimable A4 et 80 mm |
| TF-BOU-04 | 5 ventes dont une échoue pendant l'enregistrement (BOU-06) | Numéros de reçu consécutifs, sans trou ; numéro de la vente échouée consigné comme annulé ; séquence propre à chaque série d'appareil |
| TF-BOU-05 | Stock de 3 sous un seuil de 5, vente de 4 unités, sortie pour perte sans motif (BOU-04) | Alerte de seuil puis de stock négatif ; stock égal à la somme des mouvements, sans champ modifiable ; sortie refusée sans motif |
| TF-BOU-06 | Annulation d'une vente validée, puis tentative de suppression par l'interface et par appel direct (BOU-06) | Vente d'annulation liée, motif exigé, stock rétabli, reçu d'origine conservé au statut annulée ; suppression impossible |
| TF-BOU-07 | Clôture de caisse : 450 000 GNF d'espèces attendus, 440 000 GNF comptés (BOU-05) | Montants théoriques par mode de règlement ; écart de 10 000 GNF à motiver ; statut « validée avec écart » après validation par le comptable |
| TF-BOU-08 | Inventaire : 18 unités comptées pour 20 attendues (BOU-07) | Écart de 2 ; ajustement validé par le RA, enregistré comme mouvement « ajustement inventaire » ; stock à 18 |
| TF-BOU-09 | Ventes de 200 000 GNF des produits d'une déposante, part du centre 20 % ; reversement partiel de 100 000 GNF, puis du solde (BOU-08) | Montant dû 160 000 GNF ; solde 60 000 GNF après le premier reversement, 0 après le second ; chaque reversement préparé par le CPT, validé par le RC ou le RA, avec date et pièce |
| TF-BOU-10 | Export du journal des ventes, des clôtures et des reversements d'un mois (BOU-10) | Lignes identiques à l'écran, annulations visibles en contre-écriture ; export journalisé |
| TF-BOU-11 | Volet boutique du tableau de bord de centre sur le mois du jeu de référence (BOU-09) | Valeurs égales au calcul à la main ; vente annulée exclue de IND-45 et IND-46 ; reversement non payé exclu de IND-47 |
| TF-BOU-12 | Transfert de 5 paniers de la boutique vers la salle d'exposition, vente de 2 paniers depuis la salle d'exposition, retour de 3 paniers (BOU-15, RG-BOU-16) | Stock par emplacement juste à chaque étape, stock total inchangé par les transferts ; vente sur la même série de reçus et la même caisse ; part de la productrice inchangée |
| TF-USR-09 | Intérim du RC déclaré au profit du RA du 1er au 10 du mois ; validations réservées au RC tentées le 5, puis le 11 (USR-09) | Validation acceptée le 5 et tracée comme faite en intérim ; refusée le 11 ; déclaration refusée sans dates ou sans motif ; le RA ne valide jamais sa propre saisie |
| TF-CTR-09 | Le CPT rapproche une contribution financière reçue de 60 000 000 GNF (CTR-09) | Référence de pièce comptable, date d'encaissement constatée et auteur du rapprochement enregistrés ; aucun bouton de validation pour le CPT ; validation toujours par la DG |
| TF-SRC-01 | Une vente de 75 000 GNF, une clôture de caisse et une contribution financière reçue de 60 000 000 GNF saisies une fois ; consultation par le CPT, le RC et dans le rapport mensuel ; recherche d'un écran ou d'un import de ressaisie (SRC-01, RG-SRC-01, CA-SRC-01 à CA-SRC-07) | Mêmes enregistrements et mêmes totaux dans la vue du comptable, le tableau de bord du RC et le rapport ; aucune ressaisie ni import de tableur possible pour ces flux |
| TF-SRC-02 | Clôture du mois sur E-SRC-01 : état de rapprochement généré ; caisse physique inférieure de 15 000 GNF ; vérification par le CPT sans puis avec motif ; validation par le RC (SRC-02, RG-SRC-02) | Totaux par flux et par devise égaux à la somme des enregistrements du mois ; écart refusé sans motif ; statuts à faire, vérifiée, validée avec écart ; auteurs et dates enregistrés |
| TF-SRC-03 | Après validation, tentative de modifier une vente du mois clôturé, puis correction par écriture de régularisation (SRC-02, RG-SRC-03) | Modification refusée ; régularisation datée du mois courant, référencée au mois corrigé, visible dans la clôture suivante ; état du mois clôturé inchangé |
| TF-SRC-04 | Tableau de bord du centre avant, pendant et après la clôture, puis avec un écart motivé (SRC-04, IND-50) | Statut affiché à faire, vérifiée, validée, validée avec écart ; IND-50 (mois validés au plus tard le 10 du mois suivant / mois écoulés) égal au calcul à la main |
| TF-ORG-01 | Ouverture de l'application avec chaque compte du centre pilote ; désignation d'une cheffe de classe, puis d'une seconde dans la même session (Matrice § 2.1) | Titres de l'organigramme affichés (responsable du centre, adjoint, assistante, chef comptable, chef matériels, moniteur, gérante de la salle d'exposition et de la boutique) ; seconde désignation refusée ; mention sur la feuille de présence ; aucun compte créé pour la cheffe de classe |
| TF-MOD-01 | Désactivation de la boutique au Centre de test B, décision de la DG référencée (ADM-08, CA-ADM-01) | Menu Boutique masqué pour tous les rôles du centre ; vente par appel direct et vente synchronisée refusées « Module non activé » ; compte VB suspendu ; données locales du module effacées des tablettes |
| TF-MOD-02 | Tableau de bord national et clôture mensuelle après la désactivation (RG-ADM-20, CA-ADM-02) | Chiffre d'affaires du Centre de test B « Module non activé », pas 0 ; total national « 1 centre sur 2 » ; historique lisible par le RC et le CPT |
| TF-MOD-03 | Désactivation demandée avec une caisse du jour non validée ; désactivation de la seule salle d'exposition avec un article exposé (RG-ADM-19, CA-ADM-03) | Refus motivé dans les deux cas ; acceptée après validation de la caisse et retour de l'article en boutique |
| TF-MOD-04 | Désactivation saisie par l'ADM sans référence de décision, validée par lui-même, puis par la DG ; réactivation le mois suivant (RG-ADM-18, RG-ADM-20) | Refus sans référence ; auto-validation refusée ; RC notifié ; journal complet ; après réactivation, droits et menus rétablis, période désactivée toujours « Module non activé » |

### 5.5 Hors ligne et paiements

Ces cas couvrent les demandes du porteur de projet du 13/10/2026 (OFF-01 à OFF-08, PAY-01 à PAY-11). Ils sont joués dans le lot 1, pour le pilote ; ceux qui appellent la passerelle (TF-PAY-04 à TF-PAY-07, TF-PAY-09) sont joués dans l'environnement de test de l'opérateur, puis rejoués avant la mise en service des parcours Mobile Money avec passerelle (H16).

| Cas | Situation | Résultat attendu |
| --- | --- | --- |
| TF-OFF-01 | Téléphone en mode avion : ouvrir E-FOR-07, saisir les présences, fermer l'application, puis rétablir le réseau (OFF-01, OFF-02, CA-OFF-01) | Écran ouvert sans réseau ; synchronisation lancée seule ; présences reçues une seule fois ; indicateur au vert |
| TF-OFF-02 | Même lot d'opérations envoyé deux fois, puis coupure au milieu d'un lot (OFF-03) | Aucune opération appliquée deux fois ; reprise du lot sans perte |
| TF-OFF-03 | Même champ d'une fiche modifié hors ligne sur deux appareils ; puis deux champs différents (OFF-05, CA-OFF-02) | Conflit dans E-OFF-02 avec les deux valeurs, valeur du serveur conservée ; champs différents fusionnés sans conflit |
| TF-OFF-04 | Droit retiré pendant la coupure ; opération datée d'un mois verrouillé (OFF-04, RG-OFF-07, CA-OFF-04) | Opération refusée, motif dans « Mes rejets » ; écriture tardive transformée en régularisation par le CPT |
| TF-OFF-05 | Deux appareils vendent hors ligne sur le même point de vente ; comptage de caisse avant puis après leur synchronisation (OFF-08, CA-BOU-01) | Chaque reçu porte la série de son appareil, sans trou ni doublon ; comptage refusé tant qu'un appareil n'a pas synchronisé |
| TF-OFF-06 | Appareil sans synchronisation depuis 49 heures ; horloge décalée de 10 minutes ; 72 heures sans connexion en ligne (OFF-06, OFF-07) | Alerte au RC ; opérations marquées « horloge à vérifier » ; application verrouillée, saisies conservées et envoyées à la reconnexion |
| TF-PAY-01 | Tarif de scolarité modifié après l'émission d'échéances (PAY-01, PAY-02) | Échéances émises inchangées ; nouvelles échéances au nouveau tarif ; références de paiement uniques |
| TF-PAY-02 | Exonération saisie, puis validée par son auteur, puis par le RC (PAY-03) | Validation par l'auteur refusée ; restant dû réduit sans encaissement |
| TF-PAY-03 | Encaissement de 50 000 GNF en espèces hors ligne, réparti sur deux échéances (PAY-04) | Reçu dans la série de l'appareil ; échéance la plus ancienne réglée d'abord |
| TF-PAY-04 | Demande de paiement acceptée, refusée, puis restée sans réponse (PAY-05) | « Confirmé » avec reçu ; « Échoué » avec motif ; « Expiré » après la consultation à 60 minutes ; aucun code secret demandé |
| TF-PAY-05 | Paiement de la payeuse avec une référence valide, puis sans référence (PAY-06, CA-PAY-07) | Affectation automatique ; second paiement dans « Paiements à affecter », affecté par le CPT avec un motif |
| TF-PAY-06 | Déclaration hors ligne avec un identifiant présent au relevé, puis avec un identifiant inconnu (PAY-07, CA-PAY-04) | « Confirmé » au rapprochement ; « Non retrouvé » après 24 heures, hors des encaissements confirmés |
| TF-PAY-07 | Notification reçue deux fois ; montant confirmé de 140 000 GNF pour 150 000 GNF attendus (PAY-08, CA-PAY-01, CA-PAY-03) | Un seul paiement et un seul reçu ; restant dû de 10 000 GNF, sans arrondi |
| TF-PAY-08 | Situation des bénéficiaires et tableau de bord du centre sur le jeu de référence (PAY-09) | Dû, payé, exonéré et restant dû égaux au calcul à la main ; impayés listés ; aucune inscription bloquée |
| TF-PAY-09 | Relevé de l'opérateur avec une transaction absente de l'outil et un écart de montant (PAY-10, CA-PAY-08) | Deux écarts signalés au CPT, motif exigé ; totaux du mois identiques sur E-PAY-06, E-SRC-01 et le tableau de bord |
| TF-PAY-10 | Remboursement partiel demandé par le CPT, validé par lui-même, puis par le RC (PAY-11, CA-PAY-06) | Auto-validation refusée et journalisée ; statut « Remboursé partiellement » ; échéance de nouveau due pour le montant remboursé |
| TF-PAY-11 | Vente de boutique réglée par Mobile Money avec une commission de 1 % (RG-PAY-12, RG-BOU-08) | Brut, commission et net affichés ; part de la productrice calculée sur le prix de vente |

### 5.6 Sortie de C2

C2 est terminée quand tous les cas TF des scénarios et des indicateurs du tableau de bord national sont passés, ainsi que TF-USR-09, TF-CTR-09, les cas TF-BOU, TF-SRC, TF-OFF, TF-PAY, TF-ORG et TF-MOD, et qu'il ne reste aucune anomalie bloquante ni majeure ouverte (section 9).

## 6. C3 Recette de sécurité et des habilitations

C3 répond au DM § 17.2 et à l'objectif O5 du PRD : zéro accès inter-centres non autorisé en recette. Elle se joue en préproduction, configurée comme la production, et doit être terminée avant qu'une seule donnée réelle soit chargée.

### 6.1 Habilitations : la matrice, cellule par cellule

La Matrice des rôles et permissions est tenue sous forme de fichier de données (rôle, objet, action, périmètre, autorisé ou non). Ce fichier génère automatiquement les tests de droits de C1 ; C3 les rejoue en préproduction et y ajoute des contrôles manuels.

- **Pour chaque cellule autorisée**, l'action réussit dans le périmètre du compte et échoue hors périmètre (autre centre, autre programme).
- **Pour chaque cellule interdite**, l'action échoue par l'interface et par appel direct à l'adresse, avec un refus journalisé.
- **Pour chaque rôle**, un testeur parcourt manuellement l'application et vérifie qu'aucun menu, bouton, colonne ou export ne laisse voir plus que la matrice ne l'autorise.
- **Pour les cumuls**, un compte à deux rôles reçoit l'union des droits, jamais plus ; une habilitation exceptionnelle expire à la date prévue et son expiration est journalisée.

Toute différence entre la matrice et le comportement est une anomalie bloquante, même dans le sens restrictif, car elle signale que la matrice et le code ne parlent plus de la même chose.

### 6.2 Cas de sécurité

| Cas | Ce qu'on tente | Résultat attendu |
| --- | --- | --- |
| TS-01 Cloisonnement | Modifier l'identifiant d'un dossier dans l'adresse ou dans un formulaire pour viser un autre centre (CA-T1) | Refus, aucune donnée renvoyée, tentative journalisée |
| TS-02 Élévation de privilège | Envoyer un champ rôle ou centre dans une requête de modification de profil | Champ ignoré ou refusé ; aucun changement de droit |
| TS-03 Authentification | Mots de passe faibles, tentatives répétées, réinitialisation | Politique appliquée ; verrouillage temporaire ; lien de réinitialisation à usage unique et durée courte |
| TS-04 Double authentification | Connexion d'un compte privilégié sans code TOTP, avec un code expiré | Accès refusé |
| TS-05 Session | Inactivité au-delà de la durée fixée, réutilisation d'un cookie après déconnexion, connexion depuis un compte désactivé | Session expirée ; cookie invalide ; accès coupé immédiatement |
| TS-06 Documents | Ouvrir un lien de téléchargement expiré, partagé à un autre compte, ou deviner le chemin de stockage | Refus dans les trois cas ; aucun document confidentiel accessible par simple lien (DM, module 9) |
| TS-07 Journalisation | Jouer chaque action sensible : consultation nominative, export, modification de droit, fusion, validation de contribution, déclaration d'intérim ; pour la boutique, annulation de vente, validation de clôture, ajustement d'inventaire, reversement ; vérification et validation de la clôture mensuelle | 100 % présentes au journal avec auteur, date, objet ; journal non modifiable par l'application |
| TS-08 Exports | Exporter avec un rôle sans droit nominatif | Effectifs seulement, aucune colonne nominative |
| TS-09 Injections et scripts | Injection SQL, script dans un champ texte, fichier piégé déposé, requête intersite forgée | Neutralisés ; fichier refusé ou mis en quarantaine |
| TS-10 Transport | Version de TLS, en-têtes de sécurité, accès HTTP non chiffré | TLS conforme au DAT ; redirection vers HTTPS ; en-têtes présents |
| TS-11 Partenaires | Contrôler les rapports et exports destinés aux partenaires (REP-06) | Aucun nom ni coordonnée de bénéficiaire |
| TS-12 Vendeur de boutique | Avec un compte VB, ouvrir une fiche, une liste ou un export de bénéficiaires, par l'interface et par adresse directe | Refus journalisé ; seuls le nom et le code de la productrice déposante apparaissent sur l'article |
| TS-13 Comptable et déposantes | Avec un compte CPT, consulter une productrice déposante, puis une autre bénéficiaire | Identité minimale seulement (nom, prénom, code, téléphone) ; aucune autre bénéficiaire ni aucun autre champ |
| TS-14 Adjoint sans intérim | Avec un compte RA, tenter une validation réservée au RC hors intérim, puis le lendemain de la fin d'un intérim | Refus journalisé ; seuls l'inventaire et l'ajustement de stock de la boutique restent validables en propre |
| TS-15 Séparation des tâches | Valider la clôture d'une journée où l'on a saisi des ventes ; valider l'ajustement d'un inventaire qu'on a compté ; valider un reversement qu'on a préparé ; faire valider par le RA sa propre saisie ; rejouer avec des comptes cumulant VB et un autre rôle | Refus dans chaque cas, par l'interface et par appel direct, avec trace au journal |
| TS-16 Cloisonnement des boutiques | Avec les comptes VB, CPT et RA du CAEF Cameroun (Dixinn), viser les ventes, le stock, la caisse, les reversements ou la clôture mensuelle du Centre de test B | Refus journalisé ; un CPT affecté à deux centres voit ces deux boutiques et aucune autre |
| TS-17 Double authentification du comptable | Connexion d'un compte CPT sans code TOTP, avec un code expiré, puis tentative de désactiver la double authentification | Accès refusé ; désactivation impossible pour le rôle CPT |
| TS-18 Séparation des tâches de la clôture mensuelle | Valider avec le compte CPT une clôture mensuelle qu'il a vérifiée ; vérifier puis valider avec un même compte cumulant CPT et RA ; valider avec le RA hors intérim ; modifier, par l'interface et par appel direct, une vente, une clôture de caisse, un reversement ou une contribution d'un mois verrouillé (SRC-02, RG-SRC-02, RG-SRC-03) | Refus dans chaque cas, journalisé ; RA accepté seulement pendant un intérim déclaré ; mois verrouillé non modifiable, seule la régularisation datée du mois courant est possible |
| TS-19 Appareil perdu ou volé | Sur un appareil enrôlé : 5 codes erronés ; révocation puis reconnexion ; lecture directe de la base locale du navigateur | Données consultables effacées ; appareil révoqué effacé au premier contact ; base locale illisible sans le code ; aucun champ R présent |
| TS-20 Opérations forgées | Envoyer à l'API de synchronisation une opération visant un autre centre, avec un rôle sans droit, ou depuis un appareil révoqué | Refus journalisé ; rien n'est écrit |
| TS-21 Notification de paiement forgée | Notification sans signature, à signature fausse, rejouée, ou au montant modifié | Refus journalisé ; paiement inchangé (SEC-14) |
| TS-22 Montant pris du client | Modifier dans la requête de l'appareil le montant ou le statut d'un paiement Mobile Money | Ignoré ; seul le montant de l'opérateur est retenu |
| TS-23 Rôles en ligne seulement | Tenter d'activer le mode hors ligne avec les comptes ADM, DG, RSE, SE et CMT | Refus ; aucune donnée stockée sur l'appareil |
| TS-24 Module désactivé | Au Centre de test B, boutique désactivée : appel direct à l'API de vente, opération de vente envoyée par la synchronisation, export du journal des ventes, connexion du compte VB, appel avec un rôle cumulant RC et VB | Refus « Module non activé » journalisé dans tous les cas ; aucune écriture ; consultation en lecture seule pour le RC et le CPT seulement |
| TS-25 Chef matériels | Avec un compte CMT, ouvrir une fiche ou une liste de bénéficiaires, la liste des inscrites d'une session, une vente, un paiement, un export ; tenter le mode hors ligne | Refus journalisé ; sessions et séances visibles sans noms ; registre des appareils en lecture ; aucun mode hors ligne |

Tous les cas TS-01 à TS-25 sont joués pour le pilote, dans le lot 1 (H14 tranchée).

### 6.3 Vérifications complémentaires

- **Référentiel OWASP ASVS niveau 2.** La grille de contrôle est remplie point par point ; un point non applicable est justifié.
- **Test d'intrusion externe.** Un prestataire indépendant teste la préproduction pendant C3, avec un compte par rôle. Toute vulnérabilité critique ou haute est corrigée et retestée avant le pilote.
- **Restauration.** La procédure de restauration citée au DM § 17.2 est testée en C4 (section 7), avec le résultat repris au procès-verbal de C3.

## 7. C4 Performance, reprise de données et exploitation

C4 vérifie que l'outil tient dans les conditions réelles des centres (DM § 17.3, PERF-01 à PERF-03), que les données existantes peuvent y entrer proprement (MIG-01) et que l'exploitation sait sauvegarder, restaurer et déployer (DISP-01).

### 7.1 Performance et conditions réelles

Le jeu de volume reprend les hypothèses de capacité écrites dans le DAT (centres, utilisateurs, bénéficiaires, documents, sessions), multipliées par deux pour garder une marge. Les seuils de temps de réponse sont ceux du DAT ; à défaut de seuil validé, la recette retient une page courante affichée en moins de 3 secondes au 95e centile sur la connexion type d'un centre.

| Cas | Ce qu'on mesure | Résultat attendu |
| --- | --- | --- |
| TP-01 Charge nominale | Utilisateurs simultanés prévus par le DAT, parcours mixtes (recherche, saisie, présences, tableau de bord) pendant une heure | Seuils respectés ; aucune erreur serveur |
| TP-02 Pic | Toutes les formatrices saisissent les présences dans le même quart d'heure | Seuils respectés sur l'écran de présences ; aucune présence perdue |
| TP-03 Calculs lourds | Calcul nocturne des indicateurs et génération de rapports PDF pendant la charge nominale | Opérations courantes non dégradées (PERF-02) ; calcul terminé avant l'ouverture des centres |
| TP-04 Grandes listes | Recherche et pagination sur le jeu de volume | Réponse dans les seuils ; index utilisés (PERF-01) |
| TP-05 Connexion dégradée | Profil réseau mobile lent et instable simulé, puis réel au centre pilote | Pages utilisables ; coupure pendant la saisie des présences sans perte ni doublon (CA-02b) |
| TP-06 Équipements | Ordinateurs et téléphones réellement utilisés au centre pilote, navigateurs inventoriés au diagnostic | Affichage et saisie corrects, y compris à 360 pixels (CA-T3) |
| TP-07 Pages légères | Poids des pages de saisie les plus fréquentes | Poids dans la limite fixée par le DAT pour les connexions faibles |
| TP-08 Vente en 3G | Vente de 10 lignes enregistrée et reçu affiché, sur profil 3G simulé, puis réel à la boutique du CAEF Cameroun (Dixinn) | Moins de 2 secondes |
| TP-09 Numérotation concurrente | Plusieurs vendeurs enregistrent en même temps 200 ventes sur le même point de vente, avec des échecs provoqués | Numéros de reçu uniques, continus et sans trou ; numéro d'une vente échouée consigné comme annulé ; stock égal à la somme des mouvements |
| TP-10 Synchronisation après 3 jours | 500 opérations et 20 photos en attente, synchronisées sur profil 3G simulé, puis réel au centre pilote | Données en moins de 2 minutes, sans perte ni doublon ; pièces jointes envoyées ensuite, avec reprise après coupure |
| TP-11 Écran hors ligne | Ouverture des écrans de terrain en mode avion sur les téléphones du centre pilote | Moins de 2 secondes (OFF-01) |
| TP-12 Confirmation Mobile Money | Statut affiché après la notification de l'opérateur, dans l'environnement de test de l'opérateur | Moins de 5 secondes (PAY-05) |

### 7.2 Répétition de la reprise des données

La reprise suit le Plan de déploiement (§ 7) et l'exigence MIG-01. Elle est répétée au moins une fois en préproduction, sur un échantillon pseudonymisé, avant d'être faite en production. Au CAEF Cameroun (Dixinn), tout est sur papier (livrets, feuilles volantes) : la reprise est une saisie ou une numérisation des registres, pas un import de fichiers (SRC-03).

| Étape | Contrôle | Critère de réussite |
| --- | --- | --- |
| TM-01 Inventaire | Chaque registre papier (livret, cahier, feuille volante) et chaque tableau tenu par la comptable ou la responsable inventorié, avec un propriétaire identifié (SRC-03) | 100 % des sources |
| TM-02 Saisie d'échantillon | Rapport d'anomalies par ligne (BEN-08) | Toutes les anomalies classées ; IND-32 mesuré |
| TM-03 Totaux | Nombre de dossiers, d'inscriptions et de sessions avant et après | Écart nul ou expliqué ligne par ligne |
| TM-04 Contrôle de dossiers | Tirage de 30 dossiers comparés à la source par le centre | Aucune erreur de rattachement ; erreurs de champ listées |
| TM-05 Données incertaines | Valeurs douteuses de la source | Marquées « manquante » ou « à vérifier », jamais complétées par supposition |
| TM-06 Validation | Validation signée de la responsable du centre pilote | Procès-verbal de reprise |
| TM-07 Catalogue et stock d'ouverture | Reprise du catalogue de la boutique (produits, prix en vigueur, origines, déposantes) et du stock initial par un inventaire d'ouverture compté, validé par le RC ou le RA ; historique des ventes non repris, sauf décision | Stock initial égal à l'inventaire d'ouverture validé ; chaque déposante rattachée à une bénéficiaire ou à un groupement existant ; aucune vente antérieure importée sans décision du comité de pilotage |
| TM-08 Double registre | Sur le jeu de reprise, rapprocher ligne par ligne les chiffres de la comptable et ceux de la responsable pour la même période, dont le mois où les deux sources divergent (SRC-03) | Chaque divergence non résolue importée au statut « à vérifier », avec les deux valeurs et leur source ; aucune valeur arbitrée par supposition ; liste des divergences signée par le CPT et le RC |

### 7.3 Exploitation et continuité

| Cas | Ce qu'on fait | Résultat attendu |
| --- | --- | --- |
| TE-01 Restauration complète | Restaurer base et objets sur un environnement vierge à partir des sauvegardes du second site | Service rétabli dans l'objectif de reprise (8 heures ouvrées, option 2 à valider) |
| TE-02 Perte de données | Restaurer à un instant précis après une série de saisies horodatées | Perte inférieure à 15 minutes de saisie |
| TE-03 Déploiement et retour arrière | Livrer une version, puis revenir à la précédente | Sans perte de données ; durée d'interruption dans la plage de maintenance |
| TE-04 Supervision | Provoquer une erreur applicative, un arrêt du worker, un disque presque plein, un certificat proche d'expiration | Alerte reçue par l'exploitation pour chacun |
| TE-05 Tâche nocturne en échec | Interrompre le calcul des indicateurs | Tableau de bord affichant l'ancienne date de calcul et un avertissement ; relance possible |
| TE-06 Chiffrement des sauvegardes | Tenter de lire une sauvegarde sans la clé | Illisible |
| TE-07 Restauration et appareils | Restaurer la base à un instant antérieur alors que des appareils ont envoyé des opérations depuis | Les appareils renvoient leurs opérations accusées des 7 derniers jours ; aucune perte |
| TE-08 Passerelle indisponible | Couper la passerelle de paiement pendant une demande de paiement, puis la rétablir | Demande en attente, consultation du statut reprise ; aucun paiement perdu ni compté deux fois ; déclaration toujours possible |

La restauration est rejouée ensuite une fois par trimestre en production, sur une copie isolée, comme exigé par le critère de succès du PRD (restauration testée avec succès).

## 8. C5 Recette utilisateur, pilote et procès-verbal

### 8.1 Recette utilisateur

C5 répond au DM § 17.4 : les responsables métier valident que les processus reflètent les pratiques approuvées. Elle est menée par des utilisateurs clés désignés au centre pilote, formés au préalable, sur la préproduction avec le jeu de référence.

| Profil | Utilisateurs clés | Parcours joués |
| --- | --- | --- |
| Agent administratif | Un au centre pilote | SC-01, recherche et mise à jour de dossiers, exports ; SC-09, encaissement et demande de paiement |
| Responsable pédagogique et formateur | Un de chaque au centre pilote | SC-02 sur téléphone et sur ordinateur, attestations ; une séance saisie hors ligne (SC-08) |
| Responsable de centre | Un au centre pilote | Validations, tableau de bord du centre, rapport mensuel ; SC-07, validation de la clôture mensuelle ; enrôlement des appareils et file « À résoudre » |
| Responsable adjoint de centre | Un au centre pilote | Validations pendant un intérim (USR-09), dont la clôture mensuelle, tableau de bord du centre ; inventaire de la boutique |
| Comptable de centre | Une ou un au centre pilote | Rapprochement des contributions (CTR-09) ; SC-06, clôtures de caisse, reversements, exports ; SC-07, vérification de la clôture mensuelle ; SC-09, paiements à affecter et rapprochement quotidien |
| Vendeur ou vendeuse de boutique | Un au centre pilote | SC-06 sur téléphone : ventes, ouverture et comptage de caisse, entrées en stock ; une journée de vente hors ligne (SC-08) |
| Responsable RSE | Un | SC-03, SC-04, SC-05 |
| Responsable suivi-évaluation | Un | Contrôle qualité, indicateurs, rapports consolidés |
| Direction Générale | Un représentant | Tableau de bord national, lecture des niveaux de validation |

Chaque utilisateur clé reçoit un cahier de parcours rédigé dans ses mots, joue les parcours seul, puis note pour chacun : réalisé sans aide, réalisé avec aide, non réalisé, et ses remarques. Un observateur note les hésitations sans intervenir. Les remarques sont classées en anomalies (section 9) ou en demandes d'évolution, arbitrées par le comité de pilotage.

### 8.2 Procès-verbal de recette

La recette se conclut par un procès-verbal signé, avec la liste des réserves (DM § 17.4). Il prend l'une de trois décisions.

| Décision | Condition |
| --- | --- |
| Recette prononcée | Aucune anomalie bloquante ni majeure ouverte ; C1 à C4 terminées ; parcours C5 réalisés sans aide à au moins 80 % |
| Recette prononcée avec réserves | Aucune anomalie bloquante ; anomalies majeures restantes avec contournement documenté et date de correction avant la fin du premier mois de pilote |
| Recette refusée | Au moins une anomalie bloquante, ou un écart à la matrice d'habilitations, ou une restauration non réussie |

Le procès-verbal porte : la version testée, la synthèse de chaque campagne, la matrice de traçabilité, les réserves avec leur responsable et leur date, le résultat du test d'intrusion et de la restauration. Il est signé par la Direction Générale, la responsable du centre pilote et le responsable de l'équipe de réalisation.

### 8.3 Vérifications pendant le pilote

Le pilote prolonge la recette sur des données réelles. Le bilan de pilote reprend les mesures suivantes, comparées à la situation de référence.

- **Adoption** : IND-40 à IND-43, lus chaque semaine pendant le premier mois.
- **Qualité des données** : IND-30 à IND-35, contrôlés avant chaque publication mensuelle ; IND-50 et écarts entre comptable et responsable suivis à chaque clôture mensuelle (SRC-02).
- **Efficacité** : IND-10 et IND-44 comparés à la mesure faite avant la mise en service.
- **Sécurité** : revue mensuelle du journal des refus d'accès et des exports ; revue des comptes inactifs.
- **Incidents** : tableau des incidents avec gravité, délai de résolution et cause.
- **Hors ligne et paiements** : opérations rejetées et conflits par semaine, appareils en retard de synchronisation, paiements non retrouvés et écarts de rapprochement Mobile Money.

Ces mesures alimentent la décision du comité de pilotage : poursuivre, corriger ou suspendre l'extension (Plan de déploiement, jalon de validation du pilote).

## 9. Gestion des anomalies et non-régression

### 9.1 Gravité

| Gravité | Définition | Exemples | Délai de correction visé |
| --- | --- | --- | --- |
| Bloquante | Fuite de données, perte de données, chiffre faux au tableau de bord national, processus prioritaire impossible | Accès à un dossier d'un autre centre ; présences perdues ; promis additionné au reçu | Avant toute nouvelle livraison en recette |
| Majeure | Fonction importante dégradée, avec contournement possible | Export incomplet ; alerte non déclenchée ; rapport mal mis en page mais juste | Livraison suivante |
| Mineure | Gêne sans effet sur les données ni les droits | Libellé ambigu ; tri incorrect d'une colonne | Planifiée au lot en cours |
| Cosmétique | Apparence seulement | Alignement, couleur | Selon disponibilité |

Toute anomalie touchant aux droits, aux données personnelles ou à un montant est classée au moins majeure, quel que soit son effet visible.

### 9.2 Cycle d'une anomalie

Une anomalie est ouverte avec : le cas de test, l'environnement et la version, les étapes pour la reproduire, le résultat attendu et obtenu, une capture sans donnée réelle. Elle passe ensuite par les statuts ouverte, qualifiée, en correction, livrée, retestée, close (ou rejetée avec motif). Seul le testeur qui l'a ouverte, ou le responsable de la recette, peut la clore après retest. Le comité de recette se réunit chaque semaine pendant les campagnes pour arbitrer les gravités contestées et les demandes d'évolution.

### 9.3 Non-régression

- Chaque anomalie corrigée reçoit un test automatisé qui la reproduit, ajouté à C1.
- À chaque livraison en recette, la suite C1 complète et tous les scénarios bout en bout du lot (SC-01 à SC-09) sont rejoués.
- Avant chaque mise en production, une suite de fumée (connexion par rôle, création d'un dossier fictif, saisie de présences, affichage du tableau de bord, téléchargement d'un document, synchronisation d'un appareil de contrôle) est jouée en préproduction, puis en production avec un compte de contrôle sans accès nominatif.
- Toute modification de la matrice d'habilitations relance l'ensemble des tests de droits générés (6.1).

## 10. Critères d'entrée et de sortie, rôles et livrables

### 10.1 Critères par campagne

| Campagne | Pour commencer | Pour terminer |
| --- | --- | --- |
| C1 | Exigences du lot rédigées dans la SFD ; matrice disponible en fichier de données | Suite verte ; couverture atteinte, y compris les tests de droits de la clôture mensuelle (vérification CPT, validation RC, verrouillage du mois) et du rapprochement (RG-SRC-01 à RG-SRC-03), de la synchronisation (rejeu, conflits, idempotence) et des paiements (passerelle simulée) ; aucune vulnérabilité critique ou haute |
| C2 | Rapport C1 vert ; environnement de recette chargé avec le jeu de référence ; cas TF rédigés | Cas des scénarios SC-01 à SC-09, des indicateurs nationaux, TF-BOU, TF-SRC, TF-OFF, TF-PAY, TF-ORG et TF-MOD passés ; aucune anomalie bloquante ni majeure ouverte |
| C3 | C2 terminée ; préproduction conforme au DAT ; comptes de test par rôle sur les deux centres de test (CAEF Cameroun (Dixinn) et Centre de test B) | 100 % des cellules de la matrice conformes ; TS-01 à TS-25 passés, dont TS-15 et TS-18 (séparation des tâches de la caisse et de la clôture mensuelle, verrouillage du mois) ; vulnérabilités critiques et hautes du test d'intrusion corrigées |
| C4 | C3 terminée ; hypothèses de capacité écrites ; accès au centre pilote organisé | Seuils de performance tenus ; reprise des registres papier répétée et validée, divergences entre sources au statut « à vérifier » (TM-08) ; restauration réussie dans les objectifs ; TP-10 à TP-12, TE-07 et TE-08 passés |
| C5 | C4 terminée ; utilisateurs clés formés ; cahiers de parcours remis | Procès-verbal signé (8.2) |

### 10.2 Rôles

| Rôle | Responsabilités |
| --- | --- |
| Responsable de la recette | Tient ce plan, la matrice de traçabilité et le suivi des anomalies ; anime le comité de recette ; prépare le procès-verbal |
| Équipe de réalisation | Écrit et maintient C1 ; corrige les anomalies ; livre avec un rapport C1 vert |
| Testeur fonctionnel | Rédige et exécute C2 et les contrôles manuels de C3 |
| Responsable suivi-évaluation | Calcule à la main les résultats attendus des indicateurs ; valide TF-IND |
| Exploitation | Exécute C4 (performance, restauration, déploiement) |
| Prestataire de test d'intrusion | Teste la préproduction pendant C3 ; remet un rapport |
| Utilisateurs clés | Exécutent C5 |
| Comité de pilotage | Arbitre les évolutions ; décide sur le procès-verbal et sur le bilan de pilote |

### 10.3 Livrables

- Ce plan, mis à jour à chaque lot.
- Le cahier des cas de test (TF, TS, TP, TM, TE) et le jeu de données de référence avec ses résultats attendus.
- La matrice de traçabilité exigence, cas, résultat, anomalie.
- Un rapport de fin de campagne pour C2, C3 et C4, et le rapport du test d'intrusion.
- Le procès-verbal de reprise des données et le procès-verbal de suppression de l'échantillon.
- Le procès-verbal de recette avec ses réserves.
- La partie « recette » du bilan de pilote.

### 10.4 Points à arbitrer

- [ ] Désigner le responsable de la recette et les utilisateurs clés du centre pilote.
- [ ] Valider les seuils de temps de réponse et les hypothèses de capacité du DAT, utilisés par C4.
- [ ] Choisir l'outil de suivi des tests et des anomalies.
- [ ] Budgéter et contractualiser le test d'intrusion externe.
- [ ] Valider le seuil de 80 % de parcours réalisés sans aide pour prononcer la recette.
- [ ] Faire formaliser par la Direction Générale des CAEF les décisions du porteur de projet du 12/10/2026 (pilote au seul CAEF Cameroun à Dixinn ; RSE et boutique dans le lot 1) ; d'ici là, la recette les applique.
- [ ] Obtenir de l'opérateur ou de l'agrégateur retenu un environnement de test et un compte marchand de test (H16).
- [ ] Faire formaliser les demandes du 13/10/2026 (hors ligne d'abord, paiements Mobile Money) ; d'ici là, la recette les applique.
