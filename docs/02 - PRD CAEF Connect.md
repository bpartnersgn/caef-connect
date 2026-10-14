# PRD CAEF Connect

Oct 12, 2026 · @Bangoura

## 1. Objet du document

Ce PRD traduit le Document Maître CAEF-CONNECT-DM-001 (v1.0) et le Cahier des charges fonctionnel (v1.0) en exigences produit priorisées ; le Dossier d'architecture technique (v1.0) en fournit les contraintes techniques (section 7) et le Plan de déploiement (v1.0) le découpage en lots et le phasage (sections 5.1 et 9). Là où les deux documents divergent, il ne choisit pas : chaque écart est listé comme point à arbitrer (section 8.2). Le module boutique (section 6.10) et les rôles de responsable adjoint et de comptable de centre viennent du porteur de projet (source « PP ») : ni le DM ni le CDC ne les décrivent. Le 12/10/2026, le porteur de projet a tranché quatre points (A1, A3, A14, H14 : un seul centre pilote, crèche hors MVP, RSE et boutique dans le lot 1) et demandé une source unique pour les chiffres (section 6.11) ; ces décisions restent à formaliser par la Direction Générale des CAEF. Le 13/10/2026, il a demandé deux exigences d'architecture : la plateforme reste utilisable sans Internet et se synchronise automatiquement au retour du réseau (OFF-01 à OFF-08, section 7), et la scolarité et les services associés peuvent être payés par Mobile Money (section 6.12) ; elles remplacent la position sur le hors ligne (H11), lèvent pour le seul Mobile Money l'exclusion du paiement intégré (A6, H9) et restent à formaliser par la Direction Générale. Il fixe ce que la première version (MVP) doit faire, pour qui, et comment on saura qu'elle réussit. Il ne tranche pas les autres décisions ouvertes : il les signale comme hypothèses à valider (section 8.1).

| Élément | Valeur |
| --- | --- |
| Référence proposée | CAEF-CONNECT-PRD-001 |
| Version | 0.2, projet soumis à validation ; intègre le hors ligne d'abord et les paiements Mobile Money demandés le 13/10/2026 |
| Documents sources | Document Maître v1.0 (DM) ; Cahier des charges fonctionnel v1.0 (CDC) ; Dossier d'architecture technique v1.0 (DAT) ; Plan de déploiement, de gouvernance et de conduite du changement v1.0 (Plan) ; demandes et décisions du porteur de projet du 12/10/2026 (PP) : boutique, responsable adjoint et comptable de centre, centre pilote, place de la RSE et de la boutique, crèche, source unique des chiffres ; demandes du 13/10/2026 : hors ligne d'abord, paiements Mobile Money de la scolarité et des services associés |
| Institution porteuse | Direction Générale des CAEF |
| Périmètre pilote | Un seul centre : le CAEF Cameroun (quartier Cameroun, commune de Dixinn, Conakry), tranché le 12/10/2026, à formaliser par la Direction Générale |
| Valideurs attendus | Direction Générale, responsable du centre pilote, référents métiers |
| Documents suivants | SFD du MVP, puis DAT détaillé à partir du DAT v1.0 |

**Convention de priorité.** Chaque exigence porte une priorité MoSCoW :

- **P0 (Indispensable)** : sans elle, le MVP ne démontre pas sa valeur. Bloquant pour le pilote.
- **P1 (Important)** : attendue dans le MVP si les ressources le permettent ; repliable en version 1.1.
- **P2 (Souhaitable)** : évolution post-MVP, phase 5 du déploiement.
- **P3 (Hors MVP)** : explicitement exclue de la première version.

Chaque exigence porte un identifiant stable (ex. BEN-03) repris dans la SFD et le cahier de recette. La dernière colonne des tableaux renvoie à la section du Document Maître (« § » ou « M » pour un module), du cahier des charges (« CDC ») ou de la demande du porteur de projet (« PP ») d'où elle provient.

## 2. Contexte, problème et vision produit

CAEF Connect doit permettre à chaque centre de gérer ses bénéficiaires et ses formations, et à la Direction Générale de piloter le réseau sur des données consolidées et vérifiables (DM § 2.2).

**Problème.** Les informations d'un réseau de centres (dossiers des bénéficiaires, formations, présences, partenaires, conventions, contributions, résultats) sont aujourd'hui dispersées. La Direction Générale ne dispose pas d'une vue consolidée fiable, et les résultats présentés aux partenaires sont difficiles à relier à leurs sources. Le CDC (§ 2.1) situe cette dispersion entre registres, fichiers et supports de communication ; la nature exacte des difficultés par centre reste à confirmer par le diagnostic initial (DM § 2.1).

**Situation de départ du centre pilote.** Au CAEF Cameroun (Dixinn), tout est à construire : les données sont tenues sur papier (livrets, feuilles volantes), sans système existant, et les chiffres de la comptable diffèrent de ceux de la responsable du centre (constat du porteur de projet, 12/10/2026). La source unique et le rapprochement mensuel (section 6.11) répondent à ce second constat ; la reprise des données est une saisie des registres papier (MIG-01, SRC-03), et l'équipement comme la formation sont des conditions d'entrée du pilote.

**Financement du pilote.** TIKA (Agence turque de coopération et de coordination) est envisagée comme partenaire qui offrirait aux CAEF la réalisation et le démarrage du pilote. Cette offre reste à confirmer, avec ce qu'elle prend en charge : développement, hébergement initial, équipements, formation, accompagnement (H8).

**Vision.** Devenir le socle numérique de gestion et de pilotage du réseau national des CAEF, en passant d'une gestion documentaire ou fragmentée à une gestion fondée sur des données fiables, des processus formalisés et des responsabilités claires (DM § 2.3).

**Proposition de valeur par public :**

| Public | Ce que CAEF Connect lui apporte |
| --- | --- |
| Centre | Un dossier unique par bénéficiaire, des sessions et des présences suivies sans double saisie, des rapports produits sans ressaisie |
| Direction Générale | Des indicateurs nationaux définis, consolidés et reliés à leurs sources |
| Équipe RSE et partenariats | Un pipeline suivi de la prospection au rapport d'impact, avec une séparation nette entre promis, signé, reçu et exécuté |
| Partenaires (indirectement) | Des rapports crédibles, chiffrés et justifiés sur l'usage de leurs contributions |

**Principe produit structurant.** Une proposition ne vaut pas convention, une convention ne vaut pas encaissement, un encaissement ne vaut pas preuve d'exécution (DM § 9.3). Ce principe traverse tout le produit : chaque statut, indicateur et rapport distingue le déclaré du vérifié.

## 3. Objectifs produit et indicateurs de réussite

Le MVP réussit s'il démontre trois choses dans le centre pilote : un centre gère ses bénéficiaires et ses formations, un partenariat RSE est suivi de bout en bout, et la Direction Générale consulte des données consolidées fiables (DM § 23).

| Objectif MVP | Objectifs stratégiques couverts | Indicateurs de réussite (DM § 18) |
| --- | --- | --- |
| O1. Un centre gère ses bénéficiaires et ses formations dans l'outil | OS1, OS2, OS3, OS4 | Taux de dossiers complets ; taux de doublons détectés ; part des sessions dont les présences sont saisies ; temps moyen de traitement d'une inscription |
| O2. Un partenariat RSE est suivi de la prospection à la contribution reçue | OS5 | Nombre de prospects qualifiés ; propositions soumises ; taux de conversion ; montants signés et effectivement encaissés ; valeur des contributions en nature |
| O3. La Direction Générale consulte des indicateurs consolidés et traçables | OS7, OS8 | Part des indicateurs du tableau de bord dotés d'une fiche validée ; temps de production d'un rapport ; taux de rapports transmis dans les délais |
| O4. Les équipes adoptent l'outil | Transverse | Utilisateurs actifs par centre ; taux d'utilisation des modules ; taux de réalisation des formations utilisateurs |
| O5. Les données sont protégées et traçables | Principes 4.3, 4.4, 4.6 | Zéro accès inter-centres non autorisé en recette ; 100 % des actions sensibles journalisées ; restauration de sauvegarde testée avec succès |

Les valeurs cibles ne sont pas fixées ici : elles seront définies après établissement d'une situation de référence pendant le diagnostic (DM § 18). OS6 (insertion et entrepreneuriat) n'est pas un objectif du MVP ; il est traité en évolution (section 5).

## 4. Utilisateurs et personas

Le MVP sert onze profils internes, calés sur l'organigramme des centres (Matrice § 2.1), plus la gérante de la salle d'exposition et de la boutique, active au pilote avec le module boutique (lot 1) ; le partenaire externe n'a pas d'accès dans la première version. Ces profils reprennent les huit profils du DM § 7, plus deux demandés par le porteur de projet (responsable adjoint et comptable de centre) et le chef matériels de l'organigramme ; à l'écran, chaque rôle porte l'intitulé de l'organigramme (assistante du responsable, chef comptable, moniteur, gérante) ; le CDC en ajoute trois, qui n'arrivent qu'avec leurs modules (écart A10).

