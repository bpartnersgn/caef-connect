# SFD du MVP CAEF Connect

Oct 12, 2026 · @Bangoura · mis à jour le 14/10/2026 (mise en œuvre dans le backend, section 11)

## 1. Objet, périmètre et conventions

Cette SFD décrit, pour chaque fonction du MVP, les écrans, les champs, les actions, les statuts et les règles de gestion que l'équipe technique devra implémenter et que la recette vérifiera. Elle détaille les exigences du PRD CAEF Connect (v0.2) sans en ajouter de nouvelles ; tout écart repéré est renvoyé aux points ouverts (section 11).

| Élément | Valeur |
| --- | --- |
| Référence proposée | CAEF-CONNECT-SFD-001, version 0.2 ; section 11 complétée le 14/10/2026 par la mise en œuvre dans le backend du lot 1 |
| Documents d'entrée | PRD CAEF Connect ; Document Maître (DM) ; Cahier des charges fonctionnel (CDC) ; Dossier d'architecture technique (DAT) ; Plan de déploiement |
| Périmètre | Lot 1 livré au pilote (socle opérationnel, puis RSE et boutique construites en parallèle après le socle), soit toutes les exigences P0 et P1 du PRD, y compris le module boutique et salle d'exposition (BOU-01 à BOU-11, BOU-15), l'activation des modules par centre (ADM-08), la source unique et la clôture mensuelle (SRC-01 à SRC-04) et les exigences USR-09 et CTR-09, ajoutés à la demande du porteur de projet (H14 tranchée), ainsi que le hors ligne d'abord (OFF-01 à OFF-08) et la scolarité et les paiements, dont le Mobile Money (PAY-01 à PAY-11), demandés le 13/10/2026 ; pilote dans un seul centre, le CAEF Cameroun (quartier Cameroun, commune de Dixinn, Conakry) |
| Hors périmètre | Exigences P2 et P3 du PRD (dont BOU-12 à BOU-14 : consolidation nationale boutique, codes-barres, plusieurs points de vente, coût de revient, vente en ligne ; PAY-12 et PAY-13 : reversements payés par Mobile Money, carte bancaire) ; modules crèches (prévus plus tard, A3 tranchée), communication publique, insertion, entrepreneuriat, portails externes |
| Documents liés | Matrice des rôles et permissions ; Modèle et dictionnaire des données ; Référentiel des indicateurs ; Plan de tests et de recette |

**Module boutique.** Presque tous les CAEF ont une boutique où ils vendent leur production. Le module boutique (section 9) enregistre le catalogue, le stock, les ventes, la caisse du jour et les reversements aux productrices en dépôt-vente. Il est demandé par le porteur de projet et absent du DM et du CDC. Il fait partie du lot 1 livré au pilote (H14 tranchée) : construit après le socle, en parallèle de la RSE, avec BOU-01 à BOU-06 en P0 et BOU-07 à BOU-11 en P1, attendus au pilote.

**Pilote et source unique.** Le pilote se déroule dans un seul centre, le CAEF Cameroun à Dixinn, où tout est encore tenu sur papier (livrets, feuilles volantes) et où les chiffres de la comptable diffèrent de ceux de la responsable du centre. La section 9.8 fait de CAEF Connect la seule source des montants et ajoute une clôture mensuelle rapprochée (SRC-01 à SRC-04). Ces choix, comme la RSE dans le lot 1 (A14) et la crèche reportée (A3), ont été tranchés par le porteur de projet le 12/10/2026 et restent à formaliser par la Direction Générale des CAEF.

**Hors ligne et Mobile Money.** Le 13/10/2026, le porteur de projet a demandé que la plateforme reste utilisable sans Internet et se synchronise automatiquement au retour du réseau, et que la scolarité et les services associés puissent être payés par Mobile Money. La section 2.3 décrit le travail hors ligne et la section 12 le module scolarité et paiements ; la mécanique technique est dans le DAT détaillé (sections 4.5, 4.6 et 5.6). Ces demandes restent à formaliser par la Direction Générale.

**Organigramme et modules par centre.** Le 13/10/2026, le porteur de projet a fourni l'organigramme des centres : responsable du centre, adjoint du responsable, assistante de la responsable, chef comptable, chef matériels, moniteurs (enseignants et encadreurs), cheffe de classe (une élève) et gérante de la salle d'exposition et de la boutique. Les rôles de l'outil y sont calés (Matrice § 2.1) : le chef matériels (CMT) est ajouté en consultation, et la cheffe de classe reste une bénéficiaire sans compte, désignée sur son inscription. Il a aussi demandé que certains modules, comme la boutique ou la salle d'exposition, puissent être désactivés pour un centre : la section 3 le décrit (E-ADM-10, RG-ADM-17 à RG-ADM-20).

**Conventions de lecture.**

- Les identifiants d'écran sont notés `E-<module>-<n>` (ex. E-BEN-02) et les règles de gestion `RG-<module>-<n>`. Chaque règle cite l'exigence PRD qu'elle détaille.
- Champ **O** = obligatoire, **F** = facultatif, **C** = conditionnel (la condition est précisée), **S** = calculé par le système.
- Les statuts sont écrits entre guillemets dans le texte (ex. « Validée ») et leurs transitions autorisées sont listées dans un tableau ; toute transition absente du tableau est interdite.
- Les rôles cités sont ceux du PRD (section 4). Leurs droits détaillés par action sont dans la Matrice des rôles et permissions ; la SFD n'indique que le rôle principal de chaque action. Trois rôles sont ajoutés à la demande du porteur de projet : responsable adjoint de centre (RA), comptable de centre (CPT) et vendeur ou vendeuse de boutique (VB, actif au pilote). Le MVP compte ainsi onze rôles internes avec le chef matériels (CMT) de l'organigramme, plus VB. À l'écran, les rôles portent les intitulés de l'organigramme (Matrice § 2.1) : assistante du responsable de centre pour l'agent administratif, moniteur pour le formateur, chef comptable pour le comptable de centre, gérante de la salle d'exposition et de la boutique pour VB ; la SFD garde les libellés fonctionnels.
- Chaque donnée décrite ici a sa définition complète (type, format, contrôles) dans le Dictionnaire des données.

**Règles transverses appliquées à tous les modules :**

1. **RG-GEN-01 Cloisonnement.** Toute liste, recherche, fiche, export ou appel d'API est filtré côté serveur sur les centres affectés à l'utilisateur (USR-04, SEC-01).
2. **RG-GEN-02 Traçabilité.** Toute création, modification, changement de statut, validation, export ou suppression logique produit une entrée de journal : utilisateur, date et heure, objet, valeur avant, valeur après (SEC-04).
3. **RG-GEN-03 Pas de suppression physique.** Les objets métier sont archivés ou désactivés, jamais supprimés, sauf application d'une règle de conservation approuvée.
4. **RG-GEN-04 Identifiants.** Chaque objet reçoit un identifiant interne immuable et un code lisible (ex. BEN-CMR-2026-00042) généré par le système ; le numéro de téléphone n'est jamais un identifiant (DAT-01).
5. **RG-GEN-05 Données manquantes.** Un champ non renseigné est stocké comme « non renseigné », distinct de zéro ou d'une valeur vide choisie ; les statistiques les comptent séparément (TDB-09, MIG-01).
6. **RG-GEN-06 Dates.** Les dates sont saisies au format JJ/MM/AAAA, stockées en ISO 8601, et l'heure est celle de Conakry (GMT).

## 2. Principes d'interface et navigation

L'utilisateur arrive sur un tableau de bord propre à son rôle et n'accède qu'aux menus que ses droits autorisent ; un menu sans droit n'est pas affiché, plutôt que grisé (UX-01).

### 2.1 Menus par rôle

