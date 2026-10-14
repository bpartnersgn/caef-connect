# Budget et modèle économique CAEF Connect

Oct 12, 2026 · @Bangoura

## 1. Objet et statut

Le budget de CAEF Connect n'est pas encore arrêté : il sera établi à l'issue du cadrage fonctionnel et technique, après validation du périmètre du MVP et des besoins réels des centres CAEF. Ce document fixe la structure du budget (composantes, postes, scénarios, modèle économique) ; il ne contient volontairement aucun montant. Chaque poste est à chiffrer sur devis de prestataires et de fournisseurs.

Mise à jour du 13/10/2026 : le porteur de projet demande que la plateforme fonctionne sans accès à Internet, avec synchronisation automatique au retour du réseau, et qu'elle intègre le paiement par Mobile Money de la scolarité et des services associés (à formaliser par la Direction Générale). Ces deux exigences d'architecture ajoutent les postes C1.11 à C1.13, C2.5 à C2.7 et C4.10, et précisent l'équipement des appareils de terrain.

| Point | Règle retenue dans ce document |
| --- | --- |
| Montants | Aucun montant n'est retenu à ce stade ; chaque poste est **à chiffrer sur devis**, auprès d'au moins deux prestataires ou fournisseurs, avec des prix relevés à Conakry |
| Devises | Franc guinéen (GNF) pour la proposition consolidée ; devis en USD ou EUR acceptés ; pas de total mélangeant plusieurs devises sans taux daté |
| Périmètre à chiffrer | Lot 1 du MVP : socle (centres, utilisateurs, bénéficiaires, formations, présences, tableaux de bord, rapports, sécurité), RSE, boutique et clôture mensuelle avec source unique des chiffres (SRC), fonctionnement hors ligne avec synchronisation automatique, scolarité et paiements Mobile Money ; crèche hors chiffrage (plus tard) |
| Centre pilote | Un seul centre, le CAEF Cameroun (quartier Cameroun, commune de Dixinn, Conakry, Guinée) ; tout y est aujourd'hui sur papier (livrets, feuilles volantes) |
| Architecture de référence | Celle proposée par le DAT : application web unique (Django ou Laravel), PostgreSQL, stockage de documents compatible S3, conteneurs Docker ; application de terrain installable (PWA) qui fonctionne hors ligne et se synchronise seule (DAT § 4.5) ; module de paiements relié à un agrégateur ou à un opérateur Mobile Money (DAT § 4.6) ; sauvegardes en option RPO 15 minutes et RTO 8 heures ouvrées |

## 2. Les quatre composantes

Le budget est structuré en quatre composantes, chiffrées séparément pour distinguer le coût initial des dépenses récurrentes et le logiciel du matériel.

| Composante | Ce qu'elle couvre | Facteurs de coût | Nature |
| --- | --- | --- | --- |
| 1. Développement du MVP | Conception fonctionnelle, développement de la plateforme, tests, sécurisation des accès, déploiement initial, formation des utilisateurs du centre pilote ; périmètre maîtrisé, répondant aux besoins prioritaires, avant toute généralisation | Périmètre du lot 1 validé ; composition de l'équipe (locale, régionale ou internationale) ; reprise des registres papier ; déplacements sur site | Ponctuel |
| 2. Hébergement et infrastructure | Serveurs ou services cloud (calcul, base, stockage), environnements de production et de préproduction, sauvegardes et second site, noms de domaine, certificats, supervision, passerelle de paiement et envoi de SMS | Architecture retenue ; lieu d'hébergement (H7) ; nombre de centres et d'utilisateurs ; volume de données et de paiements ; exigences de sécurité ; option RPO et RTO | Récurrent (mensuel) |
| 3. Maintenance et accompagnement | Mises à jour, correction des anomalies, surveillance technique, assistance aux utilisateurs, évolutions fonctionnelles, audits de sécurité, formation des nouveaux utilisateurs ; niveau de service à définir | Niveaux de service (délais P1 à P3 du DAT § 9.1) ; rythme des évolutions ; rotation du personnel des centres | Récurrent (annuel), distinct du coût initial |
| 4. Équipement et déploiement des centres | Ordinateurs, tablettes ou téléphones, imprimante et scanner, imprimante de reçus, connectivité, alimentation de secours, accessoires | Diagnostic des équipements existants (au centre pilote : rien d'informatisé aujourd'hui) ; usages prévus ; prix à Conakry ; forfait de données mobiles | Ponctuel, plus connectivité et renouvellement récurrents ; chiffrage distinct du logiciel |