| Profil | Besoin principal dans le MVP | Portée des données | MVP |
| --- | --- | --- | --- |
| Administrateur national (technique, CDC) | Créer centres, comptes et rôles ; consulter les journaux | Technique ; contenu nominatif seulement si autorisé | Oui |
| Direction Générale | Consulter le tableau de bord national, valider les rapports consolidés | Tous centres, agrégé par défaut | Oui |
| Responsable de centre | Piloter l'activité du centre, valider, produire les rapports | Son centre | Oui |
| Responsable adjoint de centre (porteur de projet) | Seconder le responsable de centre : mêmes droits de consultation, création, modification et export ; valide seulement pendant un intérim déclaré (USR-09), sauf inventaires et ajustements de stock de la boutique | Son centre | Oui |
| Assistante du responsable de centre (agent administratif) | Enregistrer candidatures et dossiers, tenir les fiches à jour | Son centre | Oui |
| Responsable pédagogique (absent de l'organigramme ; fonction attribuée par cumul) | Planifier les sessions, affecter les formateurs, contrôler les présences | Son centre | Oui |
| Moniteur, enseignant ou encadreur (formateur) | Voir ses sessions, saisir les présences, souvent sur téléphone | Ses sessions affectées | Oui |
| Responsable RSE et partenariats | Suivre prospects, propositions, conventions et contributions | Partenaires et RSE ; données bénéficiaires agrégées seulement | Oui |
| Responsable suivi-évaluation (DM seul) | Contrôler la qualité des données, vérifier les indicateurs | Selon habilitation, national ou centre | Oui |
| Chef comptable du centre (porteur de projet) | Valider les clôtures de caisse, préparer les reversements aux productrices, exporter les journaux de la boutique, rapprocher les contributions financières reçues (CTR-09), suivre les encaissements de scolarité et rapprocher les paiements Mobile Money (PAY-10) ; aucune comptabilité générale ni paie | Son centre, ou plusieurs par cumul ; identité minimale des productrices déposantes seulement | Oui |
| Gérante de la salle d'exposition et de la boutique (porteur de projet) | Saisir les ventes, ouvrir et compter la caisse, enregistrer les entrées et sorties de stock ; ne valide ni clôture, ni inventaire, ni reversement | La salle d'exposition et la boutique de son centre ; aucune fiche bénéficiaire | Oui, si le module est activé pour le centre (lot 1) |
| Chef matériels (organigramme) | Consulter le centre, les sessions, les services et le registre des appareils ; suivre plus tard les matériels et équipements (ADM-07) | Son centre ; aucune fiche bénéficiaire | Oui, en consultation |
| Responsable insertion (CDC seul) | Suivre les bénéficiaires après formation | Son centre | Non, avec le module insertion (P2) |
| Responsable communication (CDC seul) | Publier actualités et contenus autorisés | Contenus publics | Non, écart A4 |
| Partenaire externe | Consulter ses conventions et rapports | Ses propres informations | Non, P3 |
| Apprenante ou bénéficiaire (CDC seul) | Consulter son profil et son parcours | Son propre dossier | Non, écart A11 |
| Cheffe de classe (organigramme, une élève) | Aucun compte : bénéficiaire désignée sur son inscription, mentionnée sur la feuille de présence | — | Non, sans compte au MVP |

**Contraintes d'usage à retenir pour la conception :**

- Utilisateurs non spécialistes : parcours guidés, messages d'erreur explicites, interface en français (DM § 11.2).
- Connectivité variable selon les centres : les écrans de terrain fonctionnent sans Internet et se synchronisent seuls au retour du réseau (OFF-01 à OFF-08) ; pages légères et état de synchronisation visible (DM § 11.3).
- Saisie des présences par les formateurs sur téléphone : c'est le parcours mobile prioritaire.
- Un utilisateur peut être affecté à plusieurs centres si cela est autorisé (DM § 6, module 2).
- Paiement de la scolarité : les bénéficiaires et leurs familles paient souvent par Mobile Money, depuis leur téléphone et parfois loin du centre (section 6.12).

## 5. Périmètre MVP et hors périmètre

Le MVP couvre les dix lots du DM § 23, plus le module boutique demandé par le porteur de projet (lot 11, livré dans le lot 1 : H14 tranchée le 12/10/2026) et le module scolarité et paiements demandé le 13/10/2026 (lot 12) ; il reste une proposition, réductible selon les ressources et le diagnostic (hypothèse H3). Le CDC décrit un périmètre cible de 15 modules sans fixer le premier lot (CDC § 10) ; ce PRD s'aligne donc sur le DM pour le MVP. Si une réduction s'impose, les lots marqués « Noyau » sont conservés en priorité, car ce sont eux qui démontrent les trois objectifs O1 à O3.

| Lot MVP (DM § 23) | Domaine (DM § 5) | Noyau | Ce qui est inclus | Ce qui est reporté |
| --- | --- | --- | --- | --- |
| 1. Centres et utilisateurs | 1, 2 | Oui | Référentiel des centres, comptes, rôles, cloisonnement, référentiels de base | Délégations temporaires, modèles de documents avancés |
| 2. Bénéficiaires | 3 | Oui | Fiche, candidature, validation, détection des doublons, historique | Fusion assistée avancée, suivi post-parcours |
| 3. Formations, inscriptions, présences | 4 | Oui | Catalogue, sessions, formateurs, inscriptions, présences, statuts d'achèvement | Évaluations détaillées, attestations générées, évaluation par les participantes |
| 4. Partenaires et opportunités RSE | 6, 7.1 | Oui | Fiche partenaire, interlocuteurs, interactions, pipeline en 15 étapes | Catalogue d'offres RSE, diagnostic partenaire structuré |
| 5. Propositions et conventions | 7.4, 7.5, 7.7 | Oui | Propositions versionnées, circuit de validation, conventions, engagements, échéances | Gestion fine des livrables, renouvellements automatisés |
| 6. Contributions | 7.6 | Oui | Enregistrement par nature, promis vs reçu, justificatifs, validation | Rapprochement comptable au-delà de la référence de pièce (CTR-09), affectation multi-programmes |
| 7. Tableau de bord de centre | 10.2 | Non | Indicateurs du centre, alertes, rapports à transmettre | Personnalisation des vues |
| 8. Tableau de bord national | 10.1 | Oui | Indicateurs validés uniquement, consolidés et traçables | Indicateurs sans fiche validée, répartition territoriale fine |
| 9. Reporting de base | 10, 14 | Non | Exports et rapports périodiques simples, tableau de bord RSE de base | Rapports d'impact complets, modèles avancés |
| 10. Sécurité, sauvegardes, journalisation | 11, 12 | Oui | Contrôle d'accès, journal d'activité, sauvegardes testées | Supervision avancée |
| 11. Boutique et salle d'exposition (porteur de projet) | Hors DM (PP) | Non | Noyau boutique BOU-01 à BOU-06 (catalogue, entrées en stock, ventes et reçus numérotés, stock calculé, clôture de caisse, annulation par contre-écriture) ; BOU-07 à BOU-11 (inventaire, reversements aux productrices, volet boutique du tableau de bord de centre, exports, historique des prix) ; salle d'exposition (BOU-15) ; module désactivable par centre (ADM-08) | Consolidation nationale (BOU-12), codes-barres, plusieurs points de vente, ventes en événement (BOU-13), coût de revient, marge et vente en ligne (BOU-14) ; règlements Mobile Money par le module paiements (lot 12) |
| 12. Scolarité et paiements (porteur de projet, 13/10/2026) | Hors DM (PP) | Non | Services payants et tarifs, échéances, exonérations, encaissements en espèces et Mobile Money (demande de paiement, paiement avec référence, déclaration hors ligne), reçus, rapprochement quotidien, remboursements (PAY-01 à PAY-11) | Reversements aux productrices payés par Mobile Money (PAY-12, P2) ; carte bancaire et autres paiements électroniques (PAY-13, P3) |

**Hors périmètre du MVP (P2 ou P3) :**

- Module 5 complet, programmes et projets : seule une fiche programme minimale existe dans le MVP, pour rattacher conventions et contributions (P2).
- Module 8, insertion professionnelle et entrepreneuriat (P2).
- Module 9, bibliothèque documentaire complète ; le MVP ne stocke que les pièces justificatives liées aux dossiers (P2).
- Catalogue officiel des offres RSE et diagnostic partenaire (P2).
- Portail partenaire externe (P3).
- Gestion budgétaire et comptable étendue (P3, sauf décision contraire, hypothèse H6).
- Calcul de commissions de prestataires (P3, exclu par DM § 7.9).
- Reversements aux productrices payés par Mobile Money depuis l'outil (P2, PAY-12) ; paiement par carte bancaire ou autre moyen électronique (P3, PAY-13).
- Crèche et garde d'enfants : hors MVP, prévue plus tard (lot 3 ou cycle suivant), après validation préalable des données d'enfants (A3 tranchée le 12/10/2026 ; DM § 5).
- Boutique : consolidation nationale des indicateurs (P2, BOU-12) ; lecteur de codes-barres, plusieurs points de vente par centre, ventes lors d'événements (P2, BOU-13).
- Boutique : coût de revient et marge par produit, vente en ligne (P3, BOU-14) ; le Mobile Money passe par le module paiements (section 6.12), un virement ou un chèque est déclaré avec sa référence.
- Intégrations avec des systèmes tiers autres que la passerelle Mobile Money (P3, sauf décision contraire, hypothèse H9).

**Exclusions explicites du CDC (§ 3.2), reprises comme proposition (écart A6) :** paiement électronique intégré, octroi automatisé de crédits, comptabilité générale complète, gestion de la paie, système national d'identité numérique, certification juridique automatisée des documents, application native distincte par centre, interconnexion automatique avec des systèmes non encore identifiés. Le DM ne les exclut pas nommément, mais aucune n'apparaît dans son MVP. Depuis le 13/10/2026, le paiement Mobile Money de la scolarité, des services associés et des ventes de la boutique sort de cette liste à la demande du porteur de projet (section 6.12) ; les autres paiements électroniques restent exclus.

**Modules du CDC sans équivalent dans le MVP :** crèches (M11, écart A3), communication publique (M12, écart A4), notifications et rappels (M15, écart A5, partiellement couvert par NOT-01) et parcours d'autonomisation (M06, écart A9).

### 5.1 Découpage en lots de livraison

Le plan de déploiement ordonne la livraison en trois priorités (§ 5) ; le PRD les reprend comme lots 1 à 3. Un lot dit quand une fonction est livrée, la priorité P0 à P3 dit si elle est indispensable : les deux restent distincts.

| Lot | Contenu (plan § 5) | Exigences du PRD | Phase de réalisation (plan § 4) |
| --- | --- | --- | --- |
| Lot 1, socle opérationnel (priorité 1) | Utilisateurs et permissions, centres, bénéficiaires, formations, inscriptions, présences et résultats, rapports essentiels, gestion documentaire de base, sécurité, sauvegardes, journalisation, application de terrain hors ligne et synchronisation | ADM, USR, BEN-01 à BEN-13, FOR, TDB-01 à TDB-04, TDB-09, REP-01 à REP-03, DOC-01, MIG-01, SRC-03, exigences non fonctionnelles P0 dont le hors ligne d'abord (OFF-01 à OFF-08) | Phase 3 (mois 5 à 8), piloté en phase 5 |
| Lot 1, RSE et partenaires (A14 tranchée) | Partenaires, pipeline, propositions, conventions, contributions, tableau de bord RSE | PAR, CNV, CTR, TDB-05, REP-04, REP-06 | Fin de phase 3, après le socle ; piloté en phase 5 |
| Lot 1, boutique (demande du porteur de projet, H14 tranchée) | Catalogue, stock, ventes, caisse, inventaire, reversements aux productrices, volet boutique du tableau de bord de centre | BOU-01 à BOU-06 (noyau, P0), BOU-07 à BOU-11 et BOU-15 (P1), SRC-01, SRC-02, SRC-04 ; BOU-12 au lot 2 | Fin de phase 3, après le socle et en parallèle de la RSE ; piloté en phase 5 |
| Lot 1, scolarité et paiements (demande du porteur de projet du 13/10/2026) | Services payants, échéances, exonérations, encaissements en espèces et Mobile Money, rapprochement, remboursements | PAY-01 à PAY-11 (P1), SEC-14 ; facturation de la scolarité et parcours Mobile Money avec passerelle mis en service dès que H15 et H16 sont tranchées | Fin de phase 3, avec la boutique ; déclaration des paiements Mobile Money dès le pilote, parcours avec passerelle au plus tôt pendant le pilote |
| Lot 2, accompagnement et impact (priorité 2) | Parcours d'autonomisation, insertion, entrepreneuriat, reporting d'impact | BEN-14, INS-01, REP-05, BOU-12, modules 5 et 8 du DM | Phase 6 (mois 14 à 18) |
| Lot 3, extension et optimisation (priorité 3) | Portails bénéficiaire et partenaire, crèches, notifications avancées, automatisations, intégrations externes, analytique avancée | Exigences P3 ; notifications par courriel et SMS | Phase 7 (mois 19 à 24) ou cycle suivant |

**RSE et boutique dans le pilote (A14 et H14 tranchées le 12/10/2026).** La RSE et la boutique font partie du MVP livré pour le pilote, dans le lot 1 : elles sont construites après le socle, en parallèle, et l'objectif O2 est mesuré pendant le pilote. Le noyau boutique (BOU-01 à BOU-06) est en P0 ; BOU-07 à BOU-11 restent en P1, attendues au pilote, et le rôle VB y est actif. Ces décisions du porteur de projet restent à formaliser par la Direction Générale.

**Hors ligne et Mobile Money (demandes du 13/10/2026).** Le hors ligne d'abord est une exigence d'architecture : il se construit dès le lot 1, avec les premiers écrans de saisie, car l'ajouter après coup obligerait à les réécrire. Le module paiements, son modèle de données et la déclaration d'un paiement Mobile Money sans réseau (PAY-07) sont aussi construits au lot 1 ; la facturation de la scolarité et les parcours avec passerelle (PAY-05, PAY-06) sont mis en service dès que la politique tarifaire (H15) et le choix de la passerelle et du compte marchand (H16) sont arrêtés, au plus tôt pendant le pilote, sans migration de données. Ces demandes restent à formaliser par la Direction Générale.

## 6. Exigences fonctionnelles priorisées

Le MVP compte 110 exigences fonctionnelles (63 P0, 47 P1) réparties en onze domaines, dont dix issues du CDC et du plan de déploiement (section 6.9) et trente du porteur de projet (USR-09, ADM-08, CTR-09, BOU-01 à BOU-11 et BOU-15 en section 6.10, SRC-01 à SRC-04 en section 6.11, PAY-01 à PAY-11 en section 6.12) ; les P2 sont listées pour montrer la trajectoire, pas pour être construites. Le détail des écrans, champs et règles sera décrit dans la SFD.

### 6.1 Centres, utilisateurs et habilitations

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| ADM-01 | Créer, modifier et désactiver un centre, doté d'un identifiant unique | P0 | M1, M2 |
| ADM-02 | Gérer les référentiels nationaux (catégories de programmes, types de documents, statuts, motifs de clôture), administrés par la Direction Générale | P0 | M1 |
| ADM-03 | Paramétrer les années, périodes et campagnes de formation | P0 | M1 |
| ADM-04 | Historiser toute modification d'un référentiel ou d'un paramètre structurant | P0 | M1 |
| ADM-05 | Rattacher les centres à une organisation territoriale | P1 | M1 |
| ADM-06 | Autoriser des paramètres locaux de centre non contradictoires avec les règles nationales | P2 | M1 |
| ADM-08 | Activer ou désactiver, par centre et sur décision datée de la Direction Générale, les modules optionnels : boutique et salle d'exposition, ou la seule salle d'exposition, scolarité et paiements, volet RSE du centre, puis les modules à venir ; un module désactivé disparaît des menus, est refusé côté serveur (API et synchronisation comprises), garde ses données en lecture seule et s'affiche « Module non activé » dans les tableaux de bord et la clôture mensuelle, jamais comme un zéro | P0 | PP |
| USR-01 | Créer des comptes personnels et nominatifs, non partageables | P0 | M2 |
| USR-02 | Affecter un utilisateur à un ou plusieurs centres, si autorisé | P0 | M2 |
| USR-03 | Attribuer des rôles selon le moindre privilège, définis par action (consulter, créer, modifier, valider, exporter, archiver) | P0 | M2, § 8 |
| USR-04 | Cloisonner les données : aucun accès automatique aux dossiers d'un autre centre | P0 | § 4.3 |
| USR-05 | Réinitialiser un accès de façon sécurisée | P0 | M2 |
| USR-06 | Désactiver un compte sans supprimer l'historique de ses actions | P0 | M2 |
| USR-07 | Journaliser les changements de permissions ; consulter connexions et actions sensibles | P0 | M2 |
| USR-08 | Gérer des délégations temporaires | P2 | M2 |
| USR-09 | Déclarer un intérim du responsable de centre au profit de son adjoint : dates, motif, trace ; les droits de validation du RC s'appliquent au RA pendant cette période seulement | P1 | PP |

**Critère d'acceptation clé :** un utilisateur du centre A ne peut ni voir, ni rechercher, ni exporter une fiche du centre B, par l'interface comme par l'API.

### 6.2 Bénéficiaires

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| BEN-01 | Tenir une fiche bénéficiaire à identifiant interne stable, limitée aux champs validés ; aucune donnée sensible collectée par défaut | P0 | M3 § 3.1 |
| BEN-02 | Enregistrer une candidature | P0 | M3 § 3.2 |
| BEN-03 | Vérifier la complétude (champs obligatoires, contrôles de cohérence) | P0 | M3, § 4.5 |
| BEN-04 | Valider ou rejeter une candidature, avec motif obligatoire en cas de rejet | P0 | M3 § 3.2 |
| BEN-05 | Rechercher un dossier existant avant toute création et signaler les doublons potentiels | P0 | M3 § 3.3, § 9.1 |
| BEN-06 | Historiser chaque changement de statut avec date et auteur | P0 | M3 |
| BEN-07 | Afficher le parcours chronologique (candidature, inscription, formation, attestation ; étapes suivantes quand les modules seront actifs) | P0 | M3 § 3.4 |
| BEN-08 | Importer de façon contrôlée les données existantes du centre pilote (registres papier saisis, voir MIG-01 et SRC-03), avec rapport d'anomalies et trace de migration | P0 | § 16 ph. 4, risque 2 |
| BEN-09 | Fusionner deux dossiers par un utilisateur habilité, jamais automatiquement, avec trace | P1 | M3 § 3.3 |
| BEN-10 | Transférer un dossier vers un autre centre sans en créer un nouveau | P1 | M3 § 3.5 |
| BEN-11 | Gérer une liste d'attente | P1 | M3 § 3.2 |
| BEN-12 | Joindre des pièces justificatives autorisées, à accès restreint | P1 | M3 § 3.1 |
| BEN-13 | Archiver logiquement les dossiers clôturés | P1 | M3 § 3.2 |

**Critère d'acceptation clé :** la saisie d'une personne déjà enregistrée, selon les critères de rapprochement validés, déclenche une alerte avant création, et aucun dossier n'est fusionné sans action humaine.

### 6.3 Formations, inscriptions et présences

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| FOR-01 | Tenir le catalogue des formations et leurs objectifs pédagogiques | P0 | M4 |
| FOR-02 | Créer des sessions rattachées à une formation, un centre et une période, avec dates, horaires et lieux | P0 | M4 |
| FOR-03 | Tenir les fiches formateurs et les affecter aux sessions | P0 | M4 |
| FOR-04 | Gérer la capacité d'accueil et alerter en cas de dépassement | P0 | M4 |
| FOR-05 | Inscrire des bénéficiaires validées à une session | P0 | M4, § 9.1 |
| FOR-06 | Saisir les présences et absences par séance, y compris sur téléphone par le formateur | P0 | M4, § 7.8 |
| FOR-07 | Suivre le statut de participation : inscrite, commencée, achevée, suspendue, abandonnée | P0 | M4 |
| FOR-08 | Saisir évaluations et résultats, toute modification étant tracée | P1 | M4 |
| FOR-09 | Enregistrer la délivrance d'une attestation, uniquement si les conditions du programme sont remplies | P1 | M4 |
| FOR-10 | Clôturer une session et produire son rapport | P1 | § 9.2 |
| FOR-11 | Générer le document d'attestation à partir d'un modèle validé | P2 | M4 |
| FOR-12 | Recueillir l'évaluation de la formation par les participantes | P2 | M4 |

**Critère d'acceptation clé :** les statistiques distinguent toujours les personnes inscrites, ayant commencé, ayant achevé et ayant obtenu une attestation.

### 6.4 Partenaires et pipeline RSE

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| PAR-01 | Tenir une fiche partenaire (catégorie, secteur, coordonnées institutionnelles) | P0 | M6 |
| PAR-02 | Enregistrer les interlocuteurs, limités aux coordonnées professionnelles nécessaires | P0 | M6 |
| PAR-03 | Signaler un partenaire déjà connu lors de la création | P0 | M6, § 9.3 |
| PAR-04 | Historiser interactions, rendez-vous et comptes rendus | P0 | M6 |
| PAR-05 | Créer des opportunités avec origine du contact et responsable de suivi | P0 | M6, M7 § 7.9 |
| PAR-06 | Suivre le pipeline RSE en 15 étapes paramétrables ; chaque passage est historisé avec date et auteur | P0 | M7 § 7.1 |
| PAR-07 | Qualifier le potentiel de partenariat | P1 | M6 |
| PAR-08 | Documenter les interventions de plusieurs personnes sur un même partenariat | P1 | M7 § 7.9 |
| PAR-09 | Exporter les listes de partenaires autorisées | P1 | M6 |
| PAR-10 | Tenir le catalogue officiel des offres RSE | P2 | M7 § 7.2 |
| PAR-11 | Renseigner une fiche de diagnostic partenaire structurée | P2 | M7 § 7.3 |

### 6.5 Propositions, conventions et engagements

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| CNV-01 | Créer une proposition avec identifiant, version, statut, responsable, historique et les champs du DM § 7.4 | P0 | M7 § 7.4 |
| CNV-02 | Soumettre la proposition à un circuit de validation interne paramétrable avant envoi | P0 | M7 § 7.4 |
| CNV-03 | Exiger un motif en cas de refus ou de suspension | P0 | M7 § 7.4 |
| CNV-04 | Enregistrer une convention signée, liée à sa proposition et à son partenaire, avec dates, responsables et document | P0 | M7 § 7.5 |
| CNV-05 | Définir les engagements réciproques : partie, responsable, échéance, état, justificatif, validation de réalisation | P0 | M7 § 7.7 |
| CNV-06 | Tenir une fiche programme minimale (identifiant, intitulé, centres, responsable, période, statut) pour y rattacher conventions et contributions | P0 | M5 |
| CNV-07 | Alerter avant échéance et afficher les engagements en retard sur le tableau de bord du responsable | P1 | M7 § 7.5, 7.7 |
| CNV-08 | Clôturer une convention, qui reste consultable selon les droits | P1 | M7 § 7.5 |
| CNV-09 | Suivre les livrables et les renouvellements | P2 | M7 § 7.5 |

### 6.6 Contributions

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| CTR-01 | Enregistrer une contribution selon l'une des huit natures du DM § 7.6 | P0 | M7 § 7.6 |
| CTR-02 | Renseigner partenaire, convention, programme, centre, date, valeur déclarée, justificatifs | P0 | M7 § 7.6 |
| CTR-03 | Distinguer les statuts promise, reçue et validée ; une contribution promise n'est jamais comptée comme reçue | P0 | M7 § 7.6 |
| CTR-04 | Séparer contributions financières et en nature dans tous les totaux | P0 | M7 § 7.6, § 9.5 |
| CTR-05 | Exiger un justificatif pour passer au statut validée | P0 | § 9.4, 9.5 |
| CTR-06 | Faire valider la réception par un responsable habilité, avec trace | P0 | § 9.4 |
| CTR-07 | Documenter la méthode de valorisation d'un don en nature | P1 | M7 § 7.6 |
| CTR-08 | Répartir une contribution entre plusieurs programmes sans double comptage | P2 | § 10.4 |
| CTR-09 | Permettre au comptable du centre de rapprocher une contribution financière reçue (référence de pièce comptable, date d'encaissement constatée), sans droit de validation | P1 | PP |

**Critère d'acceptation clé (6.4 à 6.6) :** pour un même partenariat, le tableau de bord affiche séparément le montant sollicité, le montant signé, le montant encaissé et la valeur des dons en nature, chacun relié à ses pièces.

### 6.7 Tableaux de bord

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| TDB-01 | Afficher au tableau de bord national uniquement les indicateurs dotés d'une fiche validée, agrégés, sans donnée nominative par défaut | P0 | M10 § 10.1, 10.4 |
| TDB-02 | Relier chaque chiffre aux données sources, consultables selon les droits | P0 | M7 § 7.8, § 14.3 |
| TDB-03 | Indiquer pour chaque indicateur sa date de mise à jour et son niveau de validation (déclaratif ou vérifié) | P0 | § 14.3 |
| TDB-04 | Fournir à chaque centre son tableau de bord : bénéficiaires, inscriptions, sessions, présences, formateurs, conventions, contributions, boutique (volet décrit en BOU-09), alertes, rapports à transmettre | P1 | M10 § 10.2 |
| TDB-05 | Fournir un tableau de bord RSE de base : prospects, rendez-vous, propositions, taux de transformation, montants proposés, signés et encaissés, dons en nature, engagements en retard | P1 | M10 § 10.3 |
| TDB-06 | Filtrer par centre, période et programme | P1 | M10 |
| TDB-07 | Gérer dans l'outil les fiches d'indicateurs (les dix rubriques du DM § 10.4) | P1 | M10 § 10.4 |
| TDB-08 | Afficher la répartition territoriale des résultats | P2 | M10 § 10.1 |

### 6.8 Reporting de base

| ID | Exigence | Priorité | DM § |
| --- | --- | --- | --- |
| REP-01 | Exporter les listes autorisées (tableur), chaque export étant journalisé | P0 | § 12.1 |
| REP-02 | Produire un rapport périodique de centre indiquant sa période et sa date de production | P1 | § 14.1 |
| REP-03 | Produire un rapport national consolidé selon le processus du DM § 9.6 et archiver la version validée | P1 | § 9.6 |
| REP-04 | Produire un rapport par partenaire : contributions et bénéficiaires soutenus, en agrégé | P1 | M7 § 7.8 |
| REP-05 | Produire des rapports d'impact complets selon la structure du DM § 14.2 | P2 | § 14.2 |

### 6.9 Compléments issus du cahier des charges et du plan de déploiement

Ces exigences viennent du CDC et du plan de déploiement, et complètent les domaines ci-dessus sans contredire le DM ; celles qui dépendent d'un écart non arbitré le signalent.

| ID | Exigence | Priorité | Source |
| --- | --- | --- | --- |
| FOR-13 | Empêcher l'ouverture d'une session sans ses informations minimales (formation, centre, période, lieu, capacité) | P0 | CDC M04 |
| FOR-14 | Verrouiller une session clôturée : toute modification exige un droit spécifique et est tracée | P0 | CDC § 8 règle 4 |
| TDB-09 | Distinguer les données manquantes des valeurs nulles dans toutes les statistiques | P0 | CDC M13 |
| REP-06 | N'utiliser dans les rapports destinés aux partenaires que les informations autorisées | P0 | CDC § 8 règle 9 |
| MIG-01 | Importer d'abord un échantillon hors production, contrôler totaux et dossiers, faire valider par les responsables métier ; marquer les données incertaines « manquante » ou « à vérifier », jamais complétées par supposition ; au centre pilote, la reprise est une saisie ou numérisation des registres papier (livrets, feuilles volantes), rapprochée selon SRC-03 | P0 | Plan § 7 |
| FOR-15 | Exporter les listes de présence et les résultats d'une session | P1 | CDC M04 |
| FOR-16 | Compléter la fiche formateur : compétences, domaines d'intervention, formations dispensées, données proportionnées | P1 | CDC M05 |
| CNV-10 | Créer une fiche projet RSE à partir d'un besoin recensé par un centre, rattachée à un objectif d'impact (selon écart A8) | P1 | CDC M10, § 6.2 |
| NOT-01 | Notifier dans l'application les demandes de validation et les échéances ; courriel et SMS seulement après validation de leur coût (écart A5) | P1 | CDC M15, DM M9 |
| DOC-01 | Rattacher des documents à un centre, une formation ou un partenaire, avec contrôle des droits (gestion documentaire de base, écart A16) | P1 | Plan § 4 ph. 3 ; CDC M14 |
| ADM-07 | Suivre les équipements, matériels, besoins et incidents des centres (fonction du chef matériels, CMT) ; module désactivable par centre (ADM-08) | P2 | CDC M02 |
| BEN-14 | Suivre un parcours d'autonomisation structuré (étapes, jalons, orientations, bilan individuel), selon écart A9 | P2 | CDC M06 |
| INS-01 | Collecter la situation professionnelle après formation à des échéances définies | P2 | CDC M07 |

### 6.10 Boutique

Le module boutique et salle d'exposition enregistre ce que le centre produit, expose et vend dans sa salle d'exposition et sa boutique, et suit le stock, les recettes et la part qui revient aux productrices (bénéficiaires ou groupements) en dépôt-vente ; les revenus générés par les bénéficiaires deviennent mesurables. Presque tous les CAEF ont une boutique, mais ni le DM ni le CDC ne décrivent ce module : il est demandé par le porteur de projet et fait partie du lot 1 livré pour le pilote (H14 tranchée le 12/10/2026).

| ID | Exigence | Priorité | Source |
| --- | --- | --- | --- |
| BOU-01 | Tenir le catalogue des produits de la boutique du centre : nom, catégorie, unité, prix de vente en vigueur, origine (atelier ou session de formation du centre, productrice en dépôt-vente, groupement, achat pour revente), statut actif | P0 | PP |
| BOU-02 | Enregistrer les entrées en stock avec origine, quantité, date et, si dépôt-vente, la productrice déposante et la part convenue pour le centre | P0 | PP |
| BOU-03 | Enregistrer une vente : lignes produits, quantités, prix, remise motivée, mode de règlement (espèces, Mobile Money confirmé par la passerelle ou déclaré avec sa référence, virement, chèque), reçu numéroté imprimable, y compris hors ligne (OFF-08) | P0 | PP |
| BOU-04 | Calculer le stock à partir des mouvements (entrées, ventes, sorties motivées : perte, don, échantillon, usage interne) et alerter sur un stock négatif ou sous un seuil | P0 | PP |
| BOU-05 | Clôturer la caisse chaque jour : montant théorique par mode de règlement, montant compté, écart motivé, validation par le comptable ou, à défaut, le RC ou RA, jamais par l'auteur des ventes | P0 | PP |
| BOU-06 | Annuler une vente ou un mouvement uniquement par contre-écriture motivée et tracée ; aucune suppression ; numérotation des reçus continue et sans trou par série (une série par appareil enrôlé sur le point de vente, OFF-08) | P0 | PP |
| BOU-07 | Réaliser un inventaire périodique : comptage, écarts, ajustement validé par le RC ou le RA | P1 | PP |
| BOU-08 | Calculer pour chaque productrice en dépôt-vente le montant dû (ventes moins part du centre), enregistrer les reversements (préparés par le comptable, validés par RC ou RA, avec date et pièce) et afficher le solde restant dû | P1 | PP |
| BOU-09 | Afficher le volet boutique du tableau de bord de centre : chiffre d'affaires par période, produit et catégorie, nombre de ventes, stock valorisé au prix de vente, ruptures, écarts de caisse, reversements dus | P1 | PP |
| BOU-10 | Exporter le journal des ventes, des clôtures de caisse et des reversements (tableur) pour la comptabilité tenue hors de l'outil, chaque export étant journalisé | P1 | PP |
| BOU-11 | Historiser les prix de vente : toute modification datée et tracée, sans effet sur les ventes passées | P1 | PP |
| BOU-15 | Gérer la salle d'exposition du centre : articles exposés, transferts entre la réserve et la salle d'exposition par mouvements tracés, stock par emplacement, vente possible depuis la salle d'exposition avec les mêmes reçus ; activable séparément de la boutique (ADM-08) | P1 | PP |
| BOU-12 | Consolider au niveau national les indicateurs boutique (agrégés, sans nom de productrice) | P2 | PP |
| BOU-13 | Lecteur de codes-barres, plusieurs points de vente par centre, ventes lors d'événements (foires, salons) | P2 | PP |
| BOU-14 | Coût de revient et marge par produit ; vente en ligne | P3 | PP |

Noyau boutique = BOU-01 à BOU-06 (vendre, encaisser, tracer). Depuis que H14 est tranchée, le noyau est en P0 : le pilote ne démarre pas sans lui. BOU-07 à BOU-11 restent en P1, attendues au pilote, et leurs cas de test sont obligatoires pour le pilote.

**Hors périmètre du module :** paiement électronique autre que le Mobile Money (A6, PAY-13), comptabilité générale, coût de revient et marge, vente en ligne, gestion des fournisseurs et achats avancée, terminal de caisse dédié, lecteur de codes-barres (P2), plusieurs points de vente par centre (P2 ; un point de vente par centre au MVP).

**Rôles et séparation des tâches.** La gérante de la salle d'exposition et de la boutique (VB, appelée vendeur ou vendeuse de boutique dans ce dossier) saisit les ventes, ouvre et compte la caisse, enregistre les entrées et sorties de stock ; le comptable de centre (CPT, double authentification obligatoire) valide les clôtures de caisse et prépare les reversements ; le responsable de centre (RC) ou son adjoint (RA) valide les inventaires et les reversements. Celui qui a saisi les ventes d'une journée ne valide pas la clôture de caisse de cette journée ; celui qui a compté un inventaire ne valide pas son ajustement ; celui qui prépare un reversement ne le marque pas « payé » s'il l'a aussi validé.

### 6.11 Source unique et rapprochement

Chaque montant est saisi une seule fois dans CAEF Connect et rapproché chaque mois, parce qu'au CAEF Cameroun les chiffres de la comptable diffèrent de ceux de la responsable du centre. Ce domaine est demandé par le porteur de projet (12/10/2026) ; il couvre les ventes, les caisses, les reversements, les contributions financières reçues et, depuis le 13/10/2026, les paiements de scolarité et de services associés.

| ID | Exigence | Priorité | Source |
| --- | --- | --- | --- |
| SRC-01 | Source unique : chaque montant (vente, encaissement de caisse, paiement de scolarité ou de service, reversement, contribution financière reçue) est saisi une seule fois dans CAEF Connect ; la vue du comptable, le tableau de bord du responsable de centre et les rapports lisent les mêmes enregistrements, sans ressaisie ni tableur parallèle | P0 | PP |
| SRC-02 | Clôture mensuelle du centre : état de rapprochement généré par l'outil (ventes, caisses, paiements de scolarité et Mobile Money rapprochés avec le relevé de l'opérateur, reversements, contributions financières reçues, sur le mois), vérifié par le comptable (CPT) puis validé par le responsable de centre (RC, ou RA en intérim) ; chaque écart avec les pièces (caisse physique, relevés, carnet de reçus) est motivé ; après validation, le mois est verrouillé et toute correction passe par une écriture datée du mois suivant | P0 | PP |
| SRC-03 | Reprise des registres papier : avant l'ouverture du pilote, inventaire des livrets et feuilles volantes ; rapprochement des chiffres de la comptable et de ceux de la responsable pour la période reprise ; les divergences non résolues sont importées avec le statut « à vérifier », jamais arbitrées par supposition (complète MIG-01) | P0 | PP |
| SRC-04 | Afficher sur le tableau de bord de centre le statut de la dernière clôture mensuelle (à faire, vérifiée, validée, avec écart motivé) | P1 | PP |

**Critère d'acceptation clé :** pour un mois donné, le comptable, le tableau de bord du responsable de centre et le rapport affichent les mêmes totaux, car ils lisent les mêmes enregistrements ; un mois validé ne se corrige plus que par une écriture de régularisation.

### 6.12 Scolarité et paiements Mobile Money

Les bénéficiaires, ou un tiers payeur, règlent la scolarité et les services associés en espèces au centre ou par Mobile Money depuis leur téléphone. Ce domaine est demandé par le porteur de projet (13/10/2026, à formaliser par la Direction Générale) ; il lève pour le seul Mobile Money l'exclusion du paiement électronique intégré (A6). CAEF Connect enregistre, affecte et rapproche les paiements, mais ne détient jamais les fonds : ils arrivent directement sur le compte marchand des CAEF (H16). La boutique utilise le même module pour ses règlements Mobile Money (BOU-03).

| ID | Exigence | Priorité | Source |
| --- | --- | --- | --- |
| PAY-01 | Tenir le catalogue des services payants (frais d'inscription, scolarité d'une session, examen ou attestation, services associés) et leurs tarifs datés, par centre et par période ; un changement de tarif est tracé et sans effet sur les échéances déjà émises | P1 | PP |
| PAY-02 | Générer les échéances d'une bénéficiaire à son inscription (montant, date limite, échéancier en plusieurs versements si le tarif le prévoit) et imprimer un avis d'échéance portant une référence de paiement unique | P1 | PP |
| PAY-03 | Enregistrer une exonération ou une prise en charge (bourse, réduction motivée, partenaire ou programme), validée par le responsable de centre, jamais par son auteur | P1 | PP |
| PAY-04 | Encaisser en espèces au centre, en ligne ou hors ligne, avec reçu numéroté, et affecter le montant à une ou plusieurs échéances | P1 | PP |
| PAY-05 | Envoyer une demande de paiement Mobile Money au téléphone de la payeuse (parcours A) ; la payeuse valide avec son code secret, jamais saisi dans CAEF Connect ; le statut s'affiche dès la notification de l'opérateur | P1 | PP |
| PAY-06 | Recevoir un paiement fait par la payeuse sur le compte marchand avec la référence de son avis d'échéance (parcours B) et l'affecter automatiquement ; sans référence valide, le placer dans la file « Paiements à affecter » du comptable | P1 | PP |
| PAY-07 | Déclarer sans réseau un paiement Mobile Money avec l'identifiant de transaction lu sur le SMS de la payeuse et remettre un reçu provisoire (parcours C) ; à la synchronisation, le confirmer ou le marquer « Non retrouvé », signalé au comptable après 24 heures | P1 | PP |
| PAY-08 | Ne compter comme encaissé qu'un paiement confirmé par l'opérateur, pour le montant confirmé par l'opérateur et jamais celui saisi ; un écart crée un paiement partiel ou un trop-perçu ; une transaction notifiée deux fois n'est comptée qu'une fois ; les paiements déclarés s'affichent à part | P1 | PP |
| PAY-09 | Afficher la situation de chaque bénéficiaire (dû, payé, exonéré, restant dû, retards) et, au tableau de bord de centre, les encaissements de scolarité par période et par canal et les impayés | P1 | PP |
| PAY-10 | Rapprocher chaque jour les paiements Mobile Money avec le relevé de l'opérateur, signaler les écarts au comptable et reprendre les totaux dans la clôture mensuelle (SRC-02) | P1 | PP |
| PAY-11 | Rembourser tout ou partie d'un paiement : demande motivée par le comptable, validation par le responsable de centre (ou le RA en intérim), jamais par la même personne ; exécution par la passerelle ou hors outil avec pièce justificative | P1 | PP |
| PAY-12 | Payer par Mobile Money, depuis l'outil, les reversements aux productrices en dépôt-vente | P2 | PP |
| PAY-13 | Carte bancaire et autres moyens de paiement électronique | P3 | PP |

**Critère d'acceptation clé :** un paiement Mobile Money n'est compté comme encaissé qu'après confirmation de l'opérateur ; le même paiement notifié deux fois n'est compté qu'une fois ; chaque paiement confirmé du mois figure dans le relevé de l'opérateur ou parmi les écarts motivés de la clôture mensuelle.

**Mise en service.** Le module, son modèle de données et la déclaration sans réseau (PAY-04, PAY-07 à PAY-11) sont construits au lot 1. La facturation de la scolarité (PAY-01 à PAY-03) et les parcours avec passerelle (PAY-05, PAY-06) sont mis en service dès que la politique tarifaire (H15) et le choix de la passerelle (H16) sont arrêtés, au plus tôt pendant le pilote.

**Rôles et séparation des tâches.** L'agent administratif et le comptable encaissent et envoient les demandes de paiement ; le vendeur ou la vendeuse de boutique encaisse les ventes ; le comptable affecte les paiements sans référence, rapproche et demande les remboursements ; le responsable de centre (ou le RA en intérim) valide exonérations et remboursements ; les tarifs sont saisis par l'administrateur sur décision de la Direction Générale (H15).

**Hors périmètre du domaine :** reversements payés par Mobile Money (PAY-12, P2), carte bancaire et autres paiements électroniques (PAY-13, P3), crédit ou paiement échelonné avec intérêts, comptabilité générale.

## 7. Exigences non fonctionnelles

La sécurité, la traçabilité et l'usage sans connexion sont des exigences P0 du MVP ; depuis le 13/10/2026, le fonctionnement hors ligne d'abord avec synchronisation automatique est une exigence d'architecture (OFF-01 à OFF-08). Ces exigences s'appuient sur le DM (§ 11 à 13) et sur le Dossier d'architecture technique v1.0 (DAT), qui reste une architecture cible à valider. Les valeurs chiffrées (disponibilité, temps de réponse, RPO, RTO) ne sont pas fixées ici : les deux documents demandent qu'elles le soient après étude des usages, des coûts et des risques.

| ID | Exigence | Priorité | Source |
| --- | --- | --- | --- |
| SEC-01 | Contrôler l'accès selon les rôles et le périmètre, et cloisonner les centres, côté serveur pour chaque requête | P0 | DM § 12.1 ; DAT § 4 |
| SEC-02 | Sécuriser les sessions (expiration, déconnexion) ; HTTPS obligatoire | P0 | DM § 12.1 ; DAT § 3 |
| SEC-03 | Chiffrer les sauvegardes et les données stockées lorsque l'outil le permet ; aucun document confidentiel accessible par lien public | P0 | DM § 12.1 ; DAT § 6.2 |
| SEC-04 | Journaliser les accès et actions sensibles (création, modification, validation, export, changement de droits) avec horodatage et auteur | P0 | DM § 4.4 ; DAT § 6.2 |
| SEC-05 | Sauvegarder automatiquement, hors de l'environnement principal, avec protection contre la suppression accidentelle ; restauration testée avant le pilote puis périodiquement | P0 | DM § 12.3 ; DAT § 7 |
| SEC-06 | Révoquer rapidement un compte compromis ou un utilisateur sortant | P0 | DM § 12.1 ; DAT § 6.1 |
| SEC-07 | Ne jamais copier de données réelles de bénéficiaires en développement ou préproduction sans anonymisation | P0 | DM § 11.5 ; CDC § 8 |
| SEC-08 | Appliquer une politique de mots de passe et bloquer les tentatives répétées de connexion | P0 | DAT § 6.1 |
| SEC-09 | Stocker secrets et clés dans un coffre sécurisé, jamais dans le code | P0 | DAT § 3, 6.2 |
| SEC-10 | Appliquer aux exports les mêmes règles d'accès que l'application | P0 | DAT § 4 |
| SEC-11 | Exiger l'authentification multifacteur pour les comptes privilégiés, si techniquement possible | P1 | DAT § 6.1 |
| SEC-12 | Revoir périodiquement les droits attribués | P1 | DAT § 6.1 |
| SEC-13 | Enregistrer les incidents de sécurité selon les rubriques du DM § 12.4 | P1 | DM § 12.4 |
| SEC-14 | Authentifier chaque notification de la passerelle de paiement (signature, origine) et ne la traiter qu'une fois ; ne jamais prendre de l'appareil de l'utilisateur le montant ou le statut d'un paiement ; aucun code secret de la payeuse dans l'outil | P1 | PP ; DAT détaillé § 5.6 |
| DAT-01 | Ne jamais utiliser le numéro de téléphone comme identifiant permanent d'une personne, y compris pour la détection des doublons (BEN-05) | P0 | DAT § 5.3 |
| DAT-02 | Normaliser dates et statuts, documenter chaque champ, permettre une correction contrôlée et tracée | P0 | DAT § 5.3 |
| UX-01 | Interface en français, responsive sur ordinateur, tablette et téléphone, organisée par rôle | P0 | DM § 11.2 |
| UX-02 | Libellés et messages d'erreur explicites ; formulaires adaptés aux utilisateurs peu expérimentés ; recherches, filtres et tris | P0 | DM § 11.2 ; DAT § 8 |
| UX-03 | Contrastes et navigation accessibles autant que possible ; compatibilité avec les navigateurs retenus | P1 | DAT § 8, 12 |
| NET-01 | Pages légères, transferts limités, état de connexion visible | P0 | DM § 11.3 |
| NET-02 | Gestion des erreurs réseau et reprise contrôlée d'une saisie interrompue, sans perte ni doublon | P0 | DM § 11.3 |
| OFF-01 | Hors ligne d'abord : les écrans de terrain (présences, candidatures et mises à jour de dossiers, ventes, mouvements de stock, caisse, encaissements, déclarations de paiement) fonctionnent sans Internet dans une application web installable (PWA) ; les fonctions qui exigent le serveur (validations, exports, tableau de bord national, demande de paiement) sont signalées « en ligne seulement » | P0 | PP |
| OFF-02 | Synchroniser automatiquement au retour du réseau, à l'ouverture de l'application et à intervalle régulier, sans action de l'utilisateur ; un bouton « Synchroniser maintenant » reste disponible | P0 | PP |
| OFF-03 | Aucune perte ni aucun doublon : chaque saisie faite sans réseau reste sur l'appareil jusqu'à l'accusé du serveur, et une opération reçue deux fois n'est appliquée qu'une fois | P0 | PP ; DM § 11.3 |
| OFF-04 | Le serveur revérifie chaque opération reçue (droits, périmètre, règles métier) comme une saisie en ligne ; une opération refusée revient à l'utilisateur avec son motif | P0 | PP ; DAT § 4 |
| OFF-05 | Résoudre les conflits selon des règles écrites (ajout seul sans conflit, fusion champ par champ, dernière présence saisie retenue) ; un vrai conflit attend une décision humaine dans une file « À résoudre », sans écrasement silencieux | P0 | PP |
| OFF-06 | Protéger l'appareil : enrôlement et révocation par le centre, mode hors ligne réservé aux rôles de terrain, base locale chiffrée et code personnel, données limitées au rôle et au périmètre, aucun champ restreint, durée maximale sans reconnexion paramétrable (72 heures proposées) | P0 | PP ; DM § 12.1 |
| OFF-07 | Afficher en permanence l'état de synchronisation (à jour, opérations en attente, dernière synchronisation, rejets et conflits) et signaler au responsable de centre un appareil qui garde des opérations en attente depuis plus de 48 heures | P0 | PP |
| OFF-08 | Numéroter les reçus sur l'appareil, par série propre à chaque appareil et sans trou ; conditionner le comptage de caisse et la clôture mensuelle à la synchronisation des appareils concernés | P0 | PP |
| PERF-01 | Paginer les listes volumineuses et indexer les champs fréquemment recherchés | P0 | DAT § 8 |
| PERF-02 | Exécuter statistiques et rapports sans dégrader les opérations quotidiennes | P0 | DAT § 3, 8 |
| PERF-03 | Valider la fluidité sur les équipements et connexions réels du centre pilote par des tests de charge, sur des hypothèses de capacité écrites (centres, utilisateurs, bénéficiaires, documents, sessions) | P1 | DM § 13.2 ; DAT § 8 |
| ARC-01 | Architecture modulaire par domaine métier, permettant d'ajouter centres, utilisateurs et modules sans refonte | P0 | DM § 11.1 ; DAT § 2 |
| ARC-02 | L'interface n'accède jamais directement à la base ; tout passe par l'API et les services métier | P0 | DAT § 4 |
| ARC-03 | Environnements séparés de développement, préproduction (recette, formation) et production | P0 | DM § 11.5 ; DAT § 10 |
| ARC-04 | Base relationnelle pour les données métier, stockage documentaire séparé pour les fichiers | P1 | DAT § 3 |
| ARC-05 | API documentée, versionnée, authentifiée, avec validation des entrées, limitation des appels et environnement de test | P1 | DM § 11.4 ; DAT § 9 |
| MNT-01 | Code versionné ; tests automatisés sur les fonctions critiques ; documentation d'installation et d'API | P0 | DM § 13.4 ; DAT § 8 |
| MNT-02 | Procédure de livraison contrôlée et de retour arrière | P0 | DAT § 8, 10 |
| MNT-03 | Propriété institutionnelle des données ; export complet dans des formats documentés (réversibilité) ; remise du code source et inventaire des composants et licences | P0 | DM risque 6 ; DAT § 2, 13 |
| OPS-01 | Supervision de la disponibilité et des erreurs | P1 | DAT § 3 |
| DISP-01 | Objectif de disponibilité, plages de maintenance, RPO et RTO fixés et validés avant la mise en production | P1 | DM § 13 ; DAT § 7, 8 |

**Contraintes d'architecture (DAT § 2 à 4).** Le flux de référence est : utilisateur, interface web, API et services métier, puis base de données et stockage documentaire. Une application structurée en modules est privilégiée ; des microservices ne seraient retenus que si la charge ou l'organisation le justifient. Aucun langage, framework, fournisseur ni pays d'hébergement n'est imposé à ce stade (hypothèses H7, H12 et H13). Le client de terrain est une application web installable (PWA) qui fonctionne hors ligne et se synchronise avec l'API (H11, H12).

**Conditions minimales de mise en service du pilote (DAT § 12) :**

- [ ] Aucune vulnérabilité critique non traitée.
- [ ] Parcours métier prioritaires validés de bout en bout.
- [ ] Rôles et permissions vérifiés, y compris les accès directs non autorisés.
- [ ] Restauration testée.
- [ ] Documentation d'exploitation et plan de support disponibles.
- [ ] Validation formelle de la Direction.
- [ ] Centre pilote équipé (ordinateurs, tablettes ou téléphones, imprimante, imprimante de reçus, connectivité, onduleur) et utilisateurs formés (porteur de projet).
- [ ] Appareils de terrain enrôlés et synchronisation testée après plusieurs jours sans réseau, sans perte ni doublon (OFF-02, OFF-03).
- [ ] Si les paiements Mobile Money avec passerelle sont mis en service : contrat marchand signé, avis juridique rendu, rapprochement testé dans l'environnement de test de l'opérateur (H16, PAY-10).

**Protection des données personnelles.** Avant la mise en service, il faut déterminer avec une compétence juridique : les règles applicables en Guinée, le responsable du traitement, les finalités et bases légitimes, l'information et les droits des personnes, les durées de conservation, les conditions de partage avec les partenaires et les formalités réglementaires (DM § 12.2 ; DAT § 6.3). Cette validation conditionne le lancement du pilote.

## 8. Hypothèses et points à arbitrer

Ce PRD repose sur seize hypothèses de travail, dont dix reprennent les décisions ouvertes du DM § 22, deux les décisions techniques du DAT § 14 une la demande boutique du porteur de projet (H14) et deux les demandes du 13/10/2026 (H15, H16), et sur seize écarts entre les documents sources ; le porteur de projet en a tranché quatre le 12/10/2026 (A1, A3, A14, H14), et ses demandes du 13/10/2026 modifient H9, H11, H12 et A6, le tout à formaliser par la Direction Générale ; les autres restent ouverts. Les décisions ouvertes du CDC (§ 10) recoupent ces deux listes. Chacune doit être confirmée ou corrigée par l'instance indiquée avant le démarrage du développement, et le PRD sera révisé en conséquence.

### 8.1 Hypothèses de travail

| ID | Décision ouverte | Hypothèse de travail du PRD | Effet si elle est invalidée | Instance qui tranche |
| --- | --- | --- | --- | --- |
| H1 | Autorité institutionnelle (D1) | La Direction Générale des CAEF porte la plateforme et est responsable du traitement des données | Revoir les mentions légales, les contrats techniques et le registre des traitements | Direction Générale |
| H2 | Centre pilote (D2) | Tranché le 12/10/2026 par le porteur de projet, à formaliser par la Direction Générale : pilote dans un seul centre, le CAEF Cameroun à Dixinn ; extension à d'autres centres par vagues après le bilan du pilote (section 9.2) | Si la Direction Générale retient un autre centre : diagnostic, reprise des registres et formation à refaire | Comité de pilotage |
| H3 | Processus prioritaires (D3) | Les cinq processus prioritaires sont : inscription d'une bénéficiaire, création d'une session et saisie des présences, suivi d'une opportunité RSE, enregistrement d'une convention, réception d'une contribution | Repriorisation des P0 ; les lots non retenus passent en P1 | Comité de pilotage |
| H4 | Gouvernance des données (D4) | Les huit profils internes du DM § 7, complétés par le responsable adjoint et le comptable de centre demandés par le porteur de projet (onze profils internes calés sur l'organigramme des centres, dont le chef matériels, plus la gérante de la salle d'exposition et de la boutique avec le module boutique), et la matrice du DM § 8 servent de base ; la matrice détaillée par action sera produite avec la SFD | Refonte des rôles et des écrans d'administration | Direction Générale et référents métiers |
| H5 | Circuit RSE (D5) | Le responsable RSE qualifie et prépare ; la Direction Générale valide les propositions financières et désigne les signataires ; le circuit est paramétrable | Adapter CNV-02 et les droits de validation | Direction Générale |
| H6 | Gestion financière (D6) | Le MVP enregistre les contributions et leurs justificatifs uniquement, sans gestion budgétaire ni comptable (voir écart A2) | Si une gestion comptable est requise : nouveau lot, impact majeur sur délai et coût | Direction Générale, avec le représentant financier |
| H7 | Hébergement (D7, DAT § 14) | Hébergement cloud ou infrastructure équivalente validée ; fournisseur, pays et région choisis après examen juridique, sécuritaire, budgétaire et opérationnel | Le choix peut modifier l'architecture et le coût récurrent | Direction Générale |
| H8 | Budget (D8) | Le pilote (lot 1, un centre) serait financé par une offre de TIKA à la Direction Générale des CAEF, à confirmer ; les coûts récurrents (hébergement, maintenance, support, extension) doivent avoir un financeur identifié avant la fin du pilote ; voir le document Budget et modèle économique | Réduction aux lots « Noyau », voire au seul volet centre et bénéficiaires | Direction Générale |
| H9 | Interopérabilité (D9) | Aucune intégration tierce dans le MVP, sauf la passerelle Mobile Money demandée le 13/10/2026 (H16) ; l'import initial et les exports tableur sont prévus ; aucune autre intégration publique, bancaire, télécom ou d'identité n'est acquise (DAT § 9) | Ajout de lots d'intégration, avec accord et spécifications | Comité de pilotage |
| H10 | Indicateurs (D10) | Le tableau de bord national démarre avec les seuls indicateurs dont la fiche est validée, issus de la liste du DM § 10.1 | Le tableau de bord national peut être réduit, ou des indicateurs ajoutés après validation | Direction Générale et suivi-évaluation |
| H11 | Hors ligne (DM § 11.3, DAT § 14) | Demandé le 13/10/2026 par le porteur de projet, à formaliser par la Direction Générale : hors ligne d'abord ; les écrans de terrain (présences, dossiers, ventes, caisse, encaissements) fonctionnent sans Internet et se synchronisent automatiquement au retour du réseau (OFF-01 à OFF-08), construits dès le lot 1 | Si la Direction Générale revient sur la demande : application en ligne seulement avec saisie différée ; les écrans de terrain déjà construits restent utilisables en ligne | Comité de pilotage, avec la Direction Générale |
| H12 | Type d'application (DAT § 3.1, 14) | Application web responsive pour le back-office et application web installable (PWA) fonctionnant hors ligne pour le terrain, sans application mobile native | Une application native ajoute un lot et des coûts de maintenance ; à étudier seulement si une fonction du téléphone l'exige | Comité de pilotage, sur proposition technique |
| H13 | Style d'architecture (DAT § 3.2, 14) | Application structurée en modules (monolithe modulaire), base relationnelle et stockage documentaire séparé ; entrepôt analytique évalué plus tard | Des microservices augmenteraient la complexité d'exploitation et le coût | Équipe technique, validé par le comité de pilotage |
| H14 | Place du module boutique (demande du porteur de projet, absente du DM et du CDC) | Tranché le 12/10/2026 par le porteur de projet, à formaliser par la Direction Générale : le module boutique fait partie du MVP livré pour le pilote, dans le lot 1, construit après le socle en parallèle de la RSE ; BOU-01 à BOU-06 en P0, BOU-07 à BOU-11 en P1 attendues au pilote ; consolidation nationale (BOU-12) au lot 2 | Si la Direction Générale revient sur la décision : le module passe au lot 2 et le pilote ne mesure ni les ventes ni les reversements | Comité de pilotage, avec la Direction Générale |
| H15 | Politique tarifaire (demande du porteur de projet du 13/10/2026) | Services payants, montants et échéanciers fixés par la Direction Générale, par centre et par période ; exonérations et prises en charge (bourse, partenaire, programme) possibles, motivées et validées ; un impayé n'empêche pas automatiquement l'inscription ni la présence : la décision reste au responsable de centre | Sans tarif arrêté, la facturation de la scolarité n'est pas mise en service ; seuls les encaissements de la boutique et les paiements déclarés fonctionnent | Direction Générale |
| H16 | Passerelle Mobile Money et compte marchand (demande du porteur de projet du 13/10/2026) | Un agrégateur agréé couvrant les opérateurs utilisés par les payeuses (relevés au diagnostic) ; compte marchand au nom de l'entité CAEF, fonds versés directement sur ce compte ; commission de l'opérateur à la charge des CAEF sauf décision contraire ; avis juridique sur la réglementation de la Banque centrale de la République de Guinée avant la mise en service | Contrat direct avec un opérateur : un adaptateur par opérateur ; sans contrat signé, le Mobile Money reste déclaré avec sa référence (parcours C) | Direction Générale, avec le représentant financier |

**Questions à poser en priorité lors de la validation :**

- [ ] Confirmer les cinq processus prioritaires (H3).
- [ ] Confirmer que le MVP n'inclut aucune gestion comptable (H6).
- [ ] Fournir la liste des indicateurs déjà exigés par la Direction Générale et les partenaires (H10).
- [ ] Désigner les signataires et valideurs du circuit RSE (H5).
- [ ] Arrêter les critères de rapprochement pour la détection des doublons (BEN-05) et la liste minimale des champs de la fiche bénéficiaire (BEN-01).
- [ ] Confirmer les rôles d'adjoint et de comptable et le circuit de validation des clôtures de caisse.
- [ ] Recenser au diagnostic la boutique du centre pilote : production du centre seulement ou aussi dépôt-vente des bénéficiaires, part du centre sur les ventes en dépôt-vente, tenue actuelle de la caisse, comptable par centre ou mutualisé, modes de règlement utilisés (H14).
- [ ] Formaliser par la DG les décisions du 12/10/2026 (A1, A3, A14, H14).
- [ ] Confirmer l'offre TIKA et son périmètre (développement, hébergement initial, équipements, formation, accompagnement) (H8).
- [ ] Arrêter la politique tarifaire de la scolarité et des services associés (H15).
- [ ] Choisir la passerelle Mobile Money, ouvrir le compte marchand au nom des CAEF et obtenir l'avis juridique (H16).
- [ ] Confirmer la durée maximale de travail hors ligne sans reconnexion (72 heures proposées, OFF-06).
- [ ] Formaliser par la DG les demandes du 13/10/2026 (hors ligne d'abord, paiements Mobile Money).

### 8.2 Écarts entre le Document Maître et le cahier des charges

Treize écarts séparent le DM et le CDC, et trois autres le DM et le plan de déploiement ; pour chacun, le PRD applique une position d'attente réversible jusqu'à l'arbitrage. Les quatre premiers changent le périmètre ou le pilote ; A1 et A3, comme A14, ont été tranchés par le porteur de projet le 12/10/2026, à formaliser par la Direction Générale.

| ID | Sujet | Document Maître | Cahier des charges | Position d'attente du PRD | Instance qui tranche |
| --- | --- | --- | --- | --- | --- |
| A1 | Site pilote | Centres de Conakry, sous réserve : deux centres envisagés | Libellé ambigu, lisible comme un seul centre ; le plan parle aussi d'un site de référence unique | Tranché le 12/10/2026 par le porteur de projet : un seul centre, le CAEF Cameroun (quartier Cameroun, commune de Dixinn, Conakry) ; à formaliser par la Direction Générale (voir H2) | Comité de pilotage |
| A2 | Gestion financière RSE | Décision 6 ouverte : contributions seules ou gestion budgétaire étendue | Comptabilité générale exclue, mais suivi du budget prévisionnel et des dépenses « selon le modèle retenu » (M10) | H6 maintenue : contributions et justificatifs ; budget prévisionnel saisi dans la proposition ; suivi des dépenses en P2 | Direction Générale, avec le représentant financier |
| A3 | Crèches | Ajout possible après validation du périmètre opérationnel (§ 5) | Module M11 dans le périmètre cible si confirmé ; données d'enfants à protection renforcée | Tranché le 12/10/2026 par le porteur de projet : hors MVP, prévu plus tard (lot 3 ou cycle suivant), en lot distinct précédé d'une validation des données, accès, consentements et conservation ; à formaliser par la Direction Générale | Direction Générale |
| A4 | Communication | Module 9 tourné vers la documentation interne, les modèles et les autorisations de diffusion | Module M12 de publication publique : actualités, annonces, calendrier, validation avant publication, autorisations photos et témoignages ; profil dédié | Hors MVP (P2) ; aucune publication de contenu sur une bénéficiaire sans autorisation | Direction Générale |
| A5 | Notifications | Alertes citées dans le module 9 et alertes d'échéance des conventions | Module M15 dédié ; canaux application, courriel ou SMS à chiffrer avant intégration | Notifications dans l'application en P1 (NOT-01) ; courriel et SMS en P2 après validation des coûts | Direction Générale |
| A6 | Exclusions explicites | Aucune liste ; exclusions implicites via les décisions 6 et 9 | Huit exclusions nommées (§ 3.2) | Liste du CDC reprise comme hors périmètre MVP (section 5), à confirmer ; depuis le 13/10/2026, le paiement Mobile Money en est retiré à la demande du porteur de projet (section 6.12) | Comité de pilotage |
| A7 | Dénomination | « Centres d'Autonomisation et d'Entrepreneuriat des Femmes et des Filles » | « Centres d'Autonomisation et d'Entrepreneuriat des Femmes » | Intitulé du DM utilisé jusqu'à confirmation de l'intitulé officiel | Direction Générale |
| A8 | Démarche RSE | Pipeline commercial en 15 étapes partant du prospect, puis proposition et convention | Parcours en 11 étapes partant d'un besoin du centre et d'une fiche projet | Les deux entrées coexistent : la fiche projet (CNV-10) alimente une proposition ; le pipeline est conservé | Direction Générale et responsable RSE |
| A9 | Parcours d'autonomisation | Parcours = historique de la fiche bénéficiaire (M3 § 3.4) | Module M06 dédié : étapes, jalons, orientations, bilan | MVP = historique (BEN-07) ; module structuré en P2 après définition officielle des parcours (BEN-14) | Direction Générale |
| A10 | Profils | Huit profils internes, dont suivi-évaluation | Ajoute responsable insertion, responsable communication et apprenante ; pas de suivi-évaluation ; permissions aussi par périmètre géographique | Suivi-évaluation conservé au MVP ; les nouveaux profils arrivent avec leurs modules ; périmètre géographique prévu dans le modèle de droits (ADM-05) | Direction Générale et référents métiers |
| A11 | Accès externes | Portail partenaire en phase ultérieure | Accès partenaire et portail bénéficiaire à décider | Aucun accès externe au MVP (P3) | Direction Générale |
| A12 | Insertion et entrepreneuriat | Hors MVP (§ 23), phase 5 | Objectif spécifique 6 et modules M07, M08 dans le périmètre cible | Hors MVP (P2) ; si la mesure de l'insertion est voulue dès le pilote, ajouter un lot réduit (INS-01) | Direction Générale |
| A13 | Horizon | 24 mois « à confirmer » | 24 mois | 24 mois à confirmer après le diagnostic | Comité de pilotage |

**Écarts ajoutés avec le plan de déploiement.** A14 décidait de ce que le pilote démontre ; il a été tranché le 12/10/2026 (RSE dans le lot 1).

| ID | Sujet | Document Maître | Plan de déploiement | Position d'attente du PRD | Instance qui tranche |
| --- | --- | --- | --- | --- | --- |
| A14 | Place de la RSE | Dans le MVP (§ 23) ; le pilote doit montrer qu'un partenariat RSE est suivi de bout en bout ; module jugé stratégique (M7) | Priorité 2 avec partenaires, insertion et entrepreneuriat (§ 5) ; développable dans le premier lot ou le suivant (§ 4 ph. 3) | Tranché le 12/10/2026 par le porteur de projet : RSE dans le MVP livré pour le pilote, lot 1, construite après le socle ; O2 mesuré pendant le pilote ; à formaliser par la Direction Générale (section 5.1) | Comité de pilotage, sur proposition du responsable métier |
| A15 | Découpage des phases | 7 phases ; pilote en phase 4, extension fonctionnelle en phase 5, sans durées | 7 phases avec mois indicatifs ; tests et formation en phase 4, pilote en phase 5 (mois 11 à 13), consolidation en phase 6 | Phasage et numérotation du plan repris en section 9, calendrier indicatif à recaler après le diagnostic | Comité de pilotage |
| A16 | Gestion documentaire | Hors MVP, sauf pièces justificatives ; bibliothèque en évolution (M9) | Gestion documentaire de base dans le premier lot | DOC-01 en P1 dans le lot 1 ; bibliothèque complète en P2 | Responsable métier |

## 9. Feuille de route, risques et validation

Le lot 1 se construit aux mois 5 à 8, se teste aux mois 9 et 10 et se pilote aux mois 11 à 13 ; le lot 2 attend la validation du pilote (plan § 4). Ce calendrier sur 24 mois est indicatif : le plan comme le DM demandent de le recaler après le diagnostic, la validation du périmètre et l'estimation technique.

&#91;embedded content: feuille de route · 7 phases sur 24 mois (plan § 4)\]

Dans la phase 3, l'ordre de construction suit le plan : administration et utilisateurs, centres, bénéficiaires, formations et inscriptions, présences et résultats, tableaux de bord essentiels, gestion documentaire de base, journalisation et contrôle des accès. La RSE et la boutique viennent ensuite, en parallèle et dans le même lot 1 (A14 et H14 tranchées le 12/10/2026), avec la clôture mensuelle et le rapprochement (SRC-01 à SRC-04). Le client de terrain hors ligne et la synchronisation sont construits avec le socle, dès les premiers écrans de saisie ; le module paiements vient avec la boutique.

| Phase | Jalon de décision (plan § 4) | Ce que le PRD y attend |
| --- | --- | --- |
| 1. Cadrage et diagnostic | Validation du cadrage par la Direction | Situation de référence des indicateurs ; registres papier à reprendre inventoriés (SRC-03) ; équipement et couverture réseau du centre pilote évalués ; opérateurs Mobile Money utilisés par les payeuses relevés |
| 2. Conception | Autorisation de lancer la réalisation | PRD validé, décisions du 12/10/2026 et demandes du 13/10/2026 formalisées par la Direction Générale, autres hypothèses et écarts arbitrés ; SFD, modèle de données, DAT détaillé |
| 3. Réalisation du lot 1 | Version candidate à la validation métier | Exigences P0 du lot 1 livrées avec leurs critères d'acceptation |
| 4. Tests et formation | Décision de mise en production pilote | Conditions minimales de mise en service remplies (section 7) ; reprise des registres papier validée (MIG-01, SRC-03) ; centre pilote équipé |
| 5. Pilote et stabilisation | Validation du pilote par le comité | Critères de succès de la section 9.1 ; décision de poursuivre, corriger ou suspendre |
| 6. Consolidation et extension contrôlée | Autorisation de chaque vague | Lot 2 livré ; conditions d'intégration de chaque centre remplies (section 9.2) |
| 7. Extension et pérennisation | Revue stratégique de fin de cycle | Lot 3 selon décision ; bilan des indicateurs et des coûts d'exploitation |

### 9.1 Critères de succès du MVP à l'issue du pilote

1. Le centre pilote enregistre ses nouvelles candidatures, sessions, présences, ventes et caisses dans CAEF Connect, sans registre papier ni tableur parallèle pour ces données.
2. Au moins un partenariat RSE réel est suivi de l'opportunité à la contribution reçue et validée, avec ses justificatifs.
3. La Direction Générale consulte un tableau de bord national dont chaque indicateur a une fiche validée et renvoie à ses données sources.
4. La recette de sécurité ne relève aucun accès inter-centres non autorisé (testé entre le centre pilote et un centre fictif, « Centre de test B ») et une restauration de sauvegarde a réussi.
5. Les cibles d'adoption et de qualité des données, fixées après la situation de référence, sont atteintes ou leurs écarts expliqués dans le bilan de pilote.
6. Chaque mois du pilote est clôturé et rapproché (SRC-02) : la comptable et la responsable du centre partent des mêmes chiffres, et chaque écart avec les pièces est motivé.
7. Une journée de travail sans réseau (présences, ventes, encaissements) se synchronise au retour du réseau sans perte ni doublon ; si les paiements Mobile Money sont en service, chaque paiement confirmé est rapproché du relevé de l'opérateur.

Une fonctionnalité n'est livrée que si elle satisfait ses critères d'acceptation documentés dans la SFD et le cahier de recette, pas seulement en démonstration (DM § 17).

### 9.2 Conditions d'intégration d'un centre à une vague

L'extension se fait par vagues fondées sur la capacité réelle d'accompagnement, pas sur le nombre de centres annoncés (plan § 13). Un centre n'entre dans une vague que si ces conditions sont réunies :

- [ ] Responsable local désigné et utilisateurs identifiés.
- [ ] Équipements et connectivité évalués.
- [ ] Processus documentés et données préparées.
- [ ] Formation planifiée et droits d'accès configurés.
- [ ] Support disponible et procédure de retour arrière connue.
- [ ] Validation du responsable de déploiement.

### 9.3 Risques produit

| Risque (DM § 19) | Réponse dans ce PRD |
| --- | --- |
| Faible adoption par les centres | Parcours mobile pour les présences (FOR-06), interface par rôle (UX-01), périmètre limité aux processus prioritaires (H3) |
| Données initiales de mauvaise qualité | Import contrôlé avec rapport d'anomalies (BEN-08), saisie des registres papier rapprochée et divergences marquées « à vérifier » (MIG-01, SRC-03), détection des doublons (BEN-05), contrôles de complétude (BEN-03) |
| Périmètre trop ambitieux | Priorités P0 à P3, lots « Noyau » identifiés (section 5), modules 5, 8 et 9 reportés |
| Accès inapproprié aux données | Cloisonnement côté serveur (SEC-01), journalisation (SEC-04), exports journalisés (REP-01) |
| Dépendance technique | Réversibilité, export complet et remise du code (MNT-03), API documentée (ARC-05) |
| Confusion entre promesses et résultats | Statuts promise, reçue, validée (CTR-03), justificatif obligatoire (CTR-05), niveau de validation affiché (TDB-03) |
| Absence de gouvernance claire, financement récurrent insuffisant | Hors produit : traités par le comité de pilotage et le modèle économique ; financement du pilote par TIKA à confirmer, financeur des coûts récurrents à identifier avant la fin du pilote ; signalés par H1, H5 et H8 |
| Écarts de caisse et fraude à la boutique (porteur de projet) | Clôture quotidienne (BOU-05), séparation des tâches (section 6.10), numérotation continue des reçus et annulation par contre-écriture (BOU-06) |
| Connectivité au moment de la vente ou de la saisie (porteur de projet) | Hors ligne d'abord : ventes, reçus, présences et encaissements saisis sans réseau et synchronisés automatiquement (OFF-01 à OFF-08) ; reçu papier de secours numéroté si l'appareil est hors service |
| Dérive vers un logiciel de caisse ou de comptabilité complet (porteur de projet) | Exclusions maintenues (BOU-14, A6) : ni comptabilité générale, ni paie, ni paiement électronique autre que le Mobile Money (PAY-13) ; CAEF Connect ne détient jamais les fonds |
| Chiffres divergents entre la comptable et la responsable du centre (porteur de projet) | Source unique (SRC-01), clôture mensuelle rapprochée et verrouillée (SRC-02), reprise des registres papier avec statut « à vérifier » (SRC-03) |
| Centre pilote parti du papier : équipement et habitudes numériques insuffisants (porteur de projet) | Équipement comme condition d'entrée du pilote (section 7), formation planifiée et conduite du changement (section 9.2) |
| Paiements Mobile Money non confirmés, détournés ou comptés deux fois (porteur de projet) | Seule la confirmation de l'opérateur vaut encaissement (PAY-08), notifications authentifiées (SEC-14), rapprochement quotidien avec le relevé de l'opérateur (PAY-10), remboursement soumis à séparation des tâches (PAY-11) |
| Conflits ou pertes de données entre appareils hors ligne (porteur de projet) | Opérations immuables rejouées sans doublon (OFF-03), règles de conflit et file « À résoudre » (OFF-05), alerte sur appareil non synchronisé (OFF-07), clôtures conditionnées à la synchronisation (OFF-08) |

### 9.4 Validation et gouvernance du PRD

Ce PRD sera considéré comme validé lorsque la Direction Générale et le responsable du centre pilote auront confirmé le périmètre MVP, les priorités P0, les décisions du 12/10/2026 (A1, A3, A14, H14), les demandes du 13/10/2026 (hors ligne d'abord, paiements Mobile Money) et les autres hypothèses et écarts de la section 8, réserves consignées. La SFD du MVP sera rédigée sur cette base, suivie du DAT.

Le PRD est ensuite tenu par le responsable métier (Product Owner), qui priorise le backlog dans les limites de son mandat et soumet au comité de pilotage ce qui le dépasse (plan § 2.2). Toute modification importante du périmètre suit la procédure de gestion des changements (plan § 11 ; DM § 15.6) et n'est acquise qu'après décision de l'autorité compétente.

| Pour | Nom et fonction | Décision | Date |
| --- | --- | --- | --- |
| Direction Générale des CAEF |  | Validé / Validé sous réserve / À réviser |  |
| Centre CAEF Cameroun (Dixinn), centre pilote |  | Validé / Validé sous réserve / À réviser |  |
| Équipe projet |  | Rédigé |  |