| Menu | Admin. national | Direction Générale | Resp. centre | Resp. adjoint (RA) | Agent admin. | Resp. pédagogique | Formateur | Resp. RSE | Suivi-évaluation | Comptable (CPT) | Vendeur boutique (VB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Accueil (tableau de bord) | Oui | Oui | Oui | Oui | Oui | Oui | Oui | Oui | Oui | Oui | Oui |
| Bénéficiaires | Non | Agrégé | Oui | Oui | Oui | Lecture | Non | Non | Oui | Non | Non |
| Formations et sessions | Non | Agrégé | Oui | Oui | Lecture | Oui | Mes sessions | Lecture | Oui | Non | Non |
| Partenaires et RSE | Non | Oui | Son centre | Son centre | Non | Non | Non | Oui | Lecture | Contributions de son centre | Non |
| Boutique | Non | Non (agrégé en P2) | Oui | Oui | Non | Non | Non | Non | Non | Ventes, stock, caisse, reversements, exports | Vente, caisse, stock |
| Clôture mensuelle (E-SRC-01) | Non | Agrégé (lecture) | Oui (validation) | Oui (validation en intérim) | Non | Non | Non | Non | Lecture | Oui (vérification) | Non |
| Rapports | Non | Oui | Oui | Oui | Non | Oui | Non | Oui | Oui | Exports boutique, état de clôture mensuelle | Non |
| Administration | Oui | Référentiels | Intérims de son centre | Intérims (lecture) | Non | Non | Non | Non | Non | Non | Non |
| Journal d'activité | Oui | Lecture | Son centre | Son centre | Non | Non | Non | Non | Lecture | Non | Non |

Le RA voit les mêmes menus que le RC ; ses droits de validation du RC ne s'appliquent que pendant un intérim déclaré (RG-ADM-14), sauf les inventaires et ajustements de stock de la boutique, qu'il valide en propre. Le menu Boutique n'apparaît que si le module boutique et salle d'exposition est activé pour le centre et qu'il a un point de vente actif ; plus généralement, aucun menu d'un module désactivé pour le centre n'apparaît, quel que soit le rôle (RG-ADM-19) ; un RC, RA ou agent admin. qui détient aussi le rôle VB par cumul voit l'écran de vente. Le chef matériels (CMT) voit l'accueil, les formations et sessions de son centre en lecture, sans les noms des inscrites, et le registre des appareils du centre en lecture.

### 2.2 Composants communs

- **Barre supérieure :** nom de l'utilisateur, centre actif (sélecteur si plusieurs centres affectés), indicateur de synchronisation (vert : à jour ; orange : opérations en attente, avec leur nombre ; rouge : hors ligne ; heure de la dernière synchronisation ; accès aux rejets et aux conflits), cloche de notifications, déconnexion (NET-01, OFF-07, NOT-01).
- **Listes :** pagination par 25 lignes par défaut, tri par colonne, recherche plein texte, filtres enregistrables, compteur de résultats, bouton d'export si l'utilisateur a le droit d'exporter (PERF-01, REP-01).
- **Fiches :** en-tête avec code, statut et centre ; onglets par thème ; onglet « Historique » listant le journal de l'objet ; boutons d'action limités aux transitions autorisées pour l'utilisateur.
- **Formulaires :** libellés explicites, champs obligatoires marqués d'un astérisque, contrôle à la sortie du champ, message d'erreur sous le champ en français simple, récapitulatif des erreurs en haut du formulaire (UX-02).
- **Badges de statut :** une couleur par famille de statut, toujours doublée d'un libellé texte (accessibilité, UX-03).
- **Badge de fiabilité :** toute donnée ou tout indicateur a un niveau « Déclaré » ou « Vérifié » affiché à côté de la valeur (TDB-03).

### 2.3 Hors ligne et synchronisation

Les écrans de terrain fonctionnent sans Internet dans l'application installable et se synchronisent seuls au retour du réseau (OFF-01 à OFF-08, demande du porteur de projet du 13/10/2026) ; la mécanique (journal d'opérations, règles de conflit, sécurité de l'appareil) est décrite au DAT détaillé, sections 4.5 et 5.6.

1. **RG-OFF-01 Écrans disponibles hors ligne.** Mes sessions et feuilles de présence (E-FOR-06, E-FOR-07), création d'une candidature et mise à jour des coordonnées (E-BEN-02), consultation des dossiers actifs du centre limitée aux champs du rôle, vente et reçu (E-BOU-04), entrées et sorties de stock (E-BOU-03), ouverture et comptage de caisse (E-BOU-05), comptage d'inventaire (E-BOU-06), situation d'une bénéficiaire et encaissement en espèces ou déclaration d'un paiement Mobile Money (E-PAY-02, E-PAY-04), tableau de bord du centre en lecture, daté de la dernière synchronisation. Toute autre action affiche « Disponible en ligne seulement » (OFF-01).
2. **RG-OFF-02 Synchronisation automatique.** Au retour du réseau, à l'ouverture de l'application, puis toutes les 5 minutes tant que des opérations attendent ; un bouton « Synchroniser maintenant » reste dans la barre supérieure (OFF-02).
3. **RG-OFF-03 Aucune perte, aucun doublon.** Chaque saisie devient une opération conservée sur l'appareil jusqu'à l'accusé du serveur, et un renvoi n'est appliqué qu'une fois ; le brouillon d'un formulaire en cours est sauvegardé toutes les 10 secondes (OFF-03, NET-02).
4. **RG-OFF-04 Revérification au serveur.** Chaque opération est rejouée avec les droits et les règles de cette SFD ; une opération refusée apparaît dans « Mes rejets » avec son motif et peut être corrigée puis renvoyée (OFF-04).
5. **RG-OFF-05 Conflits.** Ventes, règlements, mouvements de stock et encaissements ne sont jamais en conflit. Une présence saisie sur deux appareils garde la plus récente et le formateur est averti. Un même champ d'une fiche modifié des deux côtés garde la valeur du serveur et crée un conflit dans la file « À résoudre » du centre (E-OFF-02), traité par le RC ou le RA. Une candidature créée hors ligne avec un score de doublon de 60 ou plus passe « À vérifier, doublon probable » (OFF-05, RG-BEN-05).
6. **RG-OFF-06 Codes provisoires.** Un objet créé hors ligne porte un code provisoire jusqu'à la synchronisation ; le code définitif (RG-GEN-04) est attribué par le serveur. Les numéros de reçu sont attribués sur l'appareil (RG-BOU-01).
7. **RG-OFF-07 Mois verrouillé.** Une opération datée d'un mois déjà validé est refusée et placée en « Écriture tardive » ; le CPT la transforme en régularisation (RG-SRC-03).
8. **RG-OFF-08 Appareil.** Le mode hors ligne n'existe que sur un appareil enrôlé par le RC ou l'admin. national (E-OFF-01), pour les rôles RC, RA, agent admin., RP, formateur, VB et CPT ; code personnel de 6 chiffres au moins, verrouillage après 15 minutes d'inactivité, reconnexion en ligne exigée après 72 heures, effacement des données consultables après 5 codes erronés (OFF-06, PO-09).
9. **RG-OFF-09 Alerte de retard.** Un appareil qui garde des opérations en attente depuis plus de 48 heures est signalé au RC sur son tableau de bord (OFF-07, PO-09).
10. **RG-OFF-10 Poids des pages.** Les écrans de saisie courants visent moins de 500 Ko au premier chargement, puis restent en cache sur l'appareil (NET-01).

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-OFF-01 Appareils du centre | Appareil, utilisateur principal, série de reçus, dernière synchronisation, opérations en attente, « horloge à vérifier », statut ; actions Enrôler, Révoquer (OFF-06, OFF-07) | Resp. centre, admin. national |
| E-OFF-02 À résoudre | Conflits (objet, champ, valeur du serveur, valeur de l'appareil, auteurs, dates) et écritures tardives ; actions Garder, Remplacer, Régulariser (OFF-05) | Resp. centre ou RA (conflits), CPT (écritures tardives) |

- **CA-OFF-01** Un formateur dont le téléphone est en mode avion ouvre E-FOR-07, saisit les présences d'une séance et ferme l'application ; au retour du réseau, sans action de sa part, les présences arrivent au serveur une seule fois.
- **CA-OFF-02** Deux modifications du même champ d'une fiche, faites hors ligne sur deux appareils, ne s'écrasent pas : le conflit apparaît dans E-OFF-02 avec les deux valeurs.
- **CA-OFF-03** Un appareil révoqué perd ses données locales au premier contact avec le serveur ; ses opérations déjà envoyées restent.
- **CA-OFF-04** L'opération d'un utilisateur dont le droit a été retiré pendant qu'il était hors ligne est refusée à la synchronisation, avec son motif.

### 2.4 Mobile

Tous les écrans sont utilisables sur téléphone. Trois parcours sont optimisés pour une main et un petit écran : saisie des présences (E-FOR-07), consultation de mes sessions (E-FOR-06) et création d'une candidature (E-BEN-02). Ces écrans fonctionnent aussi hors ligne (RG-OFF-01) ; l'encaissement E-PAY-04 rejoint ces parcours.

## 3. Administration

L'administration couvre les centres, les référentiels nationaux, les périodes, les comptes et les rôles ; elle est réservée à l'administrateur national, la Direction Générale ne gérant que les référentiels et le responsable de centre déclarant l'intérim de son adjoint (ADM-01 à ADM-05, ADM-08, USR-01 à USR-07, USR-09). L'admin. national active aussi les modules optionnels de chaque centre, sur décision de la Direction Générale.

### 3.1 Écrans

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-ADM-01 Liste des centres | Code, nom, région, préfecture ou commune, responsable, statut, nombre d'utilisateurs actifs | Admin. national |
| E-ADM-02 Fiche centre | Champs ci-dessous ; onglets Utilisateurs, Historique | Admin. national |
| E-ADM-03 Référentiels | Une liste par référentiel : libellé, code, ordre, actif, date d'effet | Direction Générale |
| E-ADM-04 Périodes et campagnes | Année, période de reporting (mois, trimestre, année), campagne de formation, dates, statut ouverte ou clôturée | Admin. national |
| E-ADM-05 Liste des utilisateurs | Nom, identifiant de connexion, rôles, centres, dernière connexion, statut | Admin. national |
| E-ADM-06 Fiche utilisateur | Identité, rôles par centre, historique des droits, connexions | Admin. national |
| E-ADM-07 Rôles | Liste des rôles et de leurs permissions par action (lecture seule au MVP, configuration par l'équipe technique) | Admin. national |
| E-ADM-09 Intérims du responsable de centre | Centre, RC remplacé, RA bénéficiaire, date de début, date de fin, motif, déclaré par, statut (Planifié, En cours, Terminé, Interrompu), historique (USR-09) | Resp. centre, Admin. national |
| E-ADM-10 Modules du centre | Par centre : module (boutique et salle d'exposition, salle d'exposition, scolarité et paiements, volet RSE du centre, modules à venir), statut Activé ou Désactivé, date d'effet, décision de la Direction Générale (référence et date), saisi par, motif, historique ; blocages en cours affichés avant désactivation (ADM-08) | Admin. national (saisie), Direction Générale (validation), Resp. centre (lecture) |

### 3.2 Champs de la fiche centre

| Champ | Type | O/F | Contrôle |
| --- | --- | --- | --- |
| Code centre | Texte 3 lettres | S | Unique, généré à la création (ex. CMR, KLM), modifiable une fois par l'admin. avant première utilisation |
| Nom officiel | Texte | O | Unique dans le réseau |
| Région, préfecture, commune | Listes du référentiel territorial | O | Cohérence hiérarchique (ADM-05) |
| Adresse, téléphone, courriel institutionnels | Texte | F | Format téléphone +224, courriel valide |
| Responsable de centre | Lien utilisateur | O | Utilisateur actif ayant le rôle Responsable de centre |
| Responsable adjoint de centre | Lien utilisateur | F | Utilisateur actif ayant le rôle Responsable adjoint de centre (RA) sur ce centre |
| Comptable de centre | Lien utilisateur | F | Utilisateur actif ayant le rôle Comptable de centre (CPT) ; un même comptable peut être affecté à plusieurs centres |
| Date d'ouverture | Date | F | Non postérieure à aujourd'hui |
| Capacité d'accueil indicative | Entier | F | Supérieur à 0 |
| Statut | Actif, Inactif | S | Voir RG-ADM-02 |
| Modules activés | Liste | S | Socle toujours actif ; modules optionnels selon E-ADM-10 (RG-ADM-17) |

### 3.3 Champs de la fiche utilisateur

| Champ | Type | O/F | Contrôle |
| --- | --- | --- | --- |
| Nom, prénom | Texte | O |  |
| Identifiant de connexion | Texte | O | Unique ; courriel professionnel ou identifiant attribué |
| Téléphone professionnel | Texte | F | Pour la réinitialisation si retenue |
| Affectations | Liste (centre, rôle, date de début, date de fin) | O | Au moins une affectation active ; national = tous centres, sur décision traçée |
| Statut | Actif, Suspendu, Désactivé | S |  |
| Double authentification | Oui, Non | C | Obligatoire pour Admin. national et Direction Générale si disponible, et pour le Comptable de centre ; recommandée pour le Resp. adjoint de centre (SEC-11) |

### 3.4 Règles de gestion

1. **RG-ADM-01** Un centre est créé par l'administrateur national ; son code est unique et ne change plus après la première donnée saisie (ADM-01).
2. **RG-ADM-02** Un centre ne peut être désactivé que s'il n'a aucune session « Ouverte » ou « En cours » ; ses données restent consultables en lecture.
3. **RG-ADM-03** Une valeur de référentiel utilisée ne peut être supprimée, seulement désactivée ; elle reste affichée sur les objets existants et disparaît des listes de saisie (ADM-02, ADM-04).
4. **RG-ADM-04** Une période clôturée fige les données de reporting de cette période ; toute correction ultérieure exige une réouverture par la Direction Générale, tracée et motivée (ADM-03).
5. **RG-ADM-05** Un compte est nominatif ; un même identifiant ne peut être réattribué à une autre personne (USR-01).
6. **RG-ADM-06** Une affectation porte un rôle sur un centre ; un utilisateur peut cumuler plusieurs affectations. L'accès national (tous centres) exige une affectation explicite « National », accordée par l'admin. sur demande de la Direction Générale (USR-02, USR-03).
7. **RG-ADM-07** La désactivation d'un compte coupe immédiatement ses sessions ouvertes et conserve tout son historique (USR-06, SEC-06).
8. **RG-ADM-08** Un compte sans connexion depuis 90 jours passe en « Suspendu » ; le responsable de centre est notifié. Le délai est paramétrable (USR-06).
9. **RG-ADM-09** Cinq échecs de connexion consécutifs bloquent le compte 15 minutes ; dix échecs dans l'heure le suspendent jusqu'à déblocage par l'admin. Les seuils sont paramétrables (SEC-08).
10. **RG-ADM-10** La réinitialisation d'un mot de passe envoie un lien à usage unique valable 30 minutes ; à défaut de courriel, l'admin. génère un mot de passe temporaire à changer à la première connexion (USR-05).
11. **RG-ADM-11** Mot de passe : 10 caractères minimum, refus des mots de passe courants, pas d'expiration périodique forcée sauf compromission (SEC-08).
12. **RG-ADM-12** Tout ajout, retrait ou modification d'affectation est journalisé avec l'auteur et le motif (USR-07).
13. **RG-ADM-13** Un intérim du responsable de centre est déclaré par le RC ou l'admin. national au profit d'un utilisateur ayant une affectation RA active sur le même centre ; date de début, date de fin et motif sont obligatoires, et un centre n'a qu'un intérim actif à la fois (USR-09).
14. **RG-ADM-14** Pendant l'intérim, et seulement entre ses dates, le RA exerce les droits de validation du RC sur ce centre ; hors intérim, toute validation réservée au RC lui est refusée. Seule exception : le RA valide en propre les inventaires et ajustements de stock de la boutique (RG-BOU-07).
15. **RG-ADM-15** L'intérim prend fin automatiquement à sa date de fin ; le RC ou l'admin. peut l'interrompre plus tôt avec motif. Déclaration, interruption et fin sont journalisées et notifiées au RC et au RA.
16. **RG-ADM-16** Intérim ou non, un RA ne valide jamais une opération qu'il a lui-même saisie (séparation des tâches) ; chaque validation faite en intérim porte la mention « Intérim » dans le journal.
17. **RG-ADM-17 Socle et modules optionnels.** Le socle (administration, utilisateurs, bénéficiaires, formations, documents, tableaux de bord et rapports, journal) est toujours actif. Les modules optionnels s'activent ou se désactivent par centre : boutique et salle d'exposition, salle d'exposition seule (à l'intérieur du module boutique), scolarité et paiements, volet RSE du centre, puis les modules à venir (crèche, insertion, entrepreneuriat, matériels et équipements), qui arrivent désactivés (ADM-08).
18. **RG-ADM-18 Décision et trace.** Activation et désactivation sont saisies par l'admin. national avec la référence et la date de la décision de la Direction Générale, une date d'effet et un motif, puis validées par la DG ; elles sont journalisées et notifiées au RC. Au pilote, tous les modules optionnels sont activés au CAEF Cameroun.
19. **RG-ADM-19 Effets d'une désactivation.** La désactivation est refusée tant que le module a des opérations en cours : caisse non validée, inventaire non validé, reversement préparé non payé, paiement en attente de confirmation ou à affecter, article encore exposé (salle d'exposition seule). Une fois effective : menus masqués pour tous les rôles ; appels d'API et opérations de synchronisation refusés avec le motif « Module non activé » et journalisés ; données conservées en lecture seule pour la DG, le RC, le RA, le CPT et le SE ; affectations au rôle propre au module (VB) suspendues ; données locales du module effacées des appareils à la synchronisation suivante.
20. **RG-ADM-20 Chiffres d'un module désactivé.** Pour ce centre, les indicateurs et les lignes de clôture mensuelle du module s'affichent « Module non activé », jamais 0, et les totaux nationaux indiquent le nombre de centres où le module est actif (TDB-09, RG-GEN-05). La réactivation rétablit droits et affichage sans reprise de données ; la période désactivée reste « Module non activé ».

**Critères d'acceptation de l'activation des modules.**

- **CA-ADM-01** Après désactivation de la boutique au Centre de test B, le menu Boutique disparaît pour tous les rôles de ce centre ; un appel direct à l'API de vente et une vente synchronisée depuis une tablette sont refusés avec le motif « Module non activé » ; le compte VB du centre est suspendu.
- **CA-ADM-02** Sur le tableau de bord national, le chiffre d'affaires boutique du Centre de test B s'affiche « Module non activé », pas 0 ; l'historique des ventes reste lisible par le RC et le CPT.
- **CA-ADM-03** La désactivation de la boutique est refusée tant qu'une caisse du jour n'est pas validée, et celle de la seule salle d'exposition tant qu'un article y est exposé.

## 4. Bénéficiaires

Une bénéficiaire a un seul dossier dans tout le réseau, retrouvé avant toute création ; ses candidatures, inscriptions et attestations s'y rattachent (BEN-01 à BEN-13).

### 4.1 Écrans

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-BEN-01 Liste des bénéficiaires | Code, nom, prénom, âge, localité, centre, statut du dossier, dernière formation ; filtres statut, formation, période, complétude | Agent administratif |
| E-BEN-02 Nouvelle candidature | Étape 1 recherche obligatoire ; étape 2 identité ; étape 3 candidature ; étape 4 pièces | Agent administratif |
| E-BEN-03 Fiche bénéficiaire | Onglets Identité, Candidatures, Parcours, Pièces, Historique | Agent administratif |
| E-BEN-04 Parcours | Frise chronologique : candidatures, inscriptions, statuts de participation, attestations | Resp. centre |
| E-BEN-05 Doublons potentiels | Paires suspectes, score, champs concordants, actions Ce n'est pas un doublon ou Fusionner | Resp. centre |
| E-BEN-06 Transfert | Centre d'origine, centre d'accueil, motif, validation | Resp. centre d'accueil |
| E-BEN-07 Import | Dépôt du fichier, correspondance des colonnes, rapport d'anomalies, validation | Admin. national avec Suivi-évaluation |

### 4.2 Champs du dossier

La liste minimale des champs reste à valider par la Direction (PRD H4 ; CDC M03) ; la proposition ci-dessous ne collecte aucune donnée sensible par défaut.

| Champ | O/F | Contrôle ou règle |
| --- | --- | --- |
| Code bénéficiaire | S | Format BEN-\<centre de première inscription>-\<année>-\<numéro> ; immuable, même après transfert |
| Nom, prénom(s) | O | Lettres, espaces, tirets, apostrophes |
| Autres noms d'usage | F | Aide à la détection des doublons |
| Date de naissance | C | Obligatoire si le programme a une condition d'âge ; sinon année de naissance ou tranche d'âge |
| Sexe | O | Valeur par défaut F, modifiable (le réseau accueille femmes et filles) |
| Téléphone | F | Format +224 ; plusieurs dossiers peuvent partager un numéro |
| Localité de résidence | O | Référentiel territorial jusqu'à la commune ou le quartier |
| Niveau d'études | F | Référentiel |
| Situation à l'entrée | F | Référentiel (sans activité, activité informelle, salariée, élève, autre) ; sert de référence pour l'insertion future |
| Contact d'urgence | C | Seulement si le programme le justifie (CDC M03) |
| Pièce d'identité (type, numéro) | C | Seulement si le programme l'exige ; accès restreint |
| Centre de rattachement | S | Centre de l'utilisateur ; modifié seulement par transfert |
| Consentement au traitement | O | Date et mode (écrit, oral devant témoin) ; mentions d'information présentées |
| Autorisation d'image | F | Non par défaut ; nécessaire à toute publication |
| Statut du dossier | S | Voir 4.4 |
| Complétude | S | Pourcentage des champs requis par les programmes suivis |

### 4.3 Candidature : statuts et transitions

| De | Vers | Action et rôle | Condition |
| --- | --- | --- | --- |
| (aucun) | Brouillon | Créer, Agent | Recherche de doublon effectuée |
| Brouillon | Soumise | Soumettre, Agent | Champs obligatoires remplis |
| Soumise | Incomplète | Demander un complément, Agent ou Resp. centre | Motif sélectionné |
| Incomplète | Soumise | Compléter, Agent | Pièces ajoutées |
| Soumise | Validée | Valider, Resp. centre | Complétude 100 % des champs requis par la formation |
| Soumise | Rejetée | Rejeter, Resp. centre | Motif obligatoire (référentiel + commentaire) |
| Validée | En liste d'attente | Placer en attente, Resp. pédagogique | Session cible complète ou non programmée |
| Validée ou En liste d'attente | Inscrite | Inscrire à une session, Resp. pédagogique | Voir RG-FOR-05 |
| Toute sauf Inscrite | Annulée | Annuler, Agent | Motif obligatoire (désistement, erreur) |

### 4.4 Statuts du dossier

- **Actif** : au moins une candidature ou inscription non clôturée.
- **Inactif** : aucune activité depuis 12 mois (calculé, paramétrable).
- **Clôturé** : parcours terminé, motif de clôture du référentiel (BEN-13).
- **Archivé** : archivage logique selon la politique de conservation ; lecture limitée au Suivi-évaluation et à l'admin.
- **Fusionné** : dossier absorbé par un autre ; redirige vers le dossier conservé.

### 4.5 Détection des doublons

1. **RG-BEN-01** À l'étape 1 de E-BEN-02, l'agent saisit nom, prénom et date ou année de naissance ; le système cherche dans tout le réseau, en affichant pour les autres centres seulement le code, le nom, l'année de naissance et le centre (BEN-05, USR-04).
2. **RG-BEN-02** Comparaison sur les noms normalisés (sans accents, casse, espaces doubles, inversion nom et prénom) et une similarité phonétique adaptée au français. Score : nom et prénom concordants 50 points, date de naissance identique 30, localité identique 10, téléphone identique 10. Le téléphone ne suffit jamais seul (DAT-01).
3. **RG-BEN-03** Score de 60 ou plus : alerte bloquante, l'agent doit ouvrir le dossier existant ou déclarer « personne différente » avec un commentaire. Score de 40 à 59 : alerte informative. Les seuils sont paramétrables et seront calibrés sur les données importées du pilote.
4. **RG-BEN-04** Une analyse nocturne recalcule les paires suspectes et alimente E-BEN-05.
5. **RG-BEN-05** La fusion est faite par le responsable de centre (ou le Suivi-évaluation si deux centres sont concernés), jamais automatiquement : il choisit le dossier conservé et, champ par champ, la valeur retenue ; toutes les candidatures et inscriptions sont rattachées au dossier conservé ; l'opération est journalisée et réversible pendant 30 jours (BEN-09).

### 4.6 Transfert et import

1. **RG-BEN-06** Le transfert vers un autre centre est demandé par le centre d'accueil et validé par le centre d'origine ; le code et l'historique ne changent pas ; le centre d'origine garde une lecture de l'historique antérieur au transfert (BEN-10).
2. **RG-BEN-07** L'import se fait d'abord dans l'environnement de préproduction sur un échantillon ; le rapport liste lignes acceptées, rejetées (avec motif), doublons suspects et champs « à vérifier » (BEN-08, MIG-01).
3. **RG-BEN-08** Une valeur absente ou incohérente dans la source n'est jamais devinée : elle est importée « non renseignée » ou « à vérifier » (MIG-01). Au pilote, la source est un ensemble de registres papier (livrets, feuilles volantes) saisis ou numérisés ; deux registres divergents donnent le statut « à vérifier », avec les deux valeurs et leurs références (SRC-03, section 9.8).
4. **RG-BEN-09** L'import final en production exige la validation écrite du responsable métier sur le rapport d'échantillon ; chaque dossier importé garde la référence de sa ligne source.

## 5. Formations, sessions, inscriptions et présences

Une formation est une offre du catalogue ; une session en est une occurrence datée dans un centre ; une inscription relie une bénéficiaire validée à une session, et les présences se saisissent par séance (FOR-01 à FOR-16).

### 5.1 Écrans

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-FOR-01 Catalogue | Formations : code, intitulé, catégorie, durée, statut ; national ou propre à un centre | Resp. pédagogique |
| E-FOR-02 Fiche formation | Objectifs, prérequis, contenu par module, durée en heures, conditions d'achèvement et d'attestation | Resp. pédagogique |
| E-FOR-03 Liste des sessions | Code, formation, centre, dates, formateur, places occupées sur capacité, statut | Resp. pédagogique |
| E-FOR-04 Fiche session | Planning des séances, formateurs, inscrites, présences, résultats, rapport de clôture | Resp. pédagogique |
| E-FOR-05 Formateurs | Fiche : identité, compétences, domaines, statut (interne, externe), sessions animées, documents contractuels | Resp. pédagogique |
| E-FOR-06 Mes sessions | Vue formateur : sessions affectées, prochaine séance, lien direct vers la feuille de présence | Formateur |
| E-FOR-07 Feuille de présence | Une ligne par inscrite : Présente, Absente, Retard, Absence justifiée ; bouton « Toutes présentes » ; mention de la cheffe de classe ; validation | Formateur |
| E-FOR-08 Résultats | Par inscrite : évaluations, note ou appréciation, décision d'achèvement, attestation | Resp. pédagogique |

### 5.2 Champs clés

| Objet | Champs | Contrôles |
| --- | --- | --- |
| Formation | Code (S), intitulé (O), catégorie (O, référentiel), objectifs (O), prérequis (F), durée en heures (O), seuil de présence pour achèvement en % (O, défaut 80), évaluation requise (O, oui ou non), attestation prévue (O) | Intitulé unique par catégorie |
| Session | Code (S), formation (O), centre (O), période ou campagne (O), dates de début et fin (O), lieu (O), capacité (O), formateur principal (O), formateurs associés (F), programme financeur (F) | Fin après début ; capacité supérieure à 0 (FOR-13) |
| Séance | Date (O), heure de début et fin (O), thème (F) | Dans les dates de la session |
| Inscription | Bénéficiaire (O), session (O), date (S), statut de participation (S), motif de sortie (C), cheffe de classe (F : une seule par session, désignée par le formateur ou le responsable pédagogique) | Voir RG-FOR-05 |
| Présence | Séance (O), inscription (O), état (O), justificatif (F), saisie par (S) | Une seule présence par séance et inscription |

### 5.3 Session : statuts et transitions

| De | Vers | Action et rôle | Condition |
| --- | --- | --- | --- |
| (aucun) | Brouillon | Créer, Resp. pédagogique |  |
| Brouillon | Ouverte | Ouvrir les inscriptions, Resp. pédagogique | Tous les champs obligatoires remplis, au moins une séance planifiée (FOR-13) |
| Ouverte | En cours | Automatique à la première séance passée | Au moins une inscrite |
| En cours | Clôturée | Clôturer, Resp. pédagogique | Toutes les présences saisies et chaque inscrite a un statut final (FOR-10) |
| Brouillon, Ouverte | Annulée | Annuler, Resp. centre | Motif ; les inscrites repassent « Validée » ou en liste d'attente |
| Clôturée | En cours | Rouvrir, Resp. centre | Droit spécifique, motif obligatoire, journalisé (FOR-14) |

### 5.4 Participation : statuts

| Statut | Définition |
| --- | --- |
| Inscrite | Inscription enregistrée, aucune séance encore suivie |
| Commencée | Au moins une présence enregistrée (automatique) |
| Suspendue | Interruption décidée avec motif, reprise possible dans la même session |
| Abandonnée | Sortie sans achèvement, motif obligatoire (référentiel) |
| Achevée | Seuil de présence atteint et, si requise, évaluation saisie |
| Non achevée | Session clôturée sans atteinte des conditions d'achèvement |

L'attestation est un attribut distinct : « Délivrée » uniquement si la participation est « Achevée » et que les conditions de la formation sont remplies (FOR-07, FOR-09).

### 5.5 Règles de gestion

1. **RG-FOR-01** Une session appartient à une formation, un centre et une période (DM M4).
2. **RG-FOR-02** Un formateur ne peut être affecté à deux séances qui se chevauchent ; le système bloque l'affectation.
3. **RG-FOR-03** La capacité ne peut être dépassée ; au-delà, l'inscription propose la liste d'attente. Le responsable de centre peut déroger de 10 % au plus avec motif (FOR-04).
4. **RG-FOR-04** Le formateur ne voit que les inscrites de ses sessions et seulement nom, prénom et code (USR-04).
5. **RG-FOR-05** Une inscription exige une candidature « Validée » ou « En liste d'attente », une session « Ouverte » ou « En cours », une place disponible, et aucune autre inscription active de la même personne sur des séances simultanées.
6. **RG-FOR-06** Les présences d'une séance sont saisissables du jour de la séance jusqu'à 7 jours après ; au-delà, seul le responsable pédagogique peut les saisir, avec motif (FOR-06).
7. **RG-FOR-07** Trois absences non justifiées consécutives déclenchent une alerte au responsable pédagogique, qui confirme ou non l'abandon ; le passage à « Abandonnée » n'est jamais automatique.
8. **RG-FOR-08** Taux de présence = séances « Présente » ou « Retard » divisées par séances passées depuis l'inscription ; une absence justifiée est exclue du dénominateur si la formation le prévoit.
9. **RG-FOR-09** À la clôture, le système propose « Achevée » ou « Non achevée » selon le seuil ; le responsable pédagogique confirme, toute dérogation étant motivée et journalisée (FOR-08).
10. **RG-FOR-10** Une note ou un résultat modifié après saisie conserve l'ancienne valeur dans l'historique (FOR-08).
11. **RG-FOR-11** Le rapport de clôture est généré automatiquement : inscrites, commencées, achevées, abandons par motif, attestations, taux de présence moyen, commentaire du responsable (FOR-10).
12. **RG-FOR-12** Listes de présence et résultats sont exportables en tableur par les rôles autorisés, l'export étant journalisé (FOR-15).

## 6. Partenaires, opportunités et pipeline RSE

Un partenaire est une organisation unique dans le réseau ; chaque démarche auprès de lui est une opportunité qui avance dans le pipeline RSE en 15 étapes, chaque passage étant daté et signé (PAR-01 à PAR-09, CNV-10).

### 6.1 Écrans

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-PAR-01 Répertoire des partenaires | Code, raison sociale, catégorie, secteur, responsable de suivi, opportunités ouvertes, conventions actives | Resp. RSE |
| E-PAR-02 Fiche partenaire | Onglets Identité, Interlocuteurs, Interactions, Opportunités, Conventions, Contributions, Historique | Resp. RSE |
| E-PAR-03 Pipeline | Vue en colonnes par étape (glisser une carte = changer d'étape, avec confirmation) et vue liste ; filtres responsable, centre, montant, étape | Resp. RSE |
| E-PAR-04 Fiche opportunité | Origine, besoin ou projet visé, montant estimé, étape, prochaine action datée, contributeurs internes, propositions liées | Resp. RSE |
| E-PAR-05 Interaction | Type (appel, courriel, rendez-vous, visite), date, participants, compte rendu, prochaine action | Resp. RSE |
| E-PAR-06 Besoins des centres | Fiches projet issues des centres : besoin, bénéficiaires visés, objectif d'impact, budget indicatif, statut | Resp. centre |

### 6.2 Champs clés

| Objet | Champs | Contrôles |
| --- | --- | --- |
| Partenaire | Code (S), raison sociale (O), sigle (F), catégorie (O : entreprise, fondation, institution, ONG, organisme international, autre), secteur (O), adresse et coordonnées institutionnelles (F), site web (F), responsable de suivi (O) | Contrôle de doublon sur raison sociale normalisée et sigle (PAR-03) |
| Interlocuteur | Nom (O), fonction (O), téléphone et courriel professionnels (F), interlocuteur principal (O) | Aucune donnée personnelle non professionnelle (PAR-02) |
| Opportunité | Code (S), partenaire (O), intitulé (O), origine du contact (O : prospection, recommandation, sollicitation entrante, événement, autre), apporteur (C), centres concernés (O), fiche projet liée (F), montant estimé en GNF (F), nature envisagée (F), potentiel (F : faible, moyen, fort), étape (S), prochaine action et date (O tant que non close) | Prochaine action dans le futur |
| Fiche projet RSE | Centre (O), besoin (O), bénéficiaires visés (O), objectif d'impact et indicateurs (O), budget indicatif (F), statut (Brouillon, Qualifiée, Rattachée, Abandonnée) | Qualification par le Resp. RSE |

### 6.3 Étapes du pipeline

Les 15 étapes sont celles du DM § 7.1, regroupées en cinq phases pour la lecture ; elles restent paramétrables par la Direction Générale (PAR-06).

| Phase | Étapes | Objet qui porte l'étape |
| --- | --- | --- |
| Prospection | 1 Prospect identifié ; 2 Prospect qualifié ; 3 Premier contact réalisé ; 4 Rendez-vous planifié | Opportunité |
| Construction | 5 Diagnostic des besoins réalisé ; 6 Proposition en préparation ; 7 Proposition soumise ; 8 Négociation en cours | Opportunité puis proposition |
| Engagement | 9 Partenariat approuvé ; 10 Convention signée | Convention |
| Exécution | 11 Engagement en cours d'exécution ; 12 Contribution encaissée ou reçue ; 13 Programme exécuté | Convention, engagements, contributions |
| Clôture | 14 Rapport d'impact transmis ; 15 Partenariat renouvelé ou clôturé | Convention |

Une opportunité peut à tout moment être close « Perdue » ou « Suspendue », avec un motif du référentiel.

### 6.4 Règles de gestion

1. **RG-PAR-01** À la création d'un partenaire, le système affiche les partenaires de nom ou sigle proche ; l'utilisateur confirme qu'il s'agit d'une nouvelle organisation (PAR-03).
2. **RG-PAR-02** Les étapes 1 à 8 avancent par action du responsable RSE ; une étape peut être sautée vers l'avant avec commentaire, le retour en arrière exige un motif. Les étapes 9 à 15 sont dérivées des statuts de la proposition, de la convention et des contributions et ne se modifient pas à la main (PAR-06).
3. **RG-PAR-03** Chaque changement d'étape enregistre date, auteur, étape précédente et commentaire ; la durée passée dans chaque étape est calculée pour le tableau de bord RSE.
4. **RG-PAR-04** Une opportunité sans prochaine action ou dont la prochaine action est dépassée de 7 jours apparaît en alerte chez son responsable (NOT-01).
5. **RG-PAR-05** Plusieurs contributeurs internes peuvent être déclarés sur une opportunité, avec leur rôle (apporteur, négociateur, appui technique) ; aucun calcul de commission n'est fait (PAR-08, DM § 7.9).
6. **RG-PAR-06** Une fiche projet « Qualifiée » peut être rattachée à une ou plusieurs opportunités ; elle passe alors « Rattachée » (CNV-10, écart A8).
7. **RG-PAR-07** Un responsable de centre voit les partenaires et opportunités qui concernent son centre ; le responsable RSE et la Direction Générale voient tout le réseau.

## 7. Propositions, conventions, engagements et contributions

Le système tient quatre objets distincts, chacun avec ses statuts et sa preuve, pour qu'aucun montant promis ne soit compté comme signé, reçu ou exécuté (CNV-01 à CNV-08, CTR-01 à CTR-07, CTR-09).

&#91;embedded content: chaîne RSE · 4 objets, leurs statuts et leurs preuves\]

Une proposition acceptée ne vaut pas convention, une convention signée ne vaut pas encaissement, un encaissement ne vaut pas exécution (DM § 9.3) ; les tableaux de bord additionnent chaque statut séparément.

### 7.1 Écrans

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-CNV-01 Fiche proposition | Version, partenaire, centres et programme bénéficiaires, montant sollicité, nature, budget prévisionnel, résultats attendus, calendrier, circuit de validation, dates d'envoi et de réponse | Resp. RSE |
| E-CNV-02 Fiche convention | Référence, partenaire, proposition d'origine, programme, dates de début et fin, montant accordé, signataires, document signé, engagements, contributions, échéances | Resp. RSE |
| E-CNV-03 Engagements | Tableau : partie (partenaire ou CAEF), description, responsable, échéance, état, justificatif, validation | Resp. RSE, Resp. centre |
| E-CNV-04 Fiche contribution | Nature, partenaire, convention, programme, centre bénéficiaire, valeur, devise, méthode de valorisation, date, justificatifs, statut, rapprochement comptable (référence de pièce comptable, date d'encaissement constatée, rapproché par, renseignés par le comptable du centre) | Resp. RSE |
| E-CNV-05 Programmes | Fiche minimale : code, intitulé, centres, responsable, période, statut (CNV-06) | Direction Générale |
| E-CNV-06 Mes validations | File des propositions et contributions en attente de ma validation | Valideurs |

### 7.2 Proposition

1. **RG-CNV-01** Une proposition naît d'une opportunité et porte un numéro de version ; toute modification après soumission crée une nouvelle version, les précédentes restant consultables (CNV-01).
2. **RG-CNV-02** Circuit par défaut (H5, paramétrable) : le responsable RSE prépare, le responsable du centre bénéficiaire donne un avis, la Direction Générale valide. Au-dessus d'un seuil de montant fixé par la Direction, une seconde validation peut être exigée (CNV-02).
3. **RG-CNV-03** Seule une proposition « Validée » peut être marquée « Soumise » ; la date d'envoi est alors obligatoire.
4. **RG-CNV-04** Un refus, un rejet interne ou une suspension exige un motif du référentiel et un commentaire (CNV-03).

### 7.3 Convention et engagements

1. **RG-CNV-05** Une convention ne passe « Signée » qu'avec la date de signature, les signataires et le document signé déposé (CNV-04).
2. **RG-CNV-06** Le montant accordé de la convention peut différer du montant sollicité ; les deux sont conservés.
3. **RG-CNV-07** Un engagement passe « En retard » automatiquement le lendemain de son échéance s'il n'est pas « Réalisé » ; il apparaît en alerte chez son responsable et au tableau de bord RSE (CNV-05, CNV-07).
4. **RG-CNV-08** Un engagement « Réalisé » doit porter un justificatif ; il devient « Validé » après contrôle du responsable RSE.
5. **RG-CNV-09** Rappels automatiques 30 et 7 jours avant chaque échéance et 60 jours avant la fin de la convention (CNV-07).
6. **RG-CNV-10** Une convention ne peut être « Clôturée » que si tous ses engagements sont « Validé » ou explicitement abandonnés avec motif ; elle reste consultable selon les droits (CNV-08).

### 7.4 Contribution

1. **RG-CTR-01** Natures : contribution financière, don en nature, mise à disposition d'équipements, prestation de service, formation financée, mise à disposition de compétences, appui logistique, autre contribution validée (CTR-01).
2. **RG-CTR-02** À la signature, chaque versement ou apport prévu est créé « Promise » avec sa date prévue ; il ne compte jamais dans les montants reçus (CTR-03).
3. **RG-CTR-03** Passage à « Reçue » : date de réception, montant ou quantité effectivement reçus (éventuellement différents du promis) et justificatif (relevé, reçu, bon de livraison, procès-verbal) obligatoires (CTR-05).
4. **RG-CTR-04** Passage à « Validée » par un responsable habilité autre que la personne qui a saisi la réception (séparation des tâches) (CTR-06).
5. **RG-CTR-05** Une contribution non financière porte une valeur estimée facultative, une méthode de valorisation obligatoire si une valeur est saisie (facture, devis, prix de marché, déclaration du partenaire) et n'est jamais additionnée aux montants financiers (CTR-04, CTR-07).
6. **RG-CTR-06** Devise : GNF par défaut ; une contribution en devise étrangère conserve le montant d'origine et le taux de conversion appliqué à la date de réception, avec sa source.
7. **RG-CTR-07** Le rapprochement comptable reste hors de l'outil ; le champ « référence comptable » permet seulement d'y renvoyer (H6) ; c'est le comptable du centre qui renseigne ce renvoi (RG-CTR-08).
8. **RG-CTR-08** Pour une contribution financière « Reçue » ou « Validée » de son centre, le comptable du centre (CPT) peut renseigner la référence de pièce comptable et la date d'encaissement constatée ; le système enregistre l'auteur du rapprochement et sa date (CTR-09).
9. **RG-CTR-09** Le rapprochement ne change pas le statut de la contribution et ne vaut pas validation : le CPT n'a aucun droit de validation, qui reste à la Direction Générale (RG-CTR-04). Une modification du rapprochement est journalisée avec la valeur avant et après.
10. **RG-CTR-10** Le CPT consulte les contributions de son centre mais ne voit ni ne modifie les autres champs ; les contributions non financières ne se rapprochent pas. Une contribution « Validée » non rapprochée apparaît dans le volet contributions du tableau de bord de centre.

## 8. Tableaux de bord, rapports, exports, notifications et journal

Chaque tableau de bord n'affiche que des indicateurs définis dans le Référentiel des indicateurs, avec leur date de mise à jour, leur niveau de fiabilité et un lien vers la liste des données qui les composent (TDB-01 à TDB-09).

### 8.1 Tableaux de bord

| Écran | Indicateurs (codes du Référentiel) | Filtres | Destinataire |
| --- | --- | --- | --- |
| E-TDB-01 National | IND-01 à IND-12 et IND-20 à IND-24 ayant une fiche validée ; comparaison par centre | Période, centre, catégorie de formation | Direction Générale |
| E-TDB-02 Centre | Indicateurs formation et bénéficiaires du centre ; alertes ; rapports à transmettre ; volet boutique (E-BOU-08), volet contributions financières et statut de la dernière clôture mensuelle avec IND-50 (SRC-04), visibles aussi du RA et du CPT | Période, formation, session | Resp. centre |
| E-TDB-03 Pédagogique | Sessions en cours, séances sans présences saisies, inscrites en alerte d'abandon, taux de présence | Période, formation, formateur | Resp. pédagogique |
| E-TDB-04 RSE | Pipeline par étape, taux de transformation, montants sollicités, accordés, promis, reçus, valeur en nature, engagements en retard, conventions à renouveler | Période, partenaire, centre, programme | Resp. RSE, Direction Générale |
| E-TDB-05 Qualité des données | Complétude des dossiers, doublons suspects, présences manquantes, contributions reçues sans justificatif | Période, centre | Suivi-évaluation |

1. **RG-TDB-01** Les indicateurs sont recalculés chaque nuit dans des tables de synthèse, pour ne pas ralentir la saisie ; l'heure du dernier calcul est affichée. Un bouton « Actualiser » est réservé au Suivi-évaluation (PERF-02).
2. **RG-TDB-02** Un clic sur une valeur ouvre la liste des objets comptés, filtrée selon les droits de l'utilisateur ; la Direction Générale voit des agrégats sans noms sauf habilitation nominative (TDB-01, TDB-02).
3. **RG-TDB-03** Toute valeur affiche à côté le nombre de « non renseignés » pris en compte ; un indicateur dont plus de 20 % des données manquent est signalé « fiabilité faible » (TDB-09).
4. **RG-TDB-04** Une période clôturée affiche les valeurs figées à la clôture, pas un recalcul (RG-ADM-04).

### 8.2 Rapports

| Rapport | Contenu | Production |
| --- | --- | --- |
| R-01 Rapport de session | Voir RG-FOR-11 | Automatique à la clôture |
| R-02 Rapport périodique de centre | Période, activités, bénéficiaires, formations, résultats, partenariats du centre, difficultés, commentaire | Mensuel ou trimestriel, préparé par le Resp. centre, validé puis transmis (REP-02) |
| R-03 Rapport national | Structure DM § 14.2 limitée aux indicateurs validés ; contrôles doublons et manquants ; version validée archivée | Suivi-évaluation, validé par la Direction (REP-03) |
| R-04 Rapport partenaire | Convention, contributions promises, reçues et validées, engagements, bénéficiaires soutenus en agrégé uniquement, preuves | Resp. RSE (REP-04, REP-06) |

Chaque rapport indique sa période, sa date de production, son auteur, son statut (Brouillon, Validé, Transmis) et le niveau de fiabilité de ses chiffres ; il est généré en PDF et en tableur.

### 8.3 Exports

1. **RG-EXP-01** Un export applique exactement les filtres et les droits de l'écran d'origine (SEC-10).
2. **RG-EXP-02** Les exports contenant des données nominatives sont réservés aux rôles autorisés, demandent un motif et sont journalisés avec le nombre de lignes (REP-01).
3. **RG-EXP-03** Le fichier exporté porte la date, l'auteur et la mention « Document confidentiel » s'il contient des données personnelles.

### 8.4 Notifications

| Événement | Destinataire | Délai |
| --- | --- | --- |
| Candidature soumise ou complétée | Resp. centre | Immédiat |
| Validation demandée (proposition, contribution, fusion, transfert) | Valideur | Immédiat |
| Séance passée sans présences saisies | Formateur, puis Resp. pédagogique à J+2 | J+1 |
| Trois absences consécutives | Resp. pédagogique | Immédiat |
| Échéance d'engagement | Responsable de l'engagement | J-30, J-7, J+1 |
| Fin de convention | Resp. RSE | J-60 |
| Rapport périodique à produire | Resp. centre | 5 jours avant la date limite |
| Compte suspendu | Utilisateur, Resp. centre | Immédiat |
| Intérim du responsable de centre déclaré, interrompu ou terminé | Resp. centre, RA | Immédiat |
| Caisse comptée à valider ; reversement préparé à valider | CPT (caisse) ; Resp. centre, RA (reversement) | Immédiat |
| Stock négatif ou sous le seuil d'alerte | Resp. centre, RA | Immédiat |
| Clôture mensuelle à vérifier ; clôture vérifiée à valider ; mois non validé le 10 du mois suivant | CPT ; Resp. centre (RA en intérim) ; CPT et Resp. centre | Le 1er du mois ; immédiat ; le 11 |

Au MVP, les notifications sont affichées dans l'application (cloche et page « Mes alertes »). Le courriel et le SMS sont prévus comme canaux activables plus tard, après validation de leur coût (NOT-01, écart A5).

### 8.5 Journal d'activité

L'écran E-ADM-08 liste les événements journalisés : date et heure, utilisateur, adresse IP, centre, objet, action, avant et après. Il est filtrable et exportable par l'admin. national et en lecture pour la Direction Générale et le Suivi-évaluation ; un responsable de centre voit le journal de son centre. Le journal n'est modifiable par personne, y compris l'admin. (SEC-04).

## 9. Boutique et salle d'exposition

Le module boutique enregistre ce que le centre produit et vend dans sa boutique, suit le stock, la caisse du jour et la part qui revient aux productrices en dépôt-vente (BOU-01 à BOU-11). Il rend mesurables les revenus générés par les bénéficiaires. Demandé par le porteur de projet, il n'est ni dans le DM ni dans le CDC ; il fait partie du lot 1 livré au pilote (H14 tranchée). La section 9.8 ajoute la source unique et la clôture mensuelle du centre, qui couvrent aussi les contributions financières reçues.

Hors périmètre du module : paiement électronique autre que le Mobile Money (A6, PAY-13), comptabilité générale, coût de revient et marge, vente en ligne, gestion avancée des achats et fournisseurs, terminal de caisse dédié, lecteur de codes-barres et plusieurs points de vente par centre (P2). Le modèle prévoit l'entité point de vente dès le départ, un par centre au MVP.

### 9.1 Objectifs et exigences couvertes

| Objectif | Exigences PRD | Écrans |
| --- | --- | --- |
| Tenir le catalogue et des prix historisés | BOU-01, BOU-11 | E-BOU-01, E-BOU-02 |
| Enregistrer les entrées en stock et les dépôts-ventes | BOU-02, BOU-04 | E-BOU-03 |
| Vendre, encaisser et remettre un reçu numéroté | BOU-03, BOU-06 | E-BOU-04 |
| Clôturer la caisse chaque jour | BOU-05 | E-BOU-05 |
| Contrôler le stock par inventaire | BOU-04, BOU-07 | E-BOU-06 |
| Reverser aux productrices leur part | BOU-08 | E-BOU-07 |
| Piloter la boutique et exporter ses journaux | BOU-09, BOU-10 | E-BOU-08 |

Le noyau boutique est BOU-01 à BOU-06 (vendre, encaisser, tracer).

### 9.2 Rôles du module

| Action | Saisie ou préparation | Validation | Jamais par |
| --- | --- | --- | --- |
| Catalogue et prix | Resp. centre, RA | Aucune (journalisée) |  |
| Entrée en stock, sortie motivée | VB, Resp. centre, RA | Aucune (journalisée) |  |
| Vente | VB (ou Resp. centre, RA, agent admin. par cumul du rôle VB) | Aucune |  |
| Annulation de vente | CPT, Resp. centre, RA | Contre-écriture motivée | Hors de ces rôles |
| Ouverture et comptage de caisse | VB | CPT ; à défaut Resp. centre ou RA | Auteur de ventes de la journée |
| Inventaire | VB ou agent admin. (comptage) | Resp. centre ou RA | Celui qui a compté |
| Reversement | CPT (préparation, paiement) | Resp. centre ou RA | Validation par le préparateur ; paiement par le valideur |
| Exports des journaux | CPT, Resp. centre, RA | Aucune (journalisée) |  |
| Transfert vers ou depuis la salle d'exposition | VB, Resp. centre, RA | Aucune (journalisée) |  |

Le VB voit seulement le nom et le code d'une productrice déposante sur l'article ; le CPT voit son identité minimale (nom, prénom, code, téléphone) pour les reversements ; ni l'un ni l'autre n'accède aux dossiers bénéficiaires.

### 9.3 Écrans

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-BOU-01 Catalogue produits | Code, nom, catégorie, unité, prix en vigueur, origine (atelier ou session de formation du centre, productrice en dépôt-vente, groupement, achat pour revente), stock courant, seuil d'alerte, statut actif ; filtres par origine, catégorie et rupture (BOU-01) | Resp. centre, RA |
| E-BOU-02 Fiche produit et prix | Identité du produit, productrice déposante ou groupement (nom et code), session ou formation d'origine, seuil d'alerte ; onglet Prix (historique daté : prix, début, fin, auteur) ; onglets Mouvements et Historique (BOU-01, BOU-11) | Resp. centre, RA |
| E-BOU-03 Entrées en stock et dépôt-vente | Entrée : produit, origine, quantité, date ; si dépôt-vente, productrice déposante et part du centre en % ; sorties motivées (perte, don, échantillon, usage interne) ; liste des dépôts par productrice (BOU-02, BOU-04) | VB |
| E-BOU-04 Vente et reçu | Écran optimisé téléphone : recherche produit, lignes (quantité, prix appliqué, remise et motif), total, règlements (espèces ; Mobile Money par demande de paiement ou déclaré avec son identifiant de transaction, section 12 ; virement ou chèque avec référence), validation ; reçu numéroté imprimable (A4, ticket 80 mm, PDF) ; option « Saisie différée » avec le numéro du reçu papier de secours (BOU-03, BOU-06) | VB |
| E-BOU-05 Caisse du jour et clôture | Session de caisse : ouverture et fond de caisse, ventes du jour, montant théorique par mode de règlement, montant compté, écart, motif, validation (BOU-05) | VB (comptage), CPT (validation) |
| E-BOU-06 Inventaire | Produits avec quantité théorique, quantité comptée, écart par ligne, motif, validation de l'ajustement (BOU-07) | VB ou agent admin. (comptage), Resp. centre ou RA (validation) |
| E-BOU-07 Reversements aux productrices | Par productrice et période : ventes de ses produits, part du centre, montant dû calculé, reversements antérieurs, solde restant dû ; préparation, validation, paiement (date, mode, pièce justificative) (BOU-08) | CPT, Resp. centre ou RA |
| E-BOU-08 Volet boutique du tableau de bord | Chiffre d'affaires par période, produit et catégorie ; nombre de ventes ; stock valorisé au prix de vente ; ruptures et stocks sous seuil ; écarts de caisse ; reversements dus ; exports des journaux des ventes, des clôtures et des reversements (BOU-09, BOU-10) | Resp. centre, RA, CPT |
| E-BOU-09 Salle d'exposition | Articles exposés : produit, quantité, date d'exposition ; transferts entre la boutique et la salle d'exposition ; vente depuis la salle d'exposition par E-BOU-04 ; écran visible seulement si la salle d'exposition est activée pour le centre (BOU-15, ADM-08) | VB, Resp. centre, RA |

L'écran de vente E-BOU-04 rejoint les parcours optimisés pour une main et un petit écran (2.4).

### 9.4 Champs clés

| Objet | Champs | Contrôles |
| --- | --- | --- |
| Produit | Point de vente (S), code (S), nom (O), catégorie (O), unité (O), origine (O), productrice déposante ou groupement (C : origine dépôt-vente ou groupement), session ou formation d'origine (F), seuil d'alerte (F), actif (S) | Une productrice déposante est une bénéficiaire existante ou un groupement |
| Prix | Prix (O), date de début (O), date de fin (S), auteur (S) | Entier en GNF supérieur à 0 ; un seul prix en vigueur à une date donnée |
| Entrée en stock et dépôt | Produit (O), type (O), quantité (O), date (O), emplacement (S : boutique par défaut ; C : salle d'exposition si elle est activée), part du centre en % (C : dépôt-vente), motif (C : sortie) | Quantité supérieure à 0 ; part comprise entre 0 et 100 % |
| Vente | Numéro de reçu (S : série de l'appareil et numéro), date et heure (S ; C en saisie différée), numéro du reçu papier (C : saisie différée), vendeur (S), total (S), statut (S) | Au moins une ligne ; somme des règlements égale au total ; aucune donnée sur l'acheteur |
| Ligne de vente | Produit (O), quantité (O), prix unitaire appliqué (S, prix en vigueur), remise (F), motif de remise (C : remise saisie) | Remise au plus égale au montant de la ligne |
| Règlement | Mode (O), montant (O), référence externe (C : Mobile Money déclaré, virement, chèque), statut (S : confirmé, déclaré, non retrouvé), transaction de la passerelle (S : Mobile Money) | Un règlement Mobile Money n'est confirmé que par l'opérateur (RG-PAY-03) ; déclaré, il reste « Déclaré » jusqu'au rapprochement |
| Session de caisse | Date (S), ouverte par (S), fond de caisse (O), montants théoriques par mode (S), montants comptés par mode (O), écart (S), motif (C : écart non nul), compté par (S), validé par (S), date de validation (S) | Une session par point de vente et par jour de vente |
| Inventaire | Date (S), compté par (S), validé par (S) ; par ligne : quantité théorique (S), quantité comptée (O), écart (S), motif (C : écart non nul) | Valideur différent du compteur |
| Reversement | Productrice (O), période (O), montant dû (S), montant reversé (O), date (C : payé), mode (C : payé), pièce justificative (C : payé), préparé par (S), validé par (S) | Montant reversé au plus égal au solde restant dû |

### 9.5 Règles de gestion

1. **RG-BOU-01 Numérotation continue.** Chaque reçu reçoit, à la validation de la vente, un numéro composé de la série de l'appareil et d'un numéro continu propre à cet appareil (ex. CMR-B-000127), attribué sur l'appareil, en ligne comme hors ligne ; il est unique par point de vente et sans trou dans chaque série (OFF-08) ; un numéro attribué à une vente dont l'enregistrement échoue est consigné comme annulé (BOU-03, BOU-06).
2. **RG-BOU-02 Annulation par contre-écriture.** Une vente validée ou un mouvement de stock n'est jamais modifié ni supprimé ; l'annulation crée une contre-écriture liée, motivée, datée du jour de l'annulation et tracée, qui remet les quantités en stock et neutralise les règlements. Le reçu d'origine reste consultable avec la mention « Annulée » (BOU-06, RG-GEN-03).
3. **RG-BOU-03 Stock calculé.** Le stock d'un produit est la somme de ses mouvements (entrées, ventes, sorties motivées, ajustements d'inventaire, annulations) ; ce n'est jamais un champ modifiable. Toute sortie (perte, don, échantillon, usage interne) exige un motif (BOU-04).
4. **RG-BOU-04 Alertes de stock.** Une vente qui rend le stock négatif est enregistrée avec une alerte et signale le produit au prochain inventaire ; un stock sous le seuil d'alerte apparaît au volet boutique du tableau de bord (BOU-04).
5. **RG-BOU-05 Clôture de caisse quotidienne.** Chaque jour de vente ouvre une session de caisse ; le vendeur compte la caisse par mode de règlement, le système calcule le théorique et l'écart, et tout écart non nul exige un motif. La validation revient au comptable ou, à défaut, au RC ou au RA (BOU-05).
6. **RG-BOU-06 Séparation des tâches, caisse.** Celui qui a saisi des ventes d'une journée ne valide pas la clôture de caisse de cette journée ; le bouton est masqué et l'appel est refusé côté serveur (BOU-05).
7. **RG-BOU-07 Séparation des tâches, inventaire.** L'ajustement issu d'un inventaire est validé par le RC ou le RA, sans intérim nécessaire pour le RA, jamais par celui qui a compté ; à la validation, chaque écart devient un mouvement « ajustement inventaire » (BOU-07).
8. **RG-BOU-08 Reversements.** Montant dû à une productrice = ventes validées non annulées de ses produits en dépôt-vente sur la période, moins la part du centre convenue au dépôt ; solde restant dû = montants dus cumulés moins reversements payés (BOU-08).
9. **RG-BOU-09 Séparation des tâches, reversement.** Le reversement est préparé par le comptable, validé par le RC ou le RA, jamais par celui qui l'a préparé, puis marqué « Payé » avec date, mode et pièce justificative par une personne autre que celle qui l'a validé (BOU-08).
10. **RG-BOU-10 Modes de règlement.** Le règlement se fait en espèces, par Mobile Money (demande de paiement ou déclaration avec l'identifiant de transaction, section 12), ou par virement ou chèque déclaré avec sa référence ; une vente peut combiner plusieurs modes. Un règlement Mobile Money ne compte dans les encaissements confirmés qu'une fois confirmé par l'opérateur (RG-PAY-03) ; aucun autre paiement électronique n'est intégré (A6, PAY-13).
11. **RG-BOU-11 Montants entiers en GNF.** Prix, remises, règlements, fonds et comptages de caisse, montants dus et reversements sont des entiers en francs guinéens ; une remise exige un motif (BOU-03).
12. **RG-BOU-12 Prix historisés.** Une modification de prix crée une nouvelle période datée et tracée ; chaque ligne de vente conserve le prix unitaire appliqué, si bien qu'un changement de prix est sans effet sur les ventes passées (BOU-11).
13. **RG-BOU-13 Saisie différée sur reçu papier de secours.** En cas de panne de l'appareil (une coupure de réseau n'empêche pas la vente, RG-OFF-01), le vendeur remplit un reçu papier numéroté de secours ; la vente est saisie le jour même avec sa date et son heure réelles et le numéro papier en référence, puis reçoit son numéro système. Un numéro papier est unique par point de vente, et la caisse du jour ne passe « Comptée » qu'une fois tous les reçus papier saisis et tous les appareils du point de vente synchronisés (OFF-08).
14. **RG-BOU-14 Confidentialité et cloisonnement.** La boutique d'un centre n'est visible que des utilisateurs de ce centre (RG-GEN-01) ; le VB ne voit d'une productrice déposante que son nom et son code, le CPT son identité minimale (nom, prénom, code, téléphone) (BOU-08).
15. **RG-BOU-15 Exports.** Les journaux des ventes, des clôtures de caisse et des reversements s'exportent en tableur pour la comptabilité tenue hors de l'outil ; chaque export est journalisé (BOU-10, RG-EXP-01).
16. **RG-BOU-16 Salle d'exposition.** Le stock d'un produit est la somme de ses mouvements par emplacement (boutique, salle d'exposition) ; un transfert entre emplacements crée un mouvement sortant et un mouvement entrant de même quantité, tracés, sans effet sur le stock total ni sur la part des productrices ; une vente depuis la salle d'exposition décrémente cet emplacement et suit les mêmes reçus et la même caisse. Avant de désactiver la seule salle d'exposition, ses articles sont transférés vers la boutique (BOU-15, RG-ADM-19).

### 9.6 Statuts et transitions

**Vente**

| De | Vers | Action et rôle | Condition |
| --- | --- | --- | --- |
| (aucun) | Validée | Valider la vente, VB | Au moins une ligne ; règlements égaux au total ; numéro de reçu attribué (RG-BOU-01) |
| Validée | Annulée | Annuler, CPT, Resp. centre ou RA | Motif obligatoire ; contre-écriture liée (RG-BOU-02) |

**Session de caisse**

| De | Vers | Action et rôle | Condition |
| --- | --- | --- | --- |
| (aucun) | Ouverte | Ouvrir la caisse, VB | Fond de caisse saisi ; aucune autre session ce jour-là |
| Ouverte | Comptée | Compter la caisse, VB | Montants comptés par mode ; motif si écart ; reçus papier du jour saisis (RG-BOU-13) ; ventes du jour de tous les appareils synchronisées (OFF-08) |
| Comptée | Validée | Valider, CPT ; à défaut Resp. centre ou RA | Écart nul ; valideur sans vente saisie ce jour-là (RG-BOU-06) |
| Comptée | Validée avec écart | Valider, mêmes rôles | Écart non nul et motivé ; même condition sur le valideur |
| Comptée | Ouverte | Renvoyer au recomptage, valideur | Motif obligatoire |

**Inventaire**

| De | Vers | Action et rôle | Condition |
| --- | --- | --- | --- |
| (aucun) | En comptage | Ouvrir l'inventaire, Resp. centre ou RA | Quantités théoriques figées à l'ouverture |
| En comptage | Compté | Terminer le comptage, VB ou agent admin. | Quantité comptée saisie pour chaque ligne ; motif pour chaque écart |
| Compté | Validé | Valider l'ajustement, Resp. centre ou RA | Valideur différent du compteur ; les écarts deviennent des mouvements (RG-BOU-07) |
| Compté | En comptage | Faire recompter, Resp. centre ou RA | Motif obligatoire |

**Reversement**

| De | Vers | Action et rôle | Condition |
| --- | --- | --- | --- |
| (aucun) | Préparé | Préparer, CPT | Montant reversé au plus égal au solde restant dû (RG-BOU-08) |
| Préparé | Validé | Valider, Resp. centre ou RA | Valideur différent du préparateur (RG-BOU-09) |
| Validé | Payé | Marquer payé, CPT | Date, mode et pièce justificative ; auteur différent du valideur |

### 9.7 Critères d'acceptation

- **CA-BOU-01** Quand deux vendeurs valident une vente au même instant sur deux appareils du même point de vente, en ligne ou hors ligne, alors chaque reçu porte la série de son appareil, aucun numéro n'est attribué deux fois et chaque série du jour ne présente aucun trou.
- **CA-BOU-02** Une vente validée n'a ni bouton Modifier ni bouton Supprimer ; son annulation exige un motif, crée une contre-écriture liée, remet les quantités en stock, et le reçu d'origine affiche « Annulée ».
- **CA-BOU-03** Après une modification du prix d'un produit, les reçus antérieurs affichent toujours l'ancien prix et le chiffre d'affaires passé est inchangé.
- **CA-BOU-04** Le stock affiché est égal à la somme des mouvements, aucun écran ne permet de le saisir, et une vente qui le rend négatif affiche une alerte.
- **CA-BOU-05** Le vendeur qui a saisi des ventes du jour ne voit pas le bouton de validation de la clôture ; un appel direct est refusé et journalisé ; une clôture avec écart sans motif est refusée.
- **CA-BOU-06** La personne qui a compté un inventaire ne peut pas valider son ajustement ; un RA sans intérim peut le valider.
- **CA-BOU-07** Étant donné une productrice dont les produits en dépôt-vente ont été vendus pour 500 000 GNF avec une part du centre de 20 %, le montant dû affiché est 400 000 GNF ; après un reversement payé de 250 000 GNF, le solde restant dû est 150 000 GNF.
- **CA-BOU-08** Un reversement ne peut être ni validé par la personne qui l'a préparé, ni marqué « Payé » par celle qui l'a validé ou sans pièce justificative.
- **CA-BOU-09** Un montant décimal est refusé ; un règlement Mobile Money déclaré reste « Déclaré », hors des encaissements confirmés, tant que l'opérateur ne l'a pas confirmé ; aucun écran ne propose la carte bancaire.
- **CA-BOU-10** Une vente saisie en différé le jour même porte la date et l'heure réelles et le numéro du reçu papier ; un même numéro papier saisi deux fois est refusé.
- **CA-BOU-11** Le VB n'accède à aucune fiche bénéficiaire ; le CPT ne voit des déposantes que nom, prénom, code et téléphone ; la boutique d'un centre est invisible depuis un autre centre.
- **CA-BOU-12** Une vente de 10 lignes est enregistrée et son reçu affiché en moins de 2 secondes en 3G.
- **CA-BOU-13** L'export du journal des ventes reproduit exactement la liste filtrée et est journalisé avec le nombre de lignes.

### 9.8 Source unique et clôture mensuelle

CAEF Connect devient la seule source des montants du centre : chaque montant est saisi une fois, et un état de rapprochement mensuel, vérifié par le comptable puis validé par le responsable de centre, fige le mois (SRC-01 à SRC-04). Cette exigence répond au constat fait au CAEF Cameroun : les chiffres de la comptable diffèrent de ceux de la responsable du centre.

Flux couverts : ventes et annulations de la boutique, encaissements des sessions de caisse par mode de règlement, paiements de scolarité et de services associés (espèces, et Mobile Money confirmé et rapproché avec le relevé de l'opérateur, section 12), reversements payés, contributions financières reçues par le centre. La comptabilité générale, les salaires et les achats restent hors de l'outil (RG-CTR-07, RG-BOU-15).

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-SRC-01 Clôture mensuelle et rapprochement | Centre, mois, statut ; par flux et par devise : montant outil (S), montant des pièces (caisse physique, relevés, carnet de reçus), écart (S), motif ; liste des sessions de caisse non validées et des reçus papier non saisis du mois ; actions Vérifier, Valider, Renvoyer ; export PDF et tableur de l'état (SRC-02) | CPT (vérification), Resp. centre ou RA en intérim (validation) |

| Objet | Champs | Contrôles |
| --- | --- | --- |
| Clôture mensuelle | Centre (S), mois (S), statut (S), totaux par flux et par devise (S), écart total (S), motif (C : écart non nul), vérifiée par et le (S), validée par et le (S) | Une clôture par centre et par mois ; aucun total multi-devises sans taux daté |
| Ligne de rapprochement | Flux (S), devise (S), montant outil (S), montant des pièces (O), écart (S), motif (C : écart non nul) | Montants entiers en GNF ; montant d'origine conservé en USD ou EUR |

1. **RG-SRC-01 Saisie unique.** Aucun montant financier des flux couverts n'est saisi hors de CAEF Connect : la vue du CPT, le tableau de bord du responsable de centre et les rapports lisent les mêmes enregistrements. L'outil n'offre ni saisie de total mensuel à la main ni import de tableur parallèle pour ces flux (SRC-01).
2. **RG-SRC-02 Clôture mensuelle.** Le 1er de chaque mois, le système génère l'état du mois écoulé ; le CPT saisit les montants des pièces, motive chaque écart et vérifie ; le responsable de centre, ou le RA pendant un intérim déclaré (RG-ADM-14), valide. Le vérificateur ne valide jamais sa propre clôture : le bouton est masqué et l'appel refusé côté serveur. À la validation, le mois est verrouillé : aucune opération des flux couverts ne peut plus être créée ou modifiée avec une date de ce mois (SRC-02).
3. **RG-SRC-03 Correction après verrouillage.** Une erreur découverte sur un mois verrouillé se corrige par une écriture de régularisation datée du mois courant, motivée et référencée au mois corrigé ; elle apparaît dans l'état du mois courant et l'état validé du mois corrigé reste inchangé. L'annulation d'une vente suit la même logique (RG-BOU-02) (SRC-02).

**Clôture mensuelle**

| De | Vers | Action et rôle | Condition |
| --- | --- | --- | --- |
| (aucun) | À faire | Générer, système | 1er jour du mois suivant |
| À faire | Vérifiée | Vérifier, CPT | Montant des pièces saisi pour chaque ligne ; motif pour chaque écart ; sessions de caisse du mois validées ; reçus papier du mois saisis ; chaque appareil enrôlé synchronisé après la fin du mois, sauf décision motivée du RC (OFF-08) ; écarts de rapprochement Mobile Money du mois motivés (PAY-10) |
| Vérifiée | Validée | Valider, Resp. centre ou RA en intérim | Écart nul ; valideur différent du vérificateur (RG-SRC-02) |
| Vérifiée | Validée avec écart | Valider, mêmes rôles | Écart non nul et motivé ; même condition sur le valideur |
| Vérifiée | À faire | Renvoyer, valideur | Motif obligatoire |

« Validée » et « Validée avec écart » sont définitifs et verrouillent le mois. Le tableau de bord de centre affiche le statut de la dernière clôture et IND-50, part des mois validés au plus tard le 10 du mois suivant (SRC-04).

**Reprise des registres papier (SRC-03, MIG-01).** Avant l'ouverture du pilote, les livrets et feuilles volantes du centre sont inventoriés. Pour la période reprise, les chiffres de la comptable et ceux de la responsable sont rapprochés ligne à ligne ; une divergence non résolue est importée avec le statut « à vérifier », les deux valeurs et leurs références de registre, jamais arbitrée par supposition (RG-BEN-08). Le premier mois clos dans l'outil est le premier mois complet du pilote.

- **CA-SRC-01** Le montant d'une vente validée par le VB apparaît à l'identique, sans ressaisie, dans la vue du CPT, sur le tableau de bord du responsable de centre et dans l'export ; aucun écran ne permet de saisir un total mensuel.
- **CA-SRC-02** La vérification est refusée tant qu'une session de caisse du mois n'est pas validée, qu'un reçu papier n'est pas saisi ou qu'un écart n'est pas motivé.
- **CA-SRC-03** Le CPT qui a vérifié la clôture ne voit pas le bouton Valider et un appel direct est refusé et journalisé ; le RA ne valide que pendant un intérim déclaré.
- **CA-SRC-04** Après validation, une opération datée du mois verrouillé ne peut être ni créée ni modifiée ; la régularisation est datée du mois courant, référencée au mois corrigé, et l'état validé reste inchangé.
- **CA-SRC-05** Une contribution reçue en USD figure sur sa propre ligne de rapprochement et n'est jamais additionnée aux montants en GNF.
- **CA-SRC-06** Le tableau de bord de centre affiche le statut de la dernière clôture (À faire, Vérifiée, Validée, Validée avec écart) et la valeur d'IND-50.
- **CA-SRC-07** À la reprise, un montant inscrit avec deux valeurs différentes dans deux registres papier est importé « à vérifier » avec les deux valeurs et leurs références ; aucune valeur n'est choisie automatiquement.

## 10. Scénarios d'utilisation et critères d'acceptation

Neuf scénarios de bout en bout couvrent les processus prioritaires du PRD (H3), dont la boutique (SC-06), la clôture mensuelle (SC-07), une journée sans réseau (SC-08) et le paiement de la scolarité par Mobile Money (SC-09), obligatoires pour le pilote ; chacun est recetté tel quel sur l'environnement de préproduction avec des données fictives (Plan de tests, campagne C2).

### SC-01 Inscription d'une bénéficiaire

Aissatou, agente au centre Cameroun, reçoit Mariama, 22 ans, pour la formation « Couture et entrepreneuriat ». Elle recherche Mariama par nom et année de naissance, ne trouve aucun dossier, crée la candidature et joint la pièce demandée. Le responsable du centre valide, puis le responsable pédagogique l'inscrit à la session d'octobre.

- **CA-01a** Quand l'agente saisit un nom et une année de naissance déjà enregistrés dans un autre centre avec un score de 60 ou plus, alors le système bloque la création jusqu'à ce qu'elle ouvre le dossier existant ou déclare une personne différente avec commentaire.
- **CA-01b** Étant donné une candidature sans champ obligatoire, quand l'agente clique « Soumettre », alors le bouton reste inactif et les champs manquants sont listés.
- **CA-01c** Étant donné une session pleine, quand le responsable pédagogique tente l'inscription, alors le système propose la liste d'attente.
- **CA-01d** Chaque transition est visible dans l'onglet Historique avec auteur et date.

### SC-02 Session, présences et clôture

Le responsable pédagogique crée la session (12 séances, capacité 20) et affecte Fatou, formatrice. À chaque séance, Fatou ouvre E-FOR-07 sur son téléphone, marque les présences et valide. À la fin, le responsable clôture.

- **CA-02a** Une session sans lieu, capacité ou séance ne peut pas passer « Ouverte ».
- **CA-02b** Si la connexion tombe pendant la saisie, les présences cochées sont conservées et envoyées au retour du réseau, sans doublon.
- **CA-02c** Fatou ne voit ni les sessions d'autres formateurs ni les coordonnées des inscrites.
- **CA-02d** À la clôture, les inscrites au-dessus du seuil de présence sont proposées « Achevée », les autres « Non achevée », et le rapport R-01 distingue inscrites, commencées, achevées et attestées.
- **CA-02e** Une session clôturée ne peut être modifiée qu'après réouverture motivée par le responsable de centre.

### SC-03 Suivi d'une opportunité RSE

Le responsable RSE enregistre une entreprise de téléphonie rencontrée lors d'un salon, qualifie le prospect, consigne deux rendez-vous et le diagnostic, puis rattache la fiche projet « Atelier numérique » remontée par le « Centre de test B », centre fictif de recette.

- **CA-03a** La création d'un partenaire de nom proche d'un partenaire existant affiche une alerte.
- **CA-03b** Chaque changement d'étape est historisé et la durée par étape alimente E-TDB-04.
- **CA-03c** Une opportunité dont la prochaine action est dépassée de 7 jours apparaît dans les alertes du responsable.
- **CA-03d** Le responsable de centre Cameroun ne voit pas cette opportunité si elle ne concerne que le Centre de test B.

### SC-04 Proposition et convention

Le responsable RSE prépare une proposition de 150 000 000 GNF, le responsable du centre Cameroun donne un avis favorable, la Direction Générale valide, la proposition est envoyée puis acceptée pour 120 000 000 GNF. La convention est signée avec trois engagements.

- **CA-04a** Une proposition non validée ne peut pas être marquée « Soumise ».
- **CA-04b** La modification d'une proposition soumise crée une version 2, la version 1 restant consultable.
- **CA-04c** La convention ne passe « Signée » qu'avec le document signé déposé ; le tableau de bord affiche alors 150 000 000 sollicités et 120 000 000 accordés, 0 reçu.
- **CA-04d** Le lendemain de l'échéance d'un engagement non réalisé, celui-ci passe « En retard » et apparaît au tableau de bord RSE.

### SC-05 Réception de contributions

Le partenaire verse une première tranche de 60 000 000 GNF et livre 15 ordinateurs estimés sur facture à 45 000 000 GNF.

- **CA-05a** Sans justificatif, la tranche ne peut pas passer « Reçue ».
- **CA-05b** La personne qui a saisi la réception ne peut pas la valider.
- **CA-05c** Le tableau de bord affiche 60 000 000 GNF reçus en financier et 45 000 000 GNF en nature, sur deux lignes distinctes jamais additionnées, et 60 000 000 GNF encore promis.
- **CA-05d** Le rapport partenaire R-04 ne contient aucun nom de bénéficiaire.

### SC-06 De l'atelier à la vente et au reversement

Kadiatou, bénéficiaire du centre Cameroun, dépose 20 sacs tissés en dépôt-vente à 25 000 GNF pièce, avec une part du centre de 20 %. Mamadou, vendeur, en vend 12 en 5 ventes dans la journée, dont une réglée par mobile money, puis compte la caisse. Hawa, comptable, valide la clôture. En fin de mois, l'agente admin. compte l'inventaire et le responsable adjoint le valide. Hawa prépare le reversement à Kadiatou, le responsable du centre le valide, et Hawa l'enregistre payé avec la pièce.

- **CA-06a** Le dépôt crée un mouvement « entrée dépôt » de 20 sacs rattaché à Kadiatou ; après les ventes, le stock calculé affiche 8.
- **CA-06b** Les 5 ventes portent des numéros de reçu consécutifs sans trou ; la vente par Mobile Money, déclarée avec son identifiant de transaction, passe « Confirmé » au rapprochement avec la transaction de l'opérateur.
- **CA-06c** Mamadou ne peut pas valider la clôture de sa journée ; Hawa la valide, et un écart non nul exigerait un motif.
- **CA-06d** L'agente qui a compté l'inventaire ne peut pas valider l'ajustement ; le responsable adjoint le valide sans intérim déclaré.
- **CA-06e** Le montant dû à Kadiatou est 240 000 GNF (300 000 GNF moins 20 %) ; le reversement préparé par Hawa ne peut pas être validé par elle, il l'est par le responsable du centre, et une fois payé le solde restant dû passe à 0.
- **CA-06f** Après le recalcul, le tableau de bord du centre affiche des indicateurs cohérents : IND-45 = 300 000 GNF, IND-46 = 5 ventes, IND-47 = 240 000 GNF reversés à 1 productrice, IND-48 = 0 %, IND-49 = 1 productrice active.

### SC-07 Fin de mois : une seule vérité entre comptable et responsable

Le 3 novembre, Hawa, comptable du centre Cameroun, ouvre l'état d'octobre généré le 1er : ventes 1 850 000 GNF, encaissements 1 850 000 GNF (1 450 000 en espèces, 400 000 par mobile money), un reversement payé de 240 000 GNF et une contribution financière reçue de 60 000 000 GNF. Elle saisit les montants des pièces : les espèces remises font 10 000 GNF de moins, une erreur de rendu de monnaie déjà constatée à la clôture du 17 octobre. Elle motive l'écart et vérifie ; la responsable du centre valide le 5 novembre. Le 12 novembre, Hawa découvre une vente de 25 000 GNF du 30 octobre saisie en double et l'annule.

- **CA-07a** Les montants d'octobre affichés à Hawa sur E-SRC-01 et ceux du tableau de bord de la responsable sont identiques ligne à ligne, sans aucune ressaisie.
- **CA-07b** La vérification est refusée tant que l'écart de 10 000 GNF n'est pas motivé ; Hawa ne peut pas valider ; la responsable valide et le statut passe « Validée avec écart ».
- **CA-07c** La contribution de 60 000 000 GNF figure sur sa propre ligne, distincte des ventes et des encaissements de caisse.
- **CA-07d** Après validation, aucune vente datée d'octobre ne peut être créée ou modifiée ; l'annulation du 12 novembre est datée du 12 novembre, référencée à octobre, apparaît dans l'état de novembre, et l'état validé d'octobre reste à 1 850 000 GNF.
- **CA-07e** Le tableau de bord du centre affiche « Octobre : validée avec écart », et IND-50 compte octobre comme validé dans les délais (avant le 10 novembre).

### SC-08 Une journée sans réseau

Le 14 octobre, le réseau est coupé au centre Cameroun de 8 h à 17 h. Aïssatou, formatrice, saisit les présences de deux séances sur son téléphone ; Fanta, agente admin., crée deux candidatures, dont une pour une personne déjà inscrite, et encaisse 50 000 GNF en espèces ; Mamadou vend 4 articles sur la tablette de la boutique, dont un réglé par Mobile Money qu'il déclare avec l'identifiant lu sur le SMS de l'acheteuse. Le matin, la responsable du centre a corrigé en ligne le téléphone d'une bénéficiaire dont Fanta change le quartier hors ligne. Le réseau revient à 17 h.

- **CA-08a** Sans action des utilisatrices, toutes les opérations arrivent au serveur dans les minutes qui suivent le retour du réseau, une seule fois chacune, et l'indicateur passe au vert.
- **CA-08b** Les 4 reçus de Mamadou portent la série de la tablette et des numéros consécutifs ; il ne peut compter la caisse qu'une fois la tablette synchronisée.
- **CA-08c** La candidature de la personne déjà inscrite passe « À vérifier, doublon probable » ; aucune saisie n'est perdue.
- **CA-08d** La fiche modifiée des deux côtés garde le nouveau téléphone et le nouveau quartier, sans conflit, car les champs diffèrent.
- **CA-08e** La vente réglée par Mobile Money reste « Déclaré » jusqu'au rapprochement, puis passe « Confirmé » ; elle n'entre dans les encaissements confirmés qu'à ce moment.

### SC-09 Payer la scolarité par Mobile Money

Mariama s'inscrit à la session de couture d'octobre, dont la scolarité est de 150 000 GNF en deux versements. Au premier versement, Fanta envoie une demande de paiement de 75 000 GNF au téléphone de sa mère, qui la valide avec son code secret. Pour le second, la mère paie elle-même depuis le marché, avec la référence imprimée sur l'avis d'échéance. Le même jour, un paiement de 20 000 GNF arrive sur le compte marchand sans référence. Le lendemain, le relevé de l'opérateur est rapproché.

- **CA-09a** L'inscription crée deux échéances de 75 000 GNF, chacune avec sa référence de paiement.
- **CA-09b** Le premier paiement passe « Confirmé » à la notification de l'opérateur, le reçu est émis et le restant dû passe à 75 000 GNF ; ni Fanta ni l'outil ne voient le code secret.
- **CA-09c** Le second paiement est affecté automatiquement à la seconde échéance et le restant dû passe à 0.
- **CA-09d** Le paiement sans référence entre dans « Paiements à affecter » ; Hawa, comptable, l'affecte avec un motif.
- **CA-09e** Le rapprochement du lendemain apparie les trois transactions sans écart ; la commission de l'opérateur apparaît à part, et les encaissements du jour affichent 170 000 GNF bruts.

### Critères transverses

- **CA-T1** Un utilisateur du centre A qui modifie l'adresse d'une fiche pour viser un dossier du centre B reçoit un refus, et la tentative est journalisée (SEC-01).
- **CA-T2** Un export reproduit exactement la liste affichée et est journalisé avec le nombre de lignes.
- **CA-T3** Toutes les pages de saisie sont utilisables sur un téléphone de 360 pixels de large.
- **CA-T4** Pendant un intérim déclaré, le RA peut faire une validation réservée au RC sur son centre ; le lendemain de la date de fin, la même validation lui est refusée (USR-09).
- **CA-T5** Le comptable renseigne la référence de pièce et la date d'encaissement constatée d'une contribution financière reçue de son centre, sans pouvoir la valider ni modifier ses autres champs (CTR-09).

## 11. Points ouverts et traçabilité

Douze valeurs de cette SFD sont des propositions par défaut à confirmer par les référents métiers ; elles sont paramétrables, donc leur changement ne remet pas en cause la conception.

| N° | Point à confirmer | Valeur proposée | Qui confirme |
| --- | --- | --- | --- |
| PO-01 | Liste minimale des champs du dossier bénéficiaire | Section 4.2 | Direction Générale, avec le référent données |
| PO-02 | Seuils et poids de détection des doublons | 60 bloquant, 40 informatif | Suivi-évaluation, après calibrage sur l'import pilote |
| PO-03 | Seuil de présence pour l'achèvement | 80 % par défaut, réglable par formation | Resp. pédagogiques |
| PO-04 | Délai de saisie des présences et d'alerte d'abandon | 7 jours ; 3 absences consécutives | Resp. pédagogiques |
| PO-05 | Circuit et seuil de validation des propositions | Resp. RSE, avis du centre, Direction Générale ; seuil à fixer | Direction Générale (H5) |
| PO-06 | Inactivité des comptes et des dossiers | 90 jours ; 12 mois | Admin. national |
| PO-07 | Mode de recueil du consentement | Écrit ou oral devant témoin, tracé | Référent données, avec avis juridique |
| PO-08 | Délai de la clôture mensuelle | Validation au plus tard le 10 du mois suivant (IND-50) | Direction Générale, avec la comptable du centre pilote |
| PO-09 | Durée maximale sans reconnexion en ligne et seuil d'alerte de retard de synchronisation | 72 heures ; 48 heures | Direction Générale, avec l'admin. national |
| PO-10 | Délai avant « Non retrouvé » d'un paiement Mobile Money déclaré | 24 heures | CPT du centre pilote, avec l'opérateur retenu |
| PO-11 | Conséquence d'un impayé de scolarité | Aucun blocage automatique ; relance et décision du RC | Direction Générale (H15) |
| PO-12 | Modules optionnels activés au pilote ; usage de la salle d'exposition | Tous activés au CAEF Cameroun ; vente possible depuis la salle d'exposition | Porteur de projet et Direction Générale |

Le porteur de projet a tranché le 12/10/2026 quatre points du PRD : un seul centre pilote, le CAEF Cameroun à Dixinn (A1) ; la RSE dans le lot 1 (A14) ; la boutique dans le lot 1 (H14) ; la crèche reportée à plus tard (A3). Ces décisions restent à formaliser par la Direction Générale des CAEF ; les autres écarts du PRD restent ouverts. Le diagnostic du CAEF Cameroun doit établir s'il pratique le dépôt-vente et avec quelle part du centre, qui tient la caisse aujourd'hui, si la comptable est propre au centre ou mutualisée, quels modes de règlement sont utilisés et quels registres papier existent pour la reprise. Les demandes du 13/10/2026 (hors ligne d'abord, paiements Mobile Money) restent aussi à formaliser ; le diagnostic relève la couverture réseau du centre et les opérateurs Mobile Money utilisés par les payeuses (H16). Les rôles d'adjoint et de comptable et les circuits de validation des clôtures de caisse et des clôtures mensuelles sont à confirmer par la Direction Générale.

### Mise en œuvre dans le backend du lot 1 (14/10/2026)

Le backend du lot 1 applique les règles de cette SFD dans les services métier (`services.py` de chaque module) et les expose par l'API REST décrite au DAT, § 4.2 ; les écrans E-xxx restent à construire. Chaque point ouvert ci-dessus y est un paramètre réglable sans code (variable d'environnement, ou table administrée) :

| N° | Paramètre du backend | Valeur par défaut |
| --- | --- | --- |
| PO-01 | `CHAMPS_REQUIS_DOSSIER` | nom, prénoms, sexe, zone de résidence, date et mode du consentement, naissance (date, année ou tranche d'âge) |
| PO-02 | `CAEF_SEUIL_DOUBLON_BLOQUANT`, `CAEF_SEUIL_DOUBLON_INFORMATIF` | 60 ; 40 |
| PO-03 | `CAEF_SEUIL_PRESENCE_DEFAUT`, et seuil propre à chaque formation | 80 % |
| PO-04 | `CAEF_DELAI_SAISIE_PRESENCES_JOURS`, `CAEF_ABSENCES_CONSECUTIVES_ALERTE` | 7 jours ; 3 absences |
| PO-05 | `CAEF_SEUIL_SECONDE_VALIDATION_PROPOSITION` | Vide : pas de seconde validation par la DG tant que le seuil n'est pas fixé |
| PO-06 | `CAEF_INACTIVITE_COMPTE_JOURS`, `CAEF_JOURS_INACTIVITE_DOSSIER` | 90 jours ; 365 jours |
| PO-07 | Champ `consentement_mode` du dossier, liste fermée | Écrit ou oral devant témoin |
| PO-08 | `CAEF_CLOTURE_MENSUELLE_JOUR_LIMITE` | Le 10 du mois suivant |
| PO-09 | `CAEF_HORS_LIGNE_VALIDITE_HEURES`, `CAEF_ALERTE_SYNCHRO_HEURES` | 72 heures ; 48 heures |
| PO-10 | `CAEF_PAIEMENT_NON_RETROUVE_HEURES` | 24 heures |
| PO-11 | Aucun paramètre : un impayé n'empêche ni l'inscription ni la présence | Aucun blocage |
| PO-12 | Table `module_centre`, administrée par l'ADM | Tous les modules optionnels activés au CAEF Cameroun dans les données fictives |

Les tarifs de la scolarité (H15) sont saisis dans la table `tarif_service` ; sans tarif en vigueur, aucune échéance n'est créée. La passerelle Mobile Money (H16) est choisie par `CAEF_PASSERELLE_MOBILE_MONEY`, en mode `declaratif` par défaut.

Là où cette SFD et la Matrice divergent, le backend retient la lecture la plus restrictive : annulation d'une vente par le CPT seul, annulation d'une candidature avec le droit A (RC, ou RA en intérim), file « À résoudre » scindée entre conflits (RC, RA) et écritures tardives (CPT), et les autres points listés dans la Matrice, § 5.1. Quelques règles reçoivent une précision de mise en œuvre, notée dans `backend/DECISIONS.md` :

- **Doublons (RG-BEN-04).** Une date de naissance connue à l'année près ne compare que l'année, et seulement si les deux dossiers sont à cette précision. Le téléphone seul ne donne aucun point.
- **Fusion (RG-BEN-05).** Elle est annulable pendant 30 jours : l'état avant fusion est conservé.
- **Numérotation des reçus (RG-BOU, OFF-08).** Une série par appareil, au numéro continu. En ligne sans appareil, la série est `<centre>-W` pour les ventes et `<centre>-P` pour les paiements. Un numéro sauté est consigné comme vente annulée de total nul, et les contre-écritures d'annulation prennent la série `ANN`.
- **Reversements.** L'arrondi au franc se fait à la fin du calcul, au demi supérieur.
- **Écriture tardive régularisée (RG-SRC-03, OFF-05).** Elle est rejouée au nom de l'auteur d'origine, dans la série web, datée du mois courant avec le mois corrigé. Le numéro d'appareil non utilisé est consigné comme annulé.
- **Clôture mensuelle.** Le RC peut accorder une dérogation pour clôturer malgré un appareil non synchronisé ; la dérogation est tracée sur la clôture.
- **Notifications de paiement (RG-PAY).** Une signature invalide est refusée et journalisée, un doublon est accepté sans effet, et le montant retenu est celui de l'opérateur.

Ne sont pas couverts par ce lot : la lecture de l'historique d'un dossier par le centre d'origine après un transfert, et le volet boutique du tableau de bord national pour la DG, prévu au lot 2.

### Traçabilité PRD vers SFD

| Exigences PRD | Sections et règles SFD |
| --- | --- |
| ADM-01 à ADM-05, ADM-08, USR-01 à USR-07, USR-09, SEC-08, SEC-11 | 3 ; RG-ADM-01 à RG-ADM-20 ; E-ADM-10 ; CA-ADM-01 à CA-ADM-03 |
| BEN-01 à BEN-13, MIG-01, DAT-01 | 4 ; RG-BEN-01 à RG-BEN-09 ; 9.8 (reprise des registres papier) |
| FOR-01 à FOR-16 | 5 ; RG-FOR-01 à RG-FOR-12 |
| PAR-01 à PAR-09, CNV-10 | 6 ; RG-PAR-01 à RG-PAR-07 |
| CNV-01 à CNV-08, CTR-01 à CTR-07, CTR-09 | 7 ; RG-CNV-01 à RG-CNV-10, RG-CTR-01 à RG-CTR-10 |
| TDB-01 à TDB-09, REP-01 à REP-06, NOT-01, SEC-04, SEC-10 | 8 ; RG-TDB-01 à RG-TDB-04, RG-EXP-01 à RG-EXP-03 |
| SEC-01, UX-01 à UX-03, NET-01, NET-02 | 1 (RG-GEN) et 2 |
| DOC-01 | Onglets « Pièces » des fiches centre, formation, partenaire, convention (2.2) |
| BOU-01 à BOU-11 et BOU-15 (lot 1, H14 tranchée) | 9 ; RG-BOU-01 à RG-BOU-16 ; E-BOU-09 ; SC-06 |
| SRC-01 à SRC-04 | 9.8 ; E-SRC-01 ; RG-SRC-01 à RG-SRC-03 ; CA-SRC-01 à CA-SRC-07 ; SC-07 |
| OFF-01 à OFF-08 | 2.3 ; RG-OFF-01 à RG-OFF-10 ; E-OFF-01, E-OFF-02 ; CA-OFF-01 à CA-OFF-04 ; SC-08 |
| PAY-01 à PAY-11, SEC-14 | 12 ; RG-PAY-01 à RG-PAY-12 ; CA-PAY-01 à CA-PAY-08 ; SC-09 |

## 12. Scolarité et paiements

Le module enregistre ce que chaque bénéficiaire doit pour sa scolarité et les services associés, encaisse en espèces ou par Mobile Money, et rapproche chaque paiement avec l'opérateur (PAY-01 à PAY-11, SEC-14). Il est demandé par le porteur de projet le 13/10/2026, à formaliser par la Direction Générale. CAEF Connect ne détient jamais les fonds : un paiement Mobile Money arrive directement sur le compte marchand des CAEF, et seule la confirmation de l'opérateur en fait un encaissement. La facturation de la scolarité et les parcours avec passerelle sont mis en service dès que la politique tarifaire (H15) et la passerelle (H16) sont arrêtées ; jusque-là, le Mobile Money est déclaré avec son identifiant de transaction.

### 12.1 Écrans

| Écran | Contenu | Rôle principal |
| --- | --- | --- |
| E-PAY-01 Services et tarifs | Service (frais d'inscription, scolarité d'une session, examen ou attestation, service associé), centre, formation, montant, nombre de versements et dates, période de validité ; historique des tarifs (PAY-01) | Admin. national (saisie sur décision de la DG), Resp. centre (consultation) |
| E-PAY-02 Situation de la bénéficiaire | Onglet « Paiements » de la fiche bénéficiaire : échéances (service, montant, date limite, référence de paiement, statut), exonérations, paiements et reçus, restant dû ; actions Encaisser, Demander un paiement, Imprimer l'avis d'échéance (PAY-02, PAY-09) | Agent admin., CPT |
| E-PAY-03 Exonérations et prises en charge | Bénéficiaire, échéance, type (bourse, réduction motivée, partenaire, programme), montant ou pourcentage, motif, pièce, statut ; validation (PAY-03) | Agent admin. ou CPT (saisie), Resp. centre (validation) |
| E-PAY-04 Encaissement | Écran optimisé téléphone : échéances à régler, montant, canal (espèces ; Mobile Money par demande de paiement ; Mobile Money déclaré), numéro de la payeuse (C : demande), identifiant de transaction (C : déclaré), répartition sur les échéances ; statut en direct ; reçu (PAY-04, PAY-05, PAY-07) | Agent admin., CPT |
| E-PAY-05 Paiements du centre | Liste filtrable : date, bénéficiaire ou vente, canal, opérateur, montant brut, commission, net, statut, référence de l'opérateur ; files « Paiements à affecter » et « Non retrouvés » (PAY-06, PAY-08) | CPT |
| E-PAY-06 Rapprochement quotidien | Par jour et par opérateur : transactions de l'opérateur, paiements de l'outil, paires appariées, écarts (présent d'un seul côté, montant différent), motif ; totaux repris par la clôture mensuelle (PAY-10) | CPT |
| E-PAY-07 Remboursements | Paiement d'origine, montant, motif, demandé par, validé par, exécution (passerelle ou hors outil avec pièce), statut (PAY-11) | CPT (demande), Resp. centre ou RA en intérim (validation) |

### 12.2 Champs clés

| Objet | Champs | Contrôles |
| --- | --- | --- |
| Tarif | Service (O), centre (O), formation (C : scolarité), montant (O), versements (O : nombre et échéances), début (O), fin (S), auteur (S) | Entier en GNF supérieur à 0 ; un seul tarif en vigueur par service, centre et date |
| Échéance | Bénéficiaire (S), inscription (C), service (S), montant (S : tarif en vigueur à la création), date limite (S), référence de paiement (S), statut (S) | Référence unique, courte et facile à dicter (ex. CMR-26-04217) |
| Exonération | Échéance (O), type (O), montant ou pourcentage (O), motif (O), pièce (C : bourse ou partenaire), saisie par (S), validée par (S) | Au plus égale au restant dû ; valideur différent de l'auteur |
| Paiement | Canal (O), montant attendu (S), montant confirmé (S), commission (S), net (S), numéro de la payeuse (C : Mobile Money), identifiant de transaction (C : déclaré ; S : passerelle), statut (S), reçu (S), appareil et horodatage de l'appareil (S) | Montants entiers en GNF ; un identifiant de transaction de l'opérateur n'est enregistré qu'une fois |
| Affectation | Paiement (S), échéance ou vente (O), montant (O) | Somme des affectations au plus égale au montant confirmé |
| Remboursement | Paiement (O), montant (O), motif (O), demandé par (S), validé par (S), exécution (O), pièce (C : hors outil), statut (S) | Au plus égal au montant confirmé non encore remboursé |

### 12.3 Statuts d'un paiement

| De | Vers | Événement | Condition |
| --- | --- | --- | --- |
| (aucun) | Confirmé | Encaissement en espèces, agent admin. ou CPT | Montant saisi ; reçu émis |
| (aucun) | Initié | Demande de paiement, agent admin. ou CPT | Centre en ligne ; numéro de la payeuse saisi |
| Initié | En attente de la payeuse | Accusé de la passerelle | Aucune |
| En attente de la payeuse | Confirmé | Notification signée ou consultation du statut | Montant pris de l'opérateur (RG-PAY-03) |
| En attente de la payeuse | Échoué | Refus ou annulation par la payeuse ou l'opérateur | Motif de l'opérateur conservé |
| En attente de la payeuse | Expiré | Aucune réponse à la dernière consultation (60 minutes) | Aucune |
| (aucun) | Confirmé | Notification d'un paiement fait par la payeuse | Référence d'échéance valide, sinon file « Paiements à affecter » (RG-PAY-06) |
| (aucun) | Déclaré | Déclaration hors ligne, agent admin., CPT ou VB | Identifiant de transaction saisi ; reçu provisoire |
| Déclaré | Confirmé | Rapprochement avec une transaction de l'opérateur | Même identifiant ; montant de l'opérateur retenu |
| Déclaré | Non retrouvé | 24 heures sans transaction correspondante | Signalé au CPT |
| Non retrouvé | Confirmé | Transaction retrouvée au relevé, ou rapprochement manuel par le CPT | Pièce et motif |
| Confirmé | Remboursé partiellement ou Remboursé | Remboursement exécuté | Remboursement validé (RG-PAY-09) |

« Échoué », « Expiré » et « Remboursé » sont définitifs ; une nouvelle tentative crée un nouveau paiement.

### 12.4 Règles de gestion

1. **RG-PAY-01 Tarifs datés.** Un changement de tarif crée une nouvelle période datée et tracée ; une échéance garde le montant du tarif en vigueur à sa création (PAY-01).
2. **RG-PAY-02 Échéances.** L'inscription à une session crée les échéances des services liés à la formation, si un tarif est en vigueur ; l'avis d'échéance imprimable porte le montant, la date limite, la référence de paiement et le numéro marchand des CAEF. Un impayé n'empêche ni l'inscription ni la présence : il apparaît sur la fiche et au tableau de bord, et la décision reste au RC (PAY-02, H15, PO-11).
3. **RG-PAY-03 Seule la confirmation compte.** Un paiement Mobile Money n'est « Confirmé » que sur notification signée de la passerelle ou consultation de son statut ; le montant retenu est celui de l'opérateur, jamais celui saisi ou envoyé par l'appareil. Un montant confirmé inférieur au montant attendu laisse un restant dû ; supérieur, il crée un trop-perçu à affecter ou à rembourser (PAY-08, SEC-14).
4. **RG-PAY-04 Une transaction, un paiement.** Un identifiant de transaction de l'opérateur n'est enregistré qu'une fois : une notification reçue deux fois est ignorée la seconde fois, et une déclaration qui reprend un identifiant déjà confirmé est refusée (PAY-08).
5. **RG-PAY-05 Demande de paiement.** Disponible en ligne seulement. La payeuse valide sur son téléphone avec son code secret, que CAEF Connect ne demande ni ne stocke ; l'écran affiche l'attente, puis le résultat. Sans notification, le statut est consulté à 1, 5, 15 et 60 minutes, puis le paiement passe « Expiré » (PAY-05).
6. **RG-PAY-06 Paiement avec référence.** Un paiement reçu avec une référence d'échéance valide est affecté automatiquement et son reçu est disponible ; sans référence valide, il entre dans « Paiements à affecter », où le CPT l'affecte avec un motif (PAY-06).
7. **RG-PAY-07 Déclaration hors ligne.** Sans réseau, l'agent saisit l'identifiant de transaction lu sur le SMS de confirmation de la payeuse et remet un reçu provisoire marqué « Déclaré » ; au rapprochement, le paiement passe « Confirmé » ou, après 24 heures, « Non retrouvé », signalé au CPT (PAY-07, PO-10).
8. **RG-PAY-08 Encaissement et reçus.** Un encaissement en espèces ou un paiement confirmé produit un reçu numéroté dans la série de l'appareil (RG-BOU-01) ; un paiement peut couvrir plusieurs échéances, réglées de la plus ancienne à la plus récente sauf choix contraire (PAY-04).
9. **RG-PAY-09 Remboursement.** Demandé et motivé par le CPT, validé par le RC ou le RA en intérim, jamais par le demandeur ; exécuté par la passerelle si elle le permet, sinon hors outil avec pièce justificative ; l'échéance concernée redevient due pour le montant remboursé (PAY-11).
10. **RG-PAY-10 Exonérations.** Saisie motivée, validée par le RC, jamais par son auteur ; elle réduit le restant dû sans créer d'encaissement (PAY-03).
11. **RG-PAY-11 Rapprochement quotidien.** Chaque nuit, le relevé de l'opérateur est importé et apparié transaction par transaction ; chaque écart est motivé par le CPT ; les totaux du mois (brut, commission, net) entrent dans la clôture mensuelle (PAY-10, RG-SRC-02).
12. **RG-PAY-12 Commission.** La commission de l'opérateur est enregistrée à part et les encaissements sont présentés en brut, commission et net ; la part d'une productrice en dépôt-vente se calcule sur le prix de vente, jamais diminué de la commission (PAY-08, RG-BOU-08).

### 12.5 Critères d'acceptation

- **CA-PAY-01** Une notification de confirmation reçue deux fois ne crée qu'un paiement et qu'un reçu.
- **CA-PAY-02** Une notification à la signature invalide est refusée et journalisée, et le paiement reste « En attente de la payeuse ».
- **CA-PAY-03** Un paiement confirmé pour 140 000 GNF alors que 150 000 GNF étaient attendus laisse un restant dû de 10 000 GNF, sans arrondi.
- **CA-PAY-04** Un paiement déclaré sans transaction correspondante passe « Non retrouvé » après 24 heures et apparaît dans la file du CPT ; il n'est jamais compté dans les encaissements confirmés.
- **CA-PAY-05** Aucun écran ne demande ni n'affiche le code secret de la payeuse ; son numéro ne sert jamais à rechercher une bénéficiaire (DAT-01).
- **CA-PAY-06** Le CPT qui a demandé un remboursement ne voit pas le bouton Valider ; un appel direct est refusé et journalisé.
- **CA-PAY-07** Un paiement fait avec une référence inconnue entre dans « Paiements à affecter » et n'est affecté à aucune échéance sans action du CPT.
- **CA-PAY-08** Le total du mois des paiements Mobile Money confirmés est le même sur E-PAY-06, sur E-SRC-01 et au tableau de bord de centre.