## 3. Structure de chiffrage

Les tableaux ci-dessous listent les postes à faire chiffrer. La colonne « Montant » reste vide jusqu'à réception des devis.

### 3.1 Composante 1 : développement du MVP (ponctuel)

| Poste | Ce qu'il couvre | Montant |
| --- | --- | --- |
| C1.1 Cadrage et diagnostic terrain | Processus, inventaire des registres papier, équipement, connectivité | À chiffrer sur devis |
| C1.2 Conception | Parcours et maquettes UX, SFD finale | À chiffrer sur devis |
| C1.3 Développement lot 1 : socle | Centres, utilisateurs, bénéficiaires, formations, présences, tableaux de bord, rapports, sécurité applicative | À chiffrer sur devis |
| C1.4 Développement lot 1 : RSE | Partenaires, pipeline, conventions, contributions, tableau de bord RSE | À chiffrer sur devis |
| C1.5 Développement lot 1 : boutique et clôture mensuelle SRC | Produits, dépôts, ventes, caisse, reversements, clôture et rapprochement mensuels | À chiffrer sur devis |
| C1.6 Tests et recette | Plan de tests, recette métier, tests de charge, tests hors ligne et de paiement sur appareils réels | À chiffrer sur devis |
| C1.7 Sécurité | Revue de code, test d'intrusion externe avant production | À chiffrer sur devis |
| C1.8 Reprise des registres papier | Saisie, numérisation, rapprochement des chiffres de la comptable et de la responsable (SRC-03) | À chiffrer sur devis |
| C1.9 Formation et conduite du changement au centre pilote | Formateur, supports, logistique | À chiffrer sur devis |
| C1.10 Déploiement initial | Environnements, chaîne de livraison, mise en production, accompagnement sur site au démarrage | À chiffrer sur devis |
| C1.11 Développement lot 1 : hors ligne et synchronisation | Application de terrain installable, base locale chiffrée, journal d'opérations, synchronisation automatique, résolution des conflits, enrôlement et révocation des appareils (OFF-01 à OFF-08) | À chiffrer sur devis |
| C1.12 Développement lot 1 : scolarité et paiements Mobile Money | Services payants, tarifs, échéances, exonérations, encaissements, intégration de la passerelle, rapprochement quotidien, remboursements (PAY-01 à PAY-11) | À chiffrer sur devis |
| C1.13 Avis juridique et contrat de paiement | Avis sur la réglementation de la Banque centrale de la République de Guinée applicable aux paiements marchands ; ouverture du compte marchand (H16) | À chiffrer sur devis |
| **Sous-total composante 1** |  | **À chiffrer sur devis** |

### 3.2 Composante 2 : hébergement et infrastructure (récurrent)

| Poste | Ce qu'il couvre | Montant par an |
| --- | --- | --- |
| C2.1 Hébergement production et préproduction | Calcul, PostgreSQL, stockage S3 | À chiffrer sur devis |
| C2.2 Sauvegardes et second site | Option RPO 15 min, RTO 8 h | À chiffrer sur devis |
| C2.3 Supervision et suivi des erreurs | Outils auto-hébergés ou service payant | À chiffrer sur devis |
| C2.4 Noms de domaine et certificats | Domaine de la plateforme, certificats TLS | À chiffrer sur devis |
| C2.5 Passerelle de paiement | Abonnement ou frais fixes de l'agrégateur ou de l'opérateur, si la grille en prévoit | À chiffrer sur devis |
| C2.6 SMS | Avis d'échéance, confirmations de paiement et alertes | À chiffrer sur devis |
| C2.7 Commissions Mobile Money | Pourcentage prélevé par l'opérateur sur chaque paiement ; à la charge du centre ou de la payeuse selon la politique tarifaire (H15) | Selon la grille de l'opérateur |
| **Sous-total composante 2** |  | **À chiffrer sur devis** |

