# Référentiel des indicateurs CAEF Connect

Oct 12, 2026 · @Bangoura · version 0.1, à valider par la Direction Générale et le suivi-évaluation · mis à jour le 14/10/2026 (calcul dans le backend, section 2.3)

## 1. Objet, sources et principes de mesure

Ce référentiel donne une définition commune à chaque indicateur affiché dans CAEF Connect. Il répond au DM § 10.4 (« un indicateur sans définition commune ne doit pas être utilisé comme référence nationale »), au CDC M13 (définitions uniformes entre centres) et au livrable 12 du DM § 21. Il sert de source aux exigences TDB-01 à TDB-09 du PRD et aux écrans E-TDB-01 à E-TDB-03 de la SFD.

Les listes de départ sont celles du DM § 10.1 (tableau de bord national), § 10.2 (centre), § 10.3 (RSE) et du Plan de déploiement (indicateurs d'adoption et de qualité). Elles restent une proposition : l'hypothèse H10 du PRD prévoit que le tableau de bord national démarre avec les seuls indicateurs dont la fiche est validée, et la liste des indicateurs déjà exigés par la Direction Générale et les partenaires reste à fournir.

Sept principes s'appliquent à tous les indicateurs.

1. **Pas de fiche validée, pas de référence nationale.** Un indicateur au statut brouillon peut être calculé en recette ou au pilote, mais n'apparaît ni au tableau de bord national ni dans un rapport institutionnel (TDB-01).
2. **Déclaratif et vérifié restent séparés.** Chaque valeur affiche son niveau de validation (TDB-03). Une insertion déclarée par la bénéficiaire n'est jamais additionnée à une insertion confirmée par un justificatif ; une contribution promise n'est jamais additionnée à une contribution reçue (DM § 9.3).
3. **Une donnée manquante n'est pas un zéro.** Les calculs excluent les enregistrements dont le champ requis est vide et affichent à côté de la valeur le nombre d'enregistrements exclus (TDB-09, CDC M13). Un centre qui n'a rien saisi pour la période s'affiche « non renseigné », pas « 0 ».
4. **Chaque chiffre mène à sa source.** Un clic sur une valeur ouvre la liste des enregistrements qui la composent, dans la limite des droits de la personne (TDB-02). Un utilisateur sans accès nominatif voit les effectifs, pas les noms.
5. **Date de calcul toujours visible.** Les agrégats sont recalculés chaque nuit dans le schéma de pilotage (DAT § 2) ; chaque tableau de bord affiche la date et l'heure du dernier calcul.
6. **Petits effectifs masqués.** Hors du périmètre d'un centre, toute valeur calculée sur moins de cinq bénéficiaires s'affiche « < 5 » pour limiter la réidentification (seuil proposé, point à arbitrer R3). Avec un seul centre pilote, toute valeur « nationale » est celle du CAEF Cameroun (Dixinn) : la règle s'applique donc dès le pilote à tout affichage ou export hors du centre.
7. **Pas de cible sans situation de référence.** Les cibles chiffrées sont fixées après la mesure de départ du pilote, comme le prévoit le Plan de déploiement ; aucun taux de réussite n'est annoncé sans données fiables.

Les fiches de ce document suivent les dix rubriques du DM § 10.4. Le nom figure dans le titre de la fiche ; les neuf autres rubriques sont dans le tableau. Le CDC demande aussi les exclusions : elles sont écrites dans la rubrique « Formule ».

## 2. Cycle de vie d'une fiche et règles communes de calcul

### 2.1 Cycle de vie

Les fiches sont gérées dans l'outil (TDB-07, P1) ; avant cette fonction, ce document fait foi. Une fiche passe par cinq statuts.

| Statut | Qui agit | Effet |
| --- | --- | --- |
| Brouillon | Responsable suivi-évaluation (SE) | Calculé en recette et au pilote, invisible au tableau de bord national |
| Proposée | SE, après test sur des données réelles | Soumise au comité de pilotage avec un exemple de calcul |
| Validée | Direction Générale (DG) | Affichée au tableau de bord national et utilisable dans les rapports |
| Révisée | SE propose, DG valide | Nouvelle version ; l'ancienne reste consultable et les séries antérieures portent la mention de rupture |
| Retirée | DG | Plus calculée ; historique conservé |

Toute modification de formule crée une nouvelle version numérotée. Un rapport exporté indique la version de chaque fiche utilisée, pour qu'un chiffre de 2027 reste comparable à un chiffre de 2028 ou que l'écart soit expliqué.

### 2.2 Règles communes

| Règle | Contenu |
| --- | --- |
| Période | Mois civil, trimestre, semestre ou année, selon les périodes déclarées dans l'entité periode. Un événement est rattaché à la période de sa date métier (date de clôture, de délivrance, de réception), jamais à sa date de saisie. |
| Stock et flux | Un indicateur de stock (bénéficiaires actives, partenariats actifs) se lit au dernier jour de la période. Un indicateur de flux (attestations délivrées, montants reçus) additionne les événements de la période. |
| Rattachement au centre | Une inscription compte pour le centre de la session ; une bénéficiaire compte pour son centre de rattachement au dernier jour de la période. Après un transfert, l'historique reste au centre d'origine. Au niveau national, une bénéficiaire n'est comptée qu'une fois. |
| Dossiers exclus | Les dossiers fusionnés (doublons), annulés ou créés dans l'environnement de formation ne sont jamais comptés. Les dossiers archivés comptent pour les périodes où ils étaient actifs. |
| Bénéficiaire active | Bénéficiaire ayant au moins une inscription au statut inscrite, commencée ou suspendue à la date de lecture, ou une inscription achevée dans les 90 jours qui précèdent (définition proposée, point R1). |
| Montants | Agrégés dans la devise de référence nationale, après conversion enregistrée sur chaque contribution (devise d'origine, taux, source du taux, RG-CTR-06). La devise de travail est le franc guinéen (GNF) ; les contributions de partenaires internationaux peuvent être en USD ou en EUR. Les totaux s'affichent par devise, sans total multi-devises sans taux daté (R2). |
| Financier et non financier | Jamais additionnés. Les contributions en nature ont leur propre total, en valeur estimée, avec la méthode de valorisation. |
| Arrondis | Taux à une décimale ; montants à l'unité ; aucun arrondi intermédiaire. |
| Ventilations | Centre, pays, zone territoriale, période, programme, catégorie de formation, tranche d'âge. La ventilation territoriale fine est P2 (TDB-08). |
| Niveau de validation | Déclaratif : saisi sans justificatif ni second contrôle. Vérifié : appuyé par un justificatif ou validé par une seconde personne habilitée. Un indicateur affiche les deux valeurs séparément quand les deux existent. |
| Module désactivé | Pour un centre où le module source d'un indicateur est désactivé (boutique, salle d'exposition, scolarité et paiements, volet RSE du centre ; ADM-08), l'indicateur s'affiche « Module non activé », jamais 0, pour toute la période désactivée. Les totaux nationaux additionnent seulement les centres où le module est actif et indiquent leur nombre (par exemple « 3 centres sur 4 »). Une réactivation ne reprend pas de données pour la période désactivée (RG-ADM-20). |

### 2.3 Mise en œuvre dans le backend du lot 1 (14/10/2026)

Le calcul est écrit dans `backend/caef/pilotage/indicateurs.py`. Une tâche nocturne (1 h 00) recalcule le mois courant et le mois précédent, par centre réel puis au national, et range chaque valeur dans la table `pilotage.valeur_indicateur` (Modèle § 10) avec sa date de calcul, son niveau de validation, son numérateur et son dénominateur, et le nombre d'enregistrements non renseignés. Les règles de la section 2.2 y sont appliquées : une valeur absente reste vide et s'affiche « non renseigné » ; un module désactivé donne « Module non activé » ; les centres fictifs et les dossiers fusionnés ne comptent jamais ; financier et en nature, déclaratif et vérifié, et chaque devise restent séparés ; taux à une décimale et montants à l'unité, sans arrondi intermédiaire ; une valeur figée à la clôture d'une période n'est plus recalculée. Une valeur est marquée « fiabilité faible » au-delà de 20 % d'enregistrements non renseignés.

Le statut de chaque fiche est tenu dans la table `fiche_indicateur` (brouillon, proposée, validée, révisée, retirée) : seule une fiche validée s'affiche au national, et une fiche retirée n'est plus calculée. Le paramètre de la bénéficiaire active (R1) est `CAEF_JOURS_BENEFICIAIRE_ACTIVE`, 90 jours par défaut, et celui des petits effectifs (R3) `CAEF_SEUIL_PETITS_EFFECTIFS`, 5 par défaut.

| Famille | Calculés au lot 1 | Non calculés, affichés « non renseigné » |
| --- | --- | --- |
| Formation et bénéficiaires | IND-01 à IND-10 | IND-11, IND-12 (lot 3) |
| RSE et programmes | IND-20 à IND-24, IND-26 à IND-28 | IND-25 (pas de source au MVP), IND-29 (lot 3) |
| Qualité des données | IND-30, IND-31, IND-33, IND-34 | IND-32 (pas encore d'import), IND-35 |
| Adoption | IND-40 | IND-41 à IND-44 (pas de source de données au MVP) |
| Boutique et clôture mensuelle | IND-45 à IND-50 ; IND-45 à IND-49 marqués « Module non activé » pour un centre sans boutique | Aucun |

Vingt-neuf indicateurs sont donc calculés. IND-35 et IND-41 à IND-44 figurent pourtant dans la liste des fiches à valider avant le pilote (section 9.2) : leur calcul, ou une saisie manuelle de la mesure, reste à prévoir.

## 3. Catalogue des indicateurs

Le référentiel compte 39 indicateurs répartis en cinq familles. Les codes laissent des numéros libres dans chaque famille pour les ajouts. Le lot suit le PRD : lot 1 pour le noyau, lot 1 aussi pour la RSE et la boutique, livrées au pilote après le socle (A14 et H14 tranchées par le porteur de projet le 12/10/2026, à formaliser par la Direction Générale, ce qui règle l'écart A16 du PRD), lot 3 pour l'extension. Les colonnes NAT, CEN et RSE indiquent les tableaux de bord qui affichent l'indicateur (E-TDB-01 national, E-TDB-02 centre, E-TDB-03 RSE).

| Code | Indicateur | Lot | NAT | CEN | RSE | Responsable | Niveau |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IND-01 | Centres actifs | 1 | oui | non | non | SE | Vérifié |
| IND-02 | Bénéficiaires enregistrées | 1 | oui | oui | non | SE | Vérifié |
| IND-03 | Bénéficiaires actives | 1 | oui | oui | non | SE | Vérifié |
| IND-04 | Candidatures reçues | 1 | oui | oui | non | RC | Déclaratif |
| IND-05 | Sessions de formation ouvertes | 1 | oui | oui | non | RP | Vérifié |
| IND-06 | Sessions de formation clôturées | 1 | oui | oui | non | RP | Vérifié |
| IND-07 | Taux d'achèvement | 1 | oui | oui | non | RP | Vérifié |
| IND-08 | Taux d'assiduité | 1 | oui | oui | non | RP | Vérifié |
| IND-09 | Attestations délivrées | 1 | oui | oui | non | RP | Vérifié |
| IND-10 | Délai de traitement des candidatures | 1 | oui | oui | non | RC | Vérifié |
| IND-11 | Projets entrepreneuriaux suivis | 3 | oui | oui | non | RC | Les deux, séparés |
| IND-12 | Insertions professionnelles | 3 | oui | oui | non | SE | Les deux, séparés |
| IND-20 | Partenariats RSE actifs | 1 | oui | non | oui | RSE | Vérifié |
| IND-21 | Montant sollicité | 1 | oui | non | oui | RSE | Déclaratif |
| IND-22 | Montant accordé | 1 | oui | non | oui | RSE | Vérifié |
| IND-23 | Montant encaissé | 1 | oui | oui | oui | RSE | Vérifié |
| IND-24 | Valeur des contributions en nature reçues | 1 | oui | oui | oui | RSE | Vérifié |
| IND-25 | Activité commerciale RSE | 1 | non | non | oui | RSE | Déclaratif |
| IND-26 | Taux de transformation | 1 | non | non | oui | RSE | Vérifié |
| IND-27 | Engagements en retard | 1 | non | oui | oui | RSE | Vérifié |
| IND-28 | Conventions à renouveler | 1 | non | non | oui | RSE | Vérifié |
| IND-29 | Taux d'exécution des programmes | 3 | oui | non | oui | SE | Vérifié |
| IND-30 | Complétude des dossiers | 1 | non | oui | non | SE | Vérifié |
| IND-31 | Doublons détectés | 1 | non | oui | non | SE | Vérifié |
| IND-32 | Anomalies d'import | 1 | non | non | non | SE | Vérifié |
| IND-33 | Présences saisies dans les délais | 1 | non | oui | non | RP | Vérifié |
| IND-34 | Contributions reçues justifiées | 1 | non | non | oui | SE | Vérifié |
| IND-35 | Rapports transmis dans les délais | 1 | oui | oui | non | SE | Vérifié |
| IND-40 | Utilisateurs actifs | 1 | non | oui | non | ADM | Vérifié |
| IND-41 | Taux d'utilisation des modules | 1 | non | non | non | ADM | Vérifié |
| IND-42 | Demandes d'assistance | 1 | non | non | non | ADM | Vérifié |
| IND-43 | Satisfaction des utilisateurs | 1 | non | non | non | SE | Déclaratif |
| IND-44 | Temps de production du rapport mensuel | 1 | non | non | non | SE | Déclaratif |
| IND-45 | Chiffre d'affaires de la boutique | 1 | après BOU-12 | oui | non | CPT | Les deux, séparés |
| IND-46 | Nombre de ventes | 1 | non | oui | non | CPT | Les deux, séparés |
| IND-47 | Revenus reversés aux productrices | 1 | après BOU-12 | oui | non | CPT | Vérifié |
| IND-48 | Taux de clôtures de caisse avec écart | 1 | non | oui | non | CPT | Vérifié |
| IND-49 | Productrices actives en boutique | 1 | après BOU-12 | oui | non | RC | Les deux, séparés |
| IND-50 | Clôtures mensuelles rapprochées dans les délais | 1 | non | oui | non | CPT | Vérifié |

Les indicateurs de qualité et d'adoption sans tableau de bord sont lus dans l'écran d'administration et repris dans le bilan de pilote. Le « nombre d'alertes » et la « répartition territoriale » cités au DM § 10.1 ne sont pas des indicateurs : le premier est une liste de travail, la seconde une ventilation applicable à tous les indicateurs.

IND-11, IND-12 et IND-29 dépendent de modules hors MVP (entrepreneuriat, insertion, programmes complets) ; leurs fiches sont préparées dès maintenant pour que les données du lot 3 soient collectées selon la bonne définition, mais ils ne s'affichent pas tant que le module n'est pas livré.

IND-45 à IND-50 (famille boutique, revenus des productrices et clôture mensuelle) répondent à une demande du porteur de projet, absente du DM et du CDC ; leurs fiches sont proposées, à valider (H10). Ils sont dans le lot 1 (H14 tranchée) ; IND-50 mesure la clôture mensuelle rapprochée (SRC-02), née du constat que les chiffres de la comptable et ceux de la responsable du centre divergent. CPT désigne le comptable de centre, rôle ajouté à la même demande. « Après BOU-12 » : agrégat national sans nom de productrice, affiché seulement une fois la fiche validée et la consolidation BOU-12 livrée (P2).

Le catalogue couvre aussi les indicateurs de réussite du projet (DM § 18) : adoption par IND-40 et IND-41, qualité par IND-30, IND-31 et IND-35, efficacité par IND-10, IND-27 et IND-44, performance RSE par IND-22 à IND-26, résultats sociaux par IND-07, IND-09, IND-11 et IND-12. Trois indicateurs du DM § 18 restent suivis hors de l'outil, dans le bilan de pilote : le taux de réalisation des formations utilisateurs (plan de formation), le nombre d'opérations nécessitant une reprise manuelle (registre d'assistance) et le taux de production des rapports d'impact (lot 3, avec le module impact).

## 4. Fiches formation et bénéficiaires

Ces douze indicateurs portent le cœur du tableau de bord national et du tableau de bord de centre. Sauf mention contraire, ils sont recalculés chaque nuit et lus au mois.

### IND-01 · Centres actifs

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer l'étendue réelle du réseau qui utilise CAEF Connect. |
| Formule | Nombre de centres au statut actif ayant au moins une session de formation ouverte, en cours ou clôturée dans la période. Exclus : centres inactifs, centre de formation fictif. |
| Unité | Nombre de centres |
| Période de référence | Mois, trimestre, année |
| Source | centre, session\_formation |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | Le total ne dépasse pas le nombre de centres déclarés ; un centre actif sans session pendant deux mois déclenche une alerte de vérification. |
| Limites | Mesure l'activité dans l'outil, pas l'activité réelle : un centre actif sur le terrain mais qui ne saisit pas apparaît inactif. |

### IND-02 · Bénéficiaires enregistrées

| Rubrique | Contenu |
| --- | --- |
| Objectif | Connaître le nombre de personnes distinctes connues du réseau. |
| Formule | Nombre de dossiers bénéficiaire distincts créés jusqu'au dernier jour de la période. Exclus : statut fusionné, dossiers de l'environnement de formation. Une personne transférée compte une fois au niveau national. |
| Unité | Nombre de personnes |
| Période de référence | Stock au dernier jour de la période ; flux des nouvelles inscriptions en complément |
| Source | beneficiaire |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | Contrôle mensuel des doublons potentiels (IND-31) avant publication ; écart de plus de 5 % avec le mois précédent à expliquer. |
| Limites | Après la reprise des données, le stock inclut des dossiers anciens peu fiables tant que le nettoyage n'est pas terminé ; afficher la date de fin de reprise. |

### IND-03 · Bénéficiaires actives

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la population réellement accompagnée à un instant donné. |
| Formule | Nombre de bénéficiaires distinctes ayant, au dernier jour de la période, une inscription inscrite, commencée ou suspendue, ou une inscription achevée dans les 90 jours précédents. Exclus : fusionnées. |
| Unité | Nombre de personnes |
| Période de référence | Stock au dernier jour de la période |
| Source | beneficiaire, inscription |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | IND-03 ≤ IND-02 ; vérification par échantillon au pilote. |
| Limites | La fenêtre de 90 jours est une proposition (R1) ; un accompagnement hors formation (entrepreneuriat, insertion) ne compte qu'à partir du lot 3. |

### IND-04 · Candidatures reçues

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la demande adressée aux centres. |
| Formule | Nombre de candidatures dont la date de soumission tombe dans la période, quel que soit leur statut ensuite. Exclus : brouillons, annulées par erreur de saisie. Le taux de validation (validées / décidées) est affiché en détail. |
| Unité | Nombre de candidatures |
| Période de référence | Mois, trimestre, année |
| Source | candidature |
| Responsable | Responsable de centre |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | Une candidature rejetée porte toujours un motif (BEN-04). |
| Limites | Déclaratif : les demandes orales non enregistrées ne sont pas comptées ; la demande réelle peut être plus forte. |

### IND-05 · Sessions de formation ouvertes

| Rubrique | Contenu |
| --- | --- |
| Objectif | Suivre l'offre de formation mise à disposition. |
| Formule | Nombre de sessions passées au statut ouverte ou en cours dans la période. Exclus : brouillons, annulées avant ouverture. |
| Unité | Nombre de sessions ; ventilation par catégorie de formation |
| Période de référence | Mois, trimestre, année |
| Source | session\_formation |
| Responsable | Responsable pédagogique |
| Fréquence | Recalcul nocturne |
| Règles de validation | Une session ouverte a un formateur principal, un lieu et une capacité (RG-FOR-01). |
| Limites | Une session longue est comptée une fois, quelle que soit sa durée ; compléter par le nombre de places offertes. |

### IND-06 · Sessions de formation clôturées

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer l'offre effectivement menée à son terme. |
| Formule | Nombre de sessions passées au statut clôturée dans la période, avec rapport de clôture renseigné. |
| Unité | Nombre de sessions |
| Période de référence | Mois, trimestre, année (date de clôture) |
| Source | session\_formation |
| Responsable | Responsable pédagogique |
| Fréquence | Recalcul nocturne |
| Règles de validation | Une session ne peut être clôturée que si toutes les séances ont leurs présences validées et chaque inscription un statut final (SFD 5.3). |
| Limites | Les sessions annulées sont suivies à part ; un taux d'annulation élevé n'apparaît pas ici. |

### IND-07 · Taux d'achèvement

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la capacité des centres à mener les bénéficiaires au bout de leur parcours. |
| Formule | Inscriptions au statut achevée / inscriptions au statut final (achevée, non achevée, abandonnée), pour les sessions clôturées dans la période × 100. Exclus : inscriptions annulées avant le début, inscriptions sans statut final (comptées comme manquantes). |
| Unité | Pourcentage |
| Période de référence | Trimestre, année |
| Source | inscription, session\_formation |
| Responsable | Responsable pédagogique |
| Fréquence | Recalcul nocturne ; lecture trimestrielle |
| Règles de validation | Le critère d'achèvement (taux de présence minimal, évaluation) est celui paramétré pour la formation (RG-FOR-08) ; une dérogation est motivée et tracée. |
| Limites | Dépend du seuil de présence propre à chaque formation ; ne comparer les centres qu'à catégorie de formation égale. Ne pas confondre achèvement et acquisition des compétences. |

### IND-08 · Taux d'assiduité

| Rubrique | Contenu |
| --- | --- |
| Objectif | Repérer tôt les sessions et les bénéficiaires en risque d'abandon. |
| Formule | Présences (présente, retard) / présences attendues sur les séances dont la liste est validée × 100. Les absences justifiées sont retirées du dénominateur. Exclus : séances non validées (comptées comme manquantes). |
| Unité | Pourcentage |
| Période de référence | Mois |
| Source | presence, seance |
| Responsable | Responsable pédagogique |
| Fréquence | Recalcul nocturne |
| Règles de validation | Présences validées par le formateur ; une saisie tardive porte un motif (RG-FOR-06). |
| Limites | Un taux élevé sur peu de séances validées est trompeur : afficher le nombre de séances non validées à côté. |

### IND-09 · Attestations délivrées

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer les parcours reconnus officiellement. |
| Formule | Nombre d'attestations au statut délivrée dont la date de délivrance tombe dans la période. Exclus : attestations annulées. |
| Unité | Nombre d'attestations |
| Période de référence | Mois, trimestre, année |
| Source | attestation |
| Responsable | Responsable pédagogique |
| Fréquence | Recalcul nocturne |
| Règles de validation | Une attestation n'existe que pour une participation achevée (FOR-09) ; numéro unique. |
| Limites | Une bénéficiaire peut recevoir plusieurs attestations ; pour un nombre de personnes, compter les bénéficiaires distinctes. |

### IND-10 · Délai de traitement des candidatures

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la réactivité administrative des centres, demandée par le Plan de déploiement. |
| Formule | Médiane, en jours calendaires, entre la date de soumission et la date de décision (validée ou rejetée), pour les candidatures décidées dans la période. La moyenne est affichée en complément. |
| Unité | Jours |
| Période de référence | Mois, trimestre |
| Source | candidature (horodatage des changements de statut) |
| Responsable | Responsable de centre |
| Fréquence | Recalcul nocturne |
| Règles de validation | Les dates viennent de l'historique des statuts, pas d'une saisie libre. |
| Limites | Les dossiers incomplets en attente de pièces allongent le délai sans faute du centre ; afficher la part de dossiers passés par le statut incomplète. |

### IND-11 · Projets entrepreneuriaux suivis (lot 3)

| Rubrique | Contenu |
| --- | --- |
| Objectif | Suivre l'accompagnement à l'entrepreneuriat sans présenter des intentions comme des résultats (DM § 8.3). |
| Formule | Nombre de projets accompagnés dans la période, ventilé par stade : déclaré, en préparation, activité lancée, entreprise enregistrée (vérifiée), activité opérationnelle au suivi. Chaque stade est un compteur distinct, jamais additionné aux autres. |
| Unité | Nombre de projets par stade |
| Période de référence | Trimestre, année |
| Source | Module entrepreneuriat (lot 3) |
| Responsable | Responsable de centre |
| Fréquence | Recalcul nocturne ; lecture trimestrielle |
| Règles de validation | Les stades « entreprise enregistrée » et « opérationnelle » exigent un justificatif ou une visite tracée. |
| Limites | Non affiché avant le lot 3. La survie de l'activité n'est connue qu'aux échéances de suivi. |

### IND-12 · Insertions professionnelles (lot 3)

| Rubrique | Contenu |
| --- | --- |
| Objectif | Documenter l'effet des parcours sur l'emploi (DM § 14.4). |
| Formule | Nombre de bénéficiaires sorties de formation dont la situation à l'échéance de suivi (3, 6 ou 12 mois, à confirmer) est un emploi, un stage ou une activité rémunérée. Deux valeurs séparées : déclarée et confirmée par un justificatif. Le taux rapporte au nombre de bénéficiaires jointes, pas au nombre de sorties. |
| Unité | Nombre de personnes ; pourcentage des personnes jointes |
| Période de référence | Cohorte de sortie |
| Source | Module insertion (lot 3) |
| Responsable | Responsable suivi-évaluation |
| Fréquence | À chaque échéance de suivi |
| Règles de validation | Taux de réponse affiché avec le résultat ; aucune donnée transmise à un employeur sans base légitime. |
| Limites | Non affiché avant le lot 3. Les personnes non jointes ne sont pas comptées comme sans emploi ; l'insertion n'est pas attribuable à la seule formation. |

## 5. Fiches RSE et programmes

Ces indicateurs suivent la chaîne du DM § 9.3 : une proposition ne vaut pas convention, une convention ne vaut pas encaissement, un encaissement ne vaut pas exécution. Chaque maillon a donc son propre indicateur, et aucun n'est additionné à un autre. Le référentiel recommande que le tableau de bord RSE place IND-21, IND-22 et IND-23 côte à côte pour que l'écart se lise d'un coup d'œil.

### IND-20 · Partenariats RSE actifs

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la base de partenaires engagés auprès du réseau. |
| Formule | Nombre de partenaires distincts ayant au moins une convention au statut signée ou en exécution au dernier jour de la période. Exclus : prospects, conventions résiliées. |
| Unité | Nombre de partenaires |
| Période de référence | Stock au dernier jour de la période |
| Source | partenaire, convention |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | Une convention signée porte une date de signature et le document signé (RG-CNV-05). |
| Limites | Un grand partenaire et un petit comptent chacun pour un ; lire avec IND-22. |

### IND-21 · Montant sollicité

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer l'effort de mobilisation de ressources. |
| Formule | Somme des montants des propositions au statut soumise, acceptée ou refusée dont la date de transmission tombe dans la période. Exclus : brouillons, propositions en validation interne. |
| Unité | Devise de référence |
| Période de référence | Trimestre, année |
| Source | proposition |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne |
| Règles de validation | Une proposition transmise a franchi la validation interne (circuit H5). |
| Limites | Intention de financement, pas une ressource ; ne jamais présenter ce montant comme acquis. |

### IND-22 · Montant accordé

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer les engagements financiers formalisés. |
| Formule | Somme des montants accordés des conventions signées dans la période (date de signature). Exclus : conventions en préparation, résiliées avant tout versement. |
| Unité | Devise de référence |
| Période de référence | Trimestre, année |
| Source | convention |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne |
| Règles de validation | Montant accordé distinct du montant sollicité ; document signé joint. |
| Limites | Une convention pluriannuelle est comptée en entier à sa signature ; l'échelonnement se lit dans les contributions promises. |

### IND-23 · Montant encaissé

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer les ressources financières effectivement reçues. |
| Formule | Somme des montants reçus des contributions financières au statut validée, dont la date de réception tombe dans la période. Les contributions reçues mais pas encore validées s'affichent à part, en déclaratif. Exclus : promises, annulées. |
| Unité | Devise de référence |
| Période de référence | Mois, trimestre, année |
| Source | contribution |
| Responsable | Responsable RSE et partenariats ; validation par une personne habilitée distincte |
| Fréquence | Recalcul nocturne |
| Règles de validation | Saisie et validation par deux personnes différentes (RG-CTR-04) ; au moins un justificatif ; taux de conversion et sa source si la devise diffère. |
| Limites | N'est pas un chiffre comptable : le rapprochement reste sous la responsabilité de la comptabilité (H6). |

### IND-24 · Valeur des contributions en nature reçues

| Rubrique | Contenu |
| --- | --- |
| Objectif | Rendre visibles les dons de biens, services et compétences. |
| Formule | Somme des valeurs estimées des contributions non financières validées reçues dans la période, avec le nombre de contributions sans valeur estimée affiché à côté. |
| Unité | Devise de référence (valeur estimée) ; nombre de contributions |
| Période de référence | Trimestre, année |
| Source | contribution (financiere = faux) |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne |
| Règles de validation | Méthode de valorisation obligatoire dès qu'une valeur est saisie ; justificatif de réception. |
| Limites | Valeur estimée, jamais additionnée aux montants encaissés ; les méthodes de valorisation doivent être arrêtées (R4). |

### IND-25 · Activité commerciale RSE

| Rubrique | Contenu |
| --- | --- |
| Objectif | Suivre l'amont du pipeline : prospects, rendez-vous, propositions (DM § 10.3). |
| Formule | Trois compteurs distincts sur la période : nouveaux partenaires au statut prospect ; interactions de type rendez-vous ; propositions transmises. |
| Unité | Nombre |
| Période de référence | Mois, trimestre |
| Source | partenaire, interaction, proposition |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne |
| Règles de validation | Une interaction porte une date, un interlocuteur et un compte rendu. |
| Limites | Mesure l'activité, pas la performance ; ne sert pas à évaluer individuellement les personnes ni à calculer une commission. |

### IND-26 · Taux de transformation

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer l'efficacité du pipeline RSE. |
| Formule | Opportunités gagnées / opportunités clôturées (gagnées ou perdues) dans la période × 100. Exclus : opportunités ouvertes ou suspendues. |
| Unité | Pourcentage |
| Période de référence | Semestre, année (fenêtre glissante de 12 mois recommandée) |
| Source | opportunite, historique\_etape |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne |
| Règles de validation | Une opportunité perdue porte un motif ; une opportunité gagnée est liée à une convention. |
| Limites | Peu significatif sous dix opportunités clôturées : afficher l'effectif à côté du taux. |

### IND-27 · Engagements en retard

| Rubrique | Contenu |
| --- | --- |
| Objectif | Repérer les engagements des conventions, des deux parties, qui dépassent leur échéance. |
| Formule | Nombre d'engagements dont l'état est en retard au jour de lecture, ventilé par partie (partenaire, CAEF). |
| Unité | Nombre d'engagements |
| Période de référence | Jour de lecture |
| Source | engagement |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne |
| Règles de validation | État calculé automatiquement à partir de l'échéance (RG-CNV-07), jamais saisi. |
| Limites | Un engagement mal daté à la saisie fausse le compte ; vérification par le responsable à chaque alerte. |

### IND-28 · Conventions à renouveler

| Rubrique | Contenu |
| --- | --- |
| Objectif | Anticiper les renouvellements avant l'échéance. |
| Formule | Nombre de conventions en exécution dont la date de fin tombe dans les 90 prochains jours. |
| Unité | Nombre de conventions |
| Période de référence | Jour de lecture |
| Source | convention |
| Responsable | Responsable RSE et partenariats |
| Fréquence | Recalcul nocturne |
| Règles de validation | Date de fin obligatoire pour une convention signée. |
| Limites | L'horizon de 90 jours est paramétrable ; il est proposé, pas décidé. |

### IND-29 · Taux d'exécution des programmes (lot 3)

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer l'avancement réel des programmes financés (DM § 10.1). |
| Formule | Activités réalisées et validées / activités prévues au plan du programme pour la période × 100 ; un taux d'exécution budgétaire (dépenses justifiées / budget) est suivi à part. |
| Unité | Pourcentage |
| Période de référence | Trimestre, durée du programme |
| Source | Module programmes complet (lot 3) |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Recalcul nocturne ; lecture trimestrielle |
| Règles de validation | Une activité est réalisée si un justificatif est joint et validé. |
| Limites | Non affiché avant le lot 3 ; au MVP la fiche programme est minimale (CNV-06). Le volet budgétaire suppose une source comptable, hors MVP (H6). |

## 6. Fiches qualité des données

Ces six indicateurs disent si les autres sont fiables. Ils alimentent le bilan de qualité des données exigé en fin de pilote par le Plan de déploiement, et le responsable suivi-évaluation les lit avant chaque publication mensuelle.

### IND-30 · Complétude des dossiers

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la part des dossiers bénéficiaires utilisables pour le pilotage. |
| Formule | Moyenne du champ complétude (part des champs obligatoires et recommandés renseignés) sur les dossiers actifs ; part des dossiers à 100 % en complément. |
| Unité | Pourcentage |
| Période de référence | Jour de lecture ; série mensuelle |
| Source | beneficiaire (completude) |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Recalcul nocturne |
| Règles de validation | La liste des champs comptés est fixée dans le Modèle de données et versionnée avec la fiche. |
| Limites | Un champ rempli n'est pas un champ juste ; compléter par des contrôles par échantillon. |

### IND-31 · Doublons détectés

| Rubrique | Contenu |
| --- | --- |
| Objectif | Suivre le risque de compter deux fois une même personne. |
| Formule | Nombre de paires de doublons potentiels signalées par la règle de rapprochement (BEN-05) dans la période, et part traitée (fusionnée ou déclarée distincte). |
| Unité | Nombre de paires ; pourcentage traité |
| Période de référence | Mois |
| Source | beneficiaire, journal\_audit (fusions) |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Recalcul nocturne |
| Règles de validation | Toute fusion est tracée et réversible selon la SFD. |
| Limites | Dépend des critères de rapprochement, encore à arrêter ; un taux faible peut venir de critères trop stricts. |

### IND-32 · Anomalies d'import

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la qualité des données reprises des fichiers existants. |
| Formule | Lignes rejetées ou mises en anomalie / lignes soumises × 100, par lot d'import et par type d'anomalie. |
| Unité | Pourcentage |
| Période de référence | Lot d'import |
| Source | Rapport d'import (BEN-08, MIG-01) |
| Responsable | Responsable suivi-évaluation |
| Fréquence | À chaque import |
| Règles de validation | Contrôle des totaux avant et après import ; validation du lot par le centre propriétaire des données. |
| Limites | Mesure les anomalies détectables par les règles, pas les erreurs plausibles. |

### IND-33 · Présences saisies dans les délais

| Rubrique | Contenu |
| --- | --- |
| Objectif | Garantir que l'assiduité (IND-08) reflète le terrain. |
| Formule | Séances dont les présences sont validées dans les 48 heures suivant la séance / séances tenues dans la période × 100. |
| Unité | Pourcentage |
| Période de référence | Mois |
| Source | seance, presence (saisi\_le) |
| Responsable | Responsable pédagogique |
| Fréquence | Recalcul nocturne |
| Règles de validation | Une saisie au-delà du délai porte un motif (RG-FOR-06). |
| Limites | Le délai de 48 heures est proposé ; une connexion défaillante peut retarder la saisie sans négligence. |

### IND-34 · Contributions reçues justifiées

| Rubrique | Contenu |
| --- | --- |
| Objectif | Vérifier que les ressources affichées reposent sur des preuves. |
| Formule | Contributions au statut validée avec au moins un justificatif / contributions au statut reçue ou validée × 100 ; nombre de contributions reçues en attente de validation depuis plus de 30 jours. |
| Unité | Pourcentage ; nombre |
| Période de référence | Trimestre |
| Source | contribution, document |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Recalcul nocturne |
| Règles de validation | La cible est 100 % : une contribution validée sans justificatif est une anomalie bloquante. |
| Limites | Ne juge pas la valeur probante du justificatif, seulement sa présence. |

### IND-35 · Rapports transmis dans les délais

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la régularité du reporting des centres vers la Direction Générale (PRD, objectif O3). |
| Formule | Rapports périodiques attendus transmis au plus tard à la date limite / rapports attendus × 100. |
| Unité | Pourcentage |
| Période de référence | Mois, trimestre |
| Source | Calendrier des rapports et journal de transmission (REP) |
| Responsable | Responsable suivi-évaluation |
| Fréquence | À chaque date limite |
| Règles de validation | Le calendrier des rapports est validé par la Direction Générale. |
| Limites | Un rapport transmis à temps peut être incomplet ; lire avec IND-30. |

## 7. Fiches adoption

Ces cinq indicateurs mesurent l'usage de l'outil par les équipes. Ils alimentent le bilan d'adoption du pilote et la décision d'extension. Aucun n'est publié de façon nominative : l'objectif est d'adapter la formation et l'assistance, pas d'évaluer les personnes.

### IND-40 · Utilisateurs actifs

| Rubrique | Contenu |
| --- | --- |
| Objectif | Vérifier que les comptes créés servent réellement. |
| Formule | Comptes actifs ayant au moins une connexion et une action métier enregistrée dans les 30 derniers jours / comptes actifs × 100, par centre et par rôle. Exclus : comptes techniques et d'administration. |
| Unité | Pourcentage ; nombre |
| Période de référence | Fenêtre glissante de 30 jours |
| Source | journal\_audit, utilisateur, affectation |
| Responsable | Administrateur national |
| Fréquence | Recalcul nocturne ; lecture hebdomadaire au pilote |
| Règles de validation | Un compte sans connexion depuis 90 jours est signalé pour revue des droits (SEC). |
| Limites | Une connexion n'est pas un usage complet ; un compte partagé, interdit, fausserait le chiffre. |

### IND-41 · Taux d'utilisation des modules

| Rubrique | Contenu |
| --- | --- |
| Objectif | Repérer les fonctions boudées et les parcours qui restent sur papier. |
| Formule | Pour chaque module, part des centres où le module est activé ayant enregistré au moins une action métier dans le mois ; pour les présences, part des séances tenues dont les présences sont saisies dans l'outil. |
| Unité | Pourcentage |
| Période de référence | Mois |
| Source | journal\_audit, seance |
| Responsable | Administrateur national |
| Fréquence | Mensuelle |
| Règles de validation | Le nombre de séances tenues est confirmé par le responsable pédagogique. |
| Limites | Ne dit pas pourquoi un module est peu utilisé ; à lire avec IND-42 et IND-43. |

### IND-42 · Demandes d'assistance

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer la charge d'assistance et les difficultés récurrentes. |
| Formule | Nombre de demandes ouvertes dans la période, par catégorie (accès, saisie, anomalie, demande d'évolution), et délai médian de résolution. |
| Unité | Nombre ; jours |
| Période de référence | Mois |
| Source | Outil de suivi des demandes d'assistance (hors CAEF Connect au MVP) |
| Responsable | Administrateur national |
| Fréquence | Mensuelle |
| Règles de validation | Toute demande est catégorisée à sa clôture. |
| Limites | Une hausse au démarrage est normale et signe d'usage ; c'est la tendance qui compte. |

### IND-43 · Satisfaction des utilisateurs

| Rubrique | Contenu |
| --- | --- |
| Objectif | Recueillir le ressenti des équipes et les difficultés déclarées (Plan de déploiement). |
| Formule | Score moyen sur une échelle de 1 à 5 à un questionnaire court et anonyme, avec le taux de réponse. |
| Unité | Score sur 5 ; pourcentage de réponse |
| Période de référence | Fin de formation des utilisateurs, mi-pilote, fin de pilote, puis semestrielle |
| Source | Questionnaire |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Par vague d'enquête |
| Règles de validation | Résultat non publié si moins de cinq réponses dans un centre. |
| Limites | Déclaratif ; sensible au moment de l'enquête et au taux de réponse. |

### IND-44 · Temps de production du rapport mensuel

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer le gain de temps promis par l'outil sur le reporting (PRD, objectif O3). |
| Formule | Temps, en heures de travail, déclaré par le centre pour produire son rapport mensuel ; médiane des centres. Comparaison avec la situation de référence mesurée avant le pilote. |
| Unité | Heures |
| Période de référence | Mois |
| Source | Déclaration du responsable de centre |
| Responsable | Responsable suivi-évaluation |
| Fréquence | Mensuelle au pilote, puis trimestrielle |
| Règles de validation | Mesure de référence faite par la même méthode avant la mise en service. |
| Limites | Déclaratif et approximatif ; utile en tendance, pas en valeur absolue. |

## 8. Fiches boutique, revenus des productrices et clôture mensuelle

Ces six indicateurs mesurent l'activité des boutiques où presque tous les CAEF vendent leur production, et les revenus qu'en tirent les productrices (bénéficiaires ou groupements en dépôt-vente). Ils viennent d'une demande du porteur de projet (12/10/2026) : ni le DM ni le CDC ne les prévoient. Leurs fiches sont au statut proposé, à valider (H10), et leur calcul suppose le module boutique (BOU-01 à BOU-11), livré dans le lot 1 (H14 tranchée par le porteur de projet le 12/10/2026, à formaliser par la Direction Générale). IND-50 suit la clôture mensuelle rapprochée (SRC-02), qui fait de CAEF Connect la seule source des chiffres du comptable et du responsable de centre.

Au tableau de bord de centre, ils s'affichent dès la livraison du module. Au niveau national, ils n'entrent au tableau de bord qu'une fois leur fiche validée et la consolidation BOU-12 livrée (P2), sous forme d'agrégats sans aucun nom de productrice. Montants entiers, dans la devise du centre (franc guinéen, GNF). Pour un centre où le module boutique est désactivé, ils s'affichent « Module non activé » (section 2.2) ; les ventes de la salle d'exposition sont comprises dans les chiffres de la boutique (BOU-15).

### IND-45 · Chiffre d'affaires de la boutique

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer ce que la boutique du centre vend de sa production et des produits en dépôt-vente. |
| Formule | Somme des ventes au statut validée, non annulées, dont la date de vente tombe dans la période (quantité × prix unitaire appliqué, moins remise), par centre, avec ventilation par produit, catégorie et origine (atelier du centre, dépôt-vente, groupement, achat pour revente). Les ventes des journées dont la clôture de caisse est validée comptent en vérifié ; celles des journées non encore clôturées s'affichent à part, en déclaratif. Exclus : ventes annulées et leurs contre-écritures. |
| Unité | Devise du centre (franc guinéen au pilote), montant entier |
| Période de référence | Jour, mois, trimestre, année |
| Source | vente, ligne\_vente, produit, session\_caisse |
| Responsable | Comptable de centre (CPT) |
| Fréquence | Recalcul nocturne ; lecture quotidienne au centre |
| Règles de validation | Clôture de caisse quotidienne validée par le comptable ou, à défaut, le RC ou le RA, jamais par l'auteur des ventes (BOU-05) ; numérotation continue des reçus (BOU-06). Agrégat national seulement après validation de la fiche et livraison de BOU-12. |
| Limites | Chiffre d'affaires, ni marge (coût de revient hors périmètre, BOU-14) ni chiffre comptable ; inclut la part due aux productrices (lire avec IND-47). |

### IND-46 · Nombre de ventes

| Rubrique | Contenu |
| --- | --- |
| Objectif | Suivre le rythme d'activité de la boutique. |
| Formule | Nombre de reçus au statut validée, non annulés, dont la date de vente tombe dans la période, par centre ; panier moyen = IND-45 / IND-46. Même séparation vérifié / déclaratif que IND-45. Exclus : ventes annulées et numéros consignés comme annulés. |
| Unité | Nombre |
| Période de référence | Jour, mois |
| Source | vente, session\_caisse |
| Responsable | Comptable de centre (CPT) |
| Fréquence | Recalcul nocturne |
| Règles de validation | Continuité de la numérotation des reçus par point de vente (BOU-06) ; un reçu papier de secours est saisi le jour même avec son numéro en référence. |
| Limites | Indicateur de centre, non consolidé au niveau national ; une vente de plusieurs articles compte pour une. |

### IND-47 · Revenus reversés aux productrices

| Rubrique | Contenu |
| --- | --- |
| Objectif | Rendre mesurable le revenu que les bénéficiaires tirent de leur production (indicateur d'autonomisation économique). |
| Formule | Somme des reversements au statut payé dont la date de paiement tombe dans la période, et nombre de productrices distinctes payées, par centre. Le solde restant dû (ventes en dépôt-vente moins part du centre, moins reversements payés) s'affiche à côté, jamais additionné. Exclus : reversements préparés ou validés mais non payés. |
| Unité | Devise du centre (franc guinéen au pilote) ; nombre de productrices |
| Période de référence | Mois, trimestre, année |
| Source | reversement, depot, vente, ligne\_vente, beneficiaire |
| Responsable | Comptable de centre (CPT) ; validation par le RC ou le RA |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | Reversement préparé par le comptable, validé par le RC ou le RA, avec date et pièce justificative (BOU-08) ; qui l'a préparé et validé ne le marque pas « payé ». Au niveau national : montant total et nombre de productrices seulement, sans nom, petits effectifs masqués (principe 6). |
| Limites | Ne couvre que les ventes de la boutique du centre, pas les autres revenus des bénéficiaires ; une productrice peut être un groupement. |

### IND-48 · Taux de clôtures de caisse avec écart

| Rubrique | Contenu |
| --- | --- |
| Objectif | Suivre la fiabilité de la caisse (contrôle interne). |
| Formule | Clôtures de caisse validées avec écart / clôtures de caisse validées dans la période × 100, par centre ; montant cumulé des écarts affiché à côté. Exclus : sessions de caisse ouvertes ou comptées non validées. |
| Unité | Pourcentage ; montant |
| Période de référence | Mois |
| Source | session\_caisse |
| Responsable | Comptable de centre (CPT) |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | Écart motivé à chaque clôture, validée par une autre personne que l'auteur des ventes de la journée (BOU-05). Seuil d'alerte à fixer par la Direction Générale après la situation de référence. |
| Limites | Contrôle interne du centre, non publié au niveau national ; un taux nul peut cacher des clôtures non faites (lire avec le nombre de journées de vente sans clôture). |

### IND-49 · Productrices actives en boutique

| Rubrique | Contenu |
| --- | --- |
| Objectif | Mesurer combien de productrices trouvent un débouché par la boutique du centre. |
| Formule | Nombre de productrices distinctes (bénéficiaires ou groupements déposants) ayant au moins une vente validée non annulée d'un de leurs produits dans la période, par centre. Au niveau national, une productrice n'est comptée qu'une fois. Même séparation vérifié / déclaratif que IND-45. |
| Unité | Nombre |
| Période de référence | Mois, trimestre, année |
| Source | vente, ligne\_vente, produit, depot, beneficiaire |
| Responsable | Responsable de centre |
| Fréquence | Recalcul nocturne |
| Règles de validation | La productrice déposante est une bénéficiaire existante ou un groupement enregistré. Au niveau national : effectif agrégé sans nom, « < 5 » sous le seuil (principe 6). |
| Limites | Ne compte pas la production du centre sans déposante identifiée ; une productrice qui vend hors de la boutique n'est pas vue. |

### IND-50 · Clôtures mensuelles rapprochées dans les délais

| Rubrique | Contenu |
| --- | --- |
| Objectif | Vérifier que le centre tient une seule version de ses chiffres : ventes, caisses, reversements et contributions financières reçues rapprochés chaque mois (contrôle interne, SRC-01 et SRC-02). |
| Formule | Mois dont la clôture mensuelle est validée au plus tard le 10 du mois suivant / mois écoulés de la période × 100, par centre. Une clôture « validée avec écart » compte si l'écart est motivé ; le nombre de mois validés avec écart s'affiche à côté. Exclus : le mois en cours et un mois encore ouvert avant le 10 du mois suivant. |
| Unité | Pourcentage ; nombre de mois |
| Période de référence | Mois, trimestre, année |
| Source | cloture\_mensuelle, ligne\_rapprochement |
| Responsable | Comptable de centre (CPT) pour la vérification ; validation par le RC ou, en intérim, le RA |
| Fréquence | Recalcul nocturne ; lecture mensuelle |
| Règles de validation | État de rapprochement généré par l'outil, vérifié par le comptable puis validé par le RC ou le RA, jamais par la même personne (RG-SRC-02) ; chaque écart avec les pièces (caisse physique, relevés, carnet de reçus) est motivé ; après validation, le mois est verrouillé et toute correction passe par une écriture de régularisation datée du mois courant (RG-SRC-03). Totaux par flux et par devise. |
| Limites | Contrôle interne du centre, non publié au niveau national ; mesure la tenue des délais et le rapprochement, pas l'exactitude des pièces elles-mêmes. Couvre les seuls flux saisis dans CAEF Connect (RG-SRC-01). |

## 9. Points à arbitrer et validation

### 9.1 Points à arbitrer

Ces choix touchent plusieurs fiches ; chacun a une position d'attente qui permet de construire et de tester sans bloquer.

| Code | Question | Position d'attente | Qui décide |
| --- | --- | --- | --- |
| R1 | Définition d'une bénéficiaire active (IND-03) | Inscription en cours ou achevée depuis moins de 90 jours | Direction Générale, sur proposition du suivi-évaluation |
| R2 | Devise de consolidation (GNF, devise de travail ; USD ou EUR possibles pour les contributions) et source des taux datés | Totaux affichés par devise ; pas de total multi-devises sans taux daté | Direction Générale et direction financière |
| R3 | Seuil de masquage des petits effectifs | Moins de cinq personnes, hors périmètre du centre | Direction Générale, avec le référent protection des données |
| R4 | Méthodes de valorisation des dons en nature (IND-24) | Prix d'achat justifié, sinon valeur de marché documentée, sinon pas de valeur | Direction financière |
| R5 | Échéances de suivi de l'insertion (IND-12) | 6 mois après la sortie | Direction Générale et partenaires concernés |
| R6 | Indicateurs déjà exigés par les partenaires et bailleurs (H10) | Catalogue actuel ; ajout par révision de fiche | Responsable RSE et suivi-évaluation |
| R7 | Ventilations sociodémographiques autorisées (âge, situation, handicap) | Tranche d'âge seulement ; aucune donnée sensible collectée par défaut (BEN-01) | Direction Générale, avec le référent protection des données |

### 9.2 Validation du référentiel

Le référentiel est validé en deux temps. Avant le pilote, la Direction Générale valide les fiches du lot 1 qui alimentent le tableau de bord national. Au bilan du pilote, chaque fiche est relue à la lumière des données réelles, les cibles sont fixées à partir de la situation de référence, et les fiches encore au statut proposé sont validées.

- [ ] Trancher R1 à R7 ou confirmer les positions d'attente.
- [ ] Valider les fiches IND-01 à IND-10, IND-30 à IND-33, IND-35 et IND-40 à IND-44 avant le pilote.
- [ ] Mesurer la situation de référence (IND-10, IND-35, IND-44) dans le centre pilote, le CAEF Cameroun (Dixinn), avant la mise en service.
- [ ] Faire tester chaque formule par la recette (plan de tests, campagne fonctionnelle) sur un jeu de données dont le résultat est connu à l'avance.
- [ ] Valider les fiches IND-20 à IND-28 et IND-34 avant l'ouverture du module RSE.
- [ ] Valider les fiches IND-45 à IND-50 (proposées, à valider) avant l'ouverture du module boutique et de la clôture mensuelle au pilote (H14 tranchée) ; pas d'entrée au tableau de bord national avant cette validation et la livraison de BOU-12.
- [ ] Fixer les cibles chiffrées au bilan du pilote.