### 3.3 Composante 3 : maintenance et accompagnement (récurrent)

| Poste | Ce qu'il couvre | Montant par an |
| --- | --- | --- |
| C3.1 Maintenance corrective et évolutive | Corrections, mises à jour, petites évolutions | À chiffrer sur devis |
| C3.2 Support et astreinte en heures ouvrées | Assistance aux utilisateurs, prise en charge des incidents P1 à P3 | À chiffrer sur devis |
| C3.3 Sécurité annuelle | Audit, test d'intrusion allégé | À chiffrer sur devis |
| C3.4 Formation des nouveaux utilisateurs | Rotation du personnel des centres | À chiffrer sur devis |
| **Sous-total composante 3** |  | **À chiffrer sur devis** |

### 3.4 Composante 4 : équipement du centre pilote

Les besoins exacts seront fixés par le diagnostic du centre pilote.

| Poste | Usage | Montant |
| --- | --- | --- |
| C4.1 Ordinateurs portables | Responsable, adjoint(e), comptable, saisie et accueil | À chiffrer sur devis |
| C4.2 Tablettes ou smartphones Android | Présences, formatrices, boutique, encaissements ; Android récent avec navigateur Chrome à jour et stockage suffisant pour travailler hors ligne plusieurs jours | À chiffrer sur devis |
| C4.3 Imprimante multifonction avec scanner | Rapports, numérisation des registres et des pièces | À chiffrer sur devis |
| C4.4 Imprimante de reçus | Boutique et encaissements de scolarité ; Bluetooth, utilisable sans réseau | À chiffrer sur devis |
| C4.5 Routeur 4G | Connexion du centre | À chiffrer sur devis |
| C4.6 Onduleur ou batterie de secours, parasurtenseurs | Coupures d'électricité ; kit solaire si les coupures sont longues | À chiffrer sur devis |
| C4.7 Accessoires | Disque externe pour copie hors ligne, câbles, souris, housses | À chiffrer sur devis |
| **Sous-total équipement, ponctuel** |  | **À chiffrer sur devis** |
| C4.8 Forfait de données mobiles (récurrent) | Connexion mensuelle | À chiffrer sur devis |
| C4.9 Réparation et renouvellement (récurrent) | Entretien du parc | À chiffrer sur devis |
| C4.10 Gestion de flotte des appareils, optionnelle (récurrent) | Localisation et effacement à distance des téléphones et tablettes perdus, en plus de la révocation dans l'outil | À chiffrer sur devis |
| **Sous-total équipement, récurrent** |  | **À chiffrer sur devis** |

### 3.5 Récapitulatif du pilote (un centre)

| Poste | Montant |
| --- | --- |
| Composante 1, développement du MVP | À chiffrer sur devis |
| Composante 4, équipement ponctuel | À chiffrer sur devis |
| Provision pour imprévus | À fixer avec la Direction Générale |
| **Total ponctuel** | **À chiffrer sur devis** |
| Composante 2, hébergement | À chiffrer sur devis |
| Composante 3, maintenance et accompagnement | À chiffrer sur devis |
| Composante 4, équipement récurrent | À chiffrer sur devis |
| **Total récurrent par an** | **À chiffrer sur devis** |

## 4. Scénarios

Le scénario S1, pilote d'un centre, est recommandé comme point de départ : c'est le seul engagement à prendre maintenant, S2 et S3 se décident après le bilan du pilote.

| Critère | S1 Pilote un centre sur 12 mois (recommandé) | S2 Pilote puis extension à Conakry en année 2 | S3 Généralisation nationale progressive |
| --- | --- | --- | --- |
| Périmètre | Lot 1 (socle, RSE, boutique, SRC, hors ligne, scolarité et paiements) au CAEF Cameroun (Dixinn) ; 12 mois d'exploitation après la mise en production | S1, puis 5 centres de Conakry de plus en année 2 (6 au total) ; ajustements après pilote et consolidation multi-centres | S1, puis extension par vagues à l'ensemble des centres (hypothèse de volumétrie du DAT § 8.1) |
| Coût ponctuel | À chiffrer sur devis | S1 plus, par centre ajouté : équipement, reprise des registres, formation et déploiement ; plus les évolutions logicielles multi-centres | S1 plus, par centre ajouté : équipement, reprise des registres, formation et déploiement ; plus la consolidation nationale et les outils d'administration |
| Coût récurrent annuel | À chiffrer sur devis | Partie plateforme plus une partie par centre (connexion, entretien du matériel) | Partie plateforme renforcée (hébergement, support) plus une partie par centre |
| Coût total sur 5 ans | À chiffrer sur devis | À chiffrer sur devis | À chiffrer sur devis |
| Risques principaux | Conduite du changement dans un centre parti du papier ; double saisie papier et outil si la reprise traîne ; pas de financeur des coûts récurrents à la fin du pilote | Extension lancée avant un bilan solide ; diversité des pratiques entre centres ; capacité de formation et de support | Coûts récurrents sans budget pérenne ; connectivité et électricité inégales hors de Conakry ; besoin d'une équipe nationale d'administration et de formation |

Pour comparer les scénarios, les devis devront distinguer le coût ponctuel du pilote, le coût par centre ajouté et le coût récurrent selon le nombre de centres.

## 5. Modèle économique

Le pilote serait porté par une offre de TIKA (Agence turque de coopération et de coordination) à la Direction Générale des CAEF, dans une logique de contribution à la modernisation des centres ; les coûts récurrents doivent avoir un financeur identifié avant la fin du pilote. L'offre TIKA reste à confirmer.

### 5.1 Offre de mise à disposition initiale par TIKA

Recommandation : demander à TIKA de couvrir le coût ponctuel de S1 et **12 à 24 mois** d'hébergement, de maintenance et de support après la mise en production, le temps de mettre en place le financement pérenne.

Ce que la proposition de TIKA doit préciser par écrit :

| Point | Question à poser |
| --- | --- |
| Développement | Qui réalise (prestataire, nationalité, équipe locale associée) ? Périmètre exact : socle, RSE, boutique, SRC ? |
| Hébergement initial | Quel hébergeur et quel pays (compatible avec l'avis juridique, H7) ? Pour quelle durée ? |
| Équipements | Quels matériels, en quelle quantité, avec quelle garantie ? |
| Formation et accompagnement | Combien de jours sur site, pour qui, et quel transfert de compétences aux CAEF ? |
| Maintenance et support | Quelle durée, quels délais de prise en charge (P1 à P3) ? |
| Propriété | Code source, documentation et données appartiennent-ils aux CAEF dès la livraison ? |
| Sortie | Que se passe-t-il à la fin de la prise en charge : passation, export des données, changement d'hébergeur sans réécriture ? |
| Hors ligne et paiements | L'offre couvre-t-elle l'application hors ligne et l'intégration Mobile Money ? Qui négocie le contrat avec l'agrégateur ou l'opérateur, et au nom de quelle entité est ouvert le compte marchand ? |

### 5.2 Financement des coûts récurrents

| Source possible | Ce qu'elle pourrait financer | Condition |
| --- | --- | --- |
| Budget de l'État, via le ministère de tutelle | Hébergement, maintenance, support : ligne budgétaire annuelle | Inscription au budget avant la fin du pilote |
| Direction Générale des CAEF | Administration nationale, référents des centres, connectivité | Postes et temps dédiés identifiés |
| Partenaires techniques et financiers | Extension à de nouveaux centres (équipement, reprise, formation), évolutions | Projet d'extension chiffré et résultats du pilote |
| Mécénat RSE d'entreprises | Équipement d'un centre, forfaits de données, formation | Le module RSE documente lui-même la valeur rendue aux partenaires (conventions, contributions, justificatifs, tableau de bord) |

Principes à respecter :

- Aucun prélèvement sur les recettes de la boutique revenant aux femmes productrices pour financer la plateforme.
- Pas de dépendance à un fournisseur : composants open source, export complet des données, hébergeur remplaçable (DAT § 9.2).
- Le code source et les données appartiennent aux CAEF.
- Budget présenté par devise (GNF, USD, EUR), sans total multi-devises sans taux daté.
- Les commissions Mobile Money sur les ventes en dépôt-vente sont prises sur la part du centre, jamais sur celle de la productrice (RG-PAY-12).
- Les fonds payés par Mobile Money arrivent directement sur le compte marchand des CAEF ; ni la plateforme ni son prestataire ne les détiennent.

### 5.3 Conditions de pérennité

| Condition | Échéance proposée |
| --- | --- |
| Financeur des coûts récurrents identifié et engagé | Avant la fin du pilote |
| Transfert de compétences à une équipe désignée par les CAEF (administrateur national, référents de centre) | Pendant le pilote, avec rapport |
| Contrat de maintenance avec niveaux de service et réversibilité | Avant la mise en production |
| Bilan des coûts réels d'exploitation comparés au budget de référence | À la fin du pilote, avant toute extension |

## 6. Prochaines étapes et points à décider

La prochaine étape est de réaliser le cadrage du MVP, d'établir un budget de référence et de comparer plusieurs scénarios de déploiement avant de soumettre une proposition financière consolidée.

1. Cadrage du MVP au CAEF Cameroun (Dixinn) : processus réels, inventaire des livrets et feuilles volantes, validation du périmètre du lot 1.
2. Diagnostic de l'équipement, de la connectivité et de l'alimentation électrique du centre pilote, pour fixer la composante 4.
3. Choix du lieu d'hébergement (H7) après avis juridique sur la résidence des données, et de l'option RPO et RTO.
4. Demande de devis à au moins deux prestataires, poste par poste selon la section 3, sur cinq ans.
5. Confirmation par TIKA de son offre et de ce qu'elle couvre (§ 5.1).
6. Budget de référence et proposition financière consolidée, en GNF à un taux daté.
7. Validation par la Direction Générale des CAEF du scénario retenu (S1 recommandé) et du financeur des coûts récurrents.
8. Arrêt de la politique tarifaire de la scolarité et des services (H15) et choix de la passerelle Mobile Money, avec l'avis juridique (H16), sur comparaison des grilles d'au moins deux agrégateurs ou opérateurs.

| Point à décider | Qui décide |
| --- | --- |
| Périmètre du lot 1 et budget de référence | Direction Générale des CAEF, sur proposition du comité de pilotage |
| Lieu d'hébergement (H7) et option RPO et RTO | Direction Générale, après avis juridique et chiffrage |
| Couverture et durée de l'offre TIKA (12 ou 24 mois de récurrent) | Direction Générale et TIKA |
| Financeur des coûts récurrents après la prise en charge initiale | Direction Générale, ministère de tutelle, partenaires |
| Scénario d'extension (S2 ou S3) | Comité de pilotage, après le bilan du pilote |
| Politique tarifaire de la scolarité et des services, prise en charge de la commission Mobile Money (H15) | Direction Générale des CAEF |
| Passerelle Mobile Money et compte marchand (H16) | Direction Générale, après avis juridique et comparaison des grilles |
| Durée maximale de travail hors ligne (72 heures proposées) et gestion de flotte des appareils | Comité de pilotage, sur avis du prestataire |
