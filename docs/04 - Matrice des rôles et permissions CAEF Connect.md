# Matrice des rôles et permissions CAEF Connect

Oct 12, 2026 · @Bangoura · mis à jour le 14/10/2026 (transcription dans le backend, section 5)

## 1. Principes et légende

Cette matrice transforme la matrice simplifiée du DM § 8 en droits par action pour les onze rôles internes du MVP, calés sur l'organigramme des centres (section 2.1), plus le rôle de gérante de la salle d'exposition et de la boutique, active dès le pilote avec le module boutique ; elle est la référence de configuration des rôles et de la recette de sécurité. Elle reste une proposition à valider par la Direction Générale (PRD H4).

**Principes appliqués :**

1. **Moindre privilège.** Un rôle n'a que les droits nécessaires à sa fonction ; tout droit absent de la matrice est refusé (DM M2).
2. **Périmètre.** Un droit s'exerce sur un périmètre : ses sessions, son centre, ses centres affectés ou le réseau. Le périmètre est contrôlé côté serveur (SEC-01).
3. **Agrégé par défaut au niveau national.** La Direction Générale et le Responsable RSE voient des chiffres, pas des noms de bénéficiaires, sauf habilitation nominative explicite.
4. **Séparation des tâches.** Celui qui saisit une opération financière ou une dérogation ne la valide pas.
5. **Administration sans contenu.** L'administrateur national gère comptes et paramètres sans accès aux dossiers nominatifs (DM § 7.1).

**Légende des actions :** L = consulter ; C = créer ; M = modifier ; V = valider ou changer un statut soumis à validation ; E = exporter ; A = archiver, désactiver ou clôturer ; — = aucun droit. La suppression physique n'existe pour aucun rôle (RG-GEN-03).

**Légende des périmètres :** (s) ses sessions affectées ; (c) son ou ses centres affectés ; (n) réseau national ; (ag) agrégé sans données nominatives ; (p) sa propre fiche. Sans mention, le périmètre est (c).

**Abréviations des rôles :** ADM administrateur national ; DG Direction Générale ; RC responsable de centre ; RA responsable adjoint de centre ; AA assistante du responsable de centre (agent administratif) ; RP responsable pédagogique ; FO moniteur, enseignant ou encadreur (formateur) ; RSE responsable RSE et partenariats ; SE responsable suivi-évaluation ; CPT chef comptable du centre (comptable de centre) ; VB gérante de la salle d'exposition et de la boutique (vendeur ou vendeuse de boutique, active dès le pilote avec le module boutique) ; CMT chef matériels.

## 2. Rôles et périmètres

Onze rôles internes sont actifs au MVP, dont le responsable adjoint de centre (RA) et le chef comptable du centre (CPT), ajoutés à la demande du porteur de projet et absents du DM et du CDC, et le chef matériels (CMT), présent dans l'organigramme des centres ; le rôle VB est actif dès le pilote avec le module boutique, inclus dans le lot 1 (H14 tranchée par le porteur de projet le 12/10/2026, à formaliser par la Direction Générale) ; trois autres sont prévus dans le modèle de droits mais désactivés jusqu'à l'arrivée de leur module (PRD écarts A10 et A11).

| Rôle | Périmètre par défaut | Accès nominatif aux bénéficiaires | Double authentification | Au MVP |
| --- | --- | --- | --- | --- |
| ADM Administrateur national | Réseau, technique seulement | Non | Obligatoire | Oui |
| DG Direction Générale | Réseau | Non par défaut ; sur habilitation nominative tracée | Obligatoire | Oui |
| RC Responsable de centre | Son centre | Oui | Recommandée | Oui |
| RA Responsable adjoint de centre | Son centre | Oui, comme le RC | Recommandée | Oui |
| AA Assistante du responsable de centre (agent administratif) | Son centre | Oui | Non | Oui |
| RP Responsable pédagogique (fonction attribuée par cumul, section 2.1) | Son centre | Oui, données utiles à la formation | Non | Oui |
| FO Moniteur, enseignant ou encadreur (formateur) | Ses sessions | Nom, prénom et code des inscrites seulement | Non | Oui |
| RSE Responsable RSE et partenariats | Réseau pour partenaires et RSE | Non ; agrégés seulement | Recommandée | Oui |
| SE Responsable suivi-évaluation | Réseau ou centre selon affectation | Oui, pour le contrôle qualité | Recommandée | Oui |
| CPT Chef comptable du centre | Son centre (plusieurs centres possibles par cumul) | Non, sauf identité minimale (nom, prénom, code, téléphone) des productrices déposantes pour les reversements boutique, et des bénéficiaires dont il traite les paiements de scolarité | Obligatoire | Oui |
| VB Gérante de la salle d'exposition et de la boutique | La salle d'exposition et la boutique de son centre | Non ; nom et code d'une productrice déposante sur l'article seulement | Non | Oui, si le module boutique et salle d'exposition est activé pour le centre (lot 1) |
| CMT Chef matériels | Son centre | Non | Non | Oui, en consultation (section 2.1) |
| Responsable insertion | Son centre | Oui | Non | Non, lot 2 |
| Responsable communication | Contenus publics | Non | Non | Non, écart A4 |
| Partenaire externe, bénéficiaire | Ses propres informations | Non (sa propre fiche pour la bénéficiaire) | Selon portail | Non, lot 3 |

Un utilisateur peut cumuler des rôles sur un ou plusieurs centres (par exemple RC au CAEF Cameroun (Dixinn) et SE dans un autre centre après l'extension) ; ses droits sont l'union des droits de chaque affectation, chacun limité à son propre périmètre. Le cumul RSE et valideur financier sur une même opération est interdit (section 4).

### 2.1 Organigramme des centres et rôles de l'outil

L'organigramme d'un CAEF compte huit fonctions. Chacune correspond à un rôle de l'outil, sauf la cheffe de classe ; l'écran affiche l'intitulé de l'organigramme, et les documents de conception gardent les libellés fonctionnels (agent administratif, formateur, comptable de centre, vendeur ou vendeuse de boutique).

| Fonction dans l'organigramme | Rôle dans l'outil | Remarque |
| --- | --- | --- |
| Responsable du centre | RC | Valide pour le centre |
| Adjoint du responsable | RA | Valide seulement pendant un intérim déclaré, sauf en boutique (règle 6) |
| Assistante de la responsable du centre | AA | Accueil, candidatures et dossiers, encaissements de scolarité |
| Chef comptable | CPT | Double authentification obligatoire ; aucun dossier bénéficiaire (règle 7) |
| Chef matériels | CMT | Consultation seulement au MVP (ci-dessous) |
| Moniteurs (enseignants et encadreurs) | FO | Un compte par moniteur, limité à ses sessions |
| Cheffe de classe (une élève) | Aucun compte au MVP | Bénéficiaire désignée sur son inscription (ci-dessous) |
| Gérante salle d'exposition et boutique | VB | Seulement si le module boutique et salle d'exposition est activé pour le centre (règle 9) |

**Responsable pédagogique.** L'organigramme ne prévoit pas ce poste. Le rôle RP est conservé, car il planifie les sessions et affecte les moniteurs ; il est attribué par cumul à une personne de l'organigramme, par défaut l'adjoint du responsable ou un moniteur désigné par le responsable du centre.

**Chef matériels (CMT).** Au MVP, le CMT consulte la fiche du centre, les sessions et séances du centre sans les noms des inscrites, les services et tarifs, et le registre des appareils du centre pour l'inventaire physique ; il n'a aucun autre droit et n'accède à aucun dossier bénéficiaire. Sa fonction (matériel pédagogique, équipements, entretien) sera couverte par le module matériels et équipements (PRD ADM-07, P2), désactivable par centre comme les autres modules.

**Cheffe de classe.** C'est une élève : elle reste une bénéficiaire et n'a pas de compte au MVP, les comptes de bénéficiaires arrivant avec le portail (lot 3). Le moniteur ou le RP la désigne sur son inscription à la session ; la mention figure sur la feuille de présence et la liste de la session.

## 3. Matrice détaillée

La matrice compte 67 objets répartis en six domaines ; chaque cellule est un cas de test de la campagne de sécurité (Plan de tests, campagne C3). « V (intérim) » signale un droit de validation que le RA n'exerce que pendant un intérim déclaré (règle 6) ; le VB n'a de droits qu'en boutique (3.5), le CPT y ajoute le rapprochement des contributions, le tableau de bord de centre et les paiements de scolarité (3.6). Le CMT n'a que les droits de consultation décrits en 2.1, et toute cellule d'un module désactivé pour le centre vaut « — » (règle 9).

### 3.1 Administration

| Objet | ADM | DG | RC | RA | AA | RP | FO | RSE | SE | CPT | VB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Centres | L C M A (n) | L (n) | L | L | L | L | — | L (n) | L (n) | — | — |
| Référentiels nationaux | L | L C M A (n) | L | L | L | L | — | L | L | — | — |
| Périodes et campagnes | L C M A (n) | L V (n), réouverture | L | L | L | L | — | L | L (n) | — | — |
| Utilisateurs et affectations | L C M A (n) | L (n) | L | L | — | — | — | — | — | — | — |
| Rôles et permissions | L (n) | L (n) | — | — | — | — | — | — | — | — | — |
| Paramètres de sécurité | L M (n), sur délégation | L (n) | — | — | — | — | — | — | — | — | — |
| Journal d'activité | L E (n) | L (n) | L | L | — | — | — | — | L (n) | — | — |
| Appareils (enrôlement, révocation) | L C A (n) | — | L C A | L | — | — | — | — | — | — | — |
| File « À résoudre » (conflits de synchronisation et écritures tardives) | — | — | L V, conflits | L V, conflits | — | — | — | — | — | L V, écritures tardives | — |
| Modules du centre (activation et désactivation) | L M (n), sur décision de la DG | L V (n) | L | L | — | — | — | — | L (n) | — | — |

### 3.2 Bénéficiaires

| Objet | ADM | DG | RC | RA | AA | RP | FO | RSE | SE | CPT | VB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dossier, identité et coordonnées | — | L (ag) | L C M A | L C M A | L C M | L | L (s), nom et code | L (ag) | L | — | — |
| Données restreintes (pièce d'identité, contact d'urgence) | — | — | L M | L M | L C M | — | — | — | L | — | — |
| Candidature | — | L (ag) | L V A | L V (intérim) A | L C M | L | — | — | L | — | — |
| Pièces justificatives | — | — | L C A | L C A | L C | — | — | — | L | — | — |
| Recherche réseau (anti-doublon) | — | — | L (n), champs minimaux | L (n), champs minimaux | L (n), champs minimaux | — | — | — | L (n) | — | — |
| Fusion de doublons | — | — | V | V (intérim) | L | — | — | — | V (n), inter-centres | — | — |
| Transfert entre centres | — | — | C (accueil), V (origine) | C (accueil), V (origine, intérim) | L | — | — | — | L (n) | — | — |
| Import de données | C, exécution technique | — | L, rapport | L, rapport | — | — | — | — | V (n) | — | — |
| Export nominatif | — | — | E | E | — | E, listes de session | — | — | E | — | — |

### 3.3 Formations

| Objet | ADM | DG | RC | RA | AA | RP | FO | RSE | SE | CPT | VB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Catalogue, formations nationales | — | L C M A (n) | L | L | L | L | L (s) | L (n) | L (n) | — | — |
| Catalogue, formations du centre | — | L (n) | L V | L V (intérim) | L | L C M A | L (s) | L (n) | L (n) | — | — |
| Sessions et séances | — | L (ag) | L A, annuler ou rouvrir | L A, annuler ou rouvrir | L | L C M A | L (s) | L (ag) | L | — | — |
| Formateurs | — | — | L | L | — | L C M A | L (p) | — | L | — | — |
| Inscriptions | — | L (ag) | L | L | L | L C M | L (s) | — | L | — | — |
| Présences | — | L (ag) | L | L | L | L C M | L C M (s), jusqu'à J+7 | — | L | — | — |
| Évaluations et résultats | — | L (ag) | L V, dérogation | L V (intérim), dérogation | — | L C M V | L C M (s) | — | L | — | — |
| Attestations | — | L (ag) | L | L | L | L C V | — | — | L | — | — |
| Export listes et résultats | — | — | E | E | — | E | — | — | E | — | — |

### 3.4 Partenaires, RSE et pilotage

| Objet | ADM | DG | RC | RA | AA | RP | FO | RSE | SE | CPT | VB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Partenaires | — | L (n) | L C | L C | — | — | — | L C M A (n) | L (n) | — | — |
| Interlocuteurs et interactions | — | L (n) | L C | L C | — | — | — | L C M (n) | L (n) | — | — |
| Opportunités et pipeline | — | L (n) | L | L | — | — | — | L C M A (n) | L (n) | — | — |
| Fiches projet des centres | — | L (n) | L C M | L C M | — | L | — | L V (n), qualification | L (n) | — | — |
| Programmes | — | L C M A (n) | L | L | — | L | — | L (n) | L (n) | — | — |
| Propositions | — | L V (n) | L V, avis | L V (intérim), avis | — | — | — | L C M (n) | L (n) | — | — |
| Conventions | — | L V (n) | L | L | — | — | — | L C M A (n) | L (n) | — | — |
| Engagements | — | L (n) | L M, engagements CAEF du centre | L M, engagements CAEF du centre | — | — | — | L C M V (n) | L (n) | — | — |
| Contributions, saisie de réception | — | L (n) | L | L | — | — | — | L C M (n) | L (n) | L M, rapprochement (CTR-09) | — |
| Contributions, validation | — | V (n) | — | — | — | — | — | — | — | — | — |
| Tableau de bord national | — | L E (n) | — | — | — | — | — | L (n), volet RSE | L E (n) | — | — |
| Tableau de bord de centre | — | L (n) | L E | L E | L | L | — | — | L | L, volets boutique et contributions | — |
| Tableau de bord RSE | — | L E (n) | L | L | — | — | — | L E (n) | L (n) | — | — |
| Rapport de centre | — | L (n) | L C V E | L C V (intérim) E | — | C | — | — | L E | — | — |
| Rapport national | — | L V E (n) | — | — | — | — | — | — | L C E (n) | — | — |
| Rapport partenaire | — | L V (n) | L | L | — | — | — | L C E (n) | L (n) | — | — |
| Fiches d'indicateurs | — | L V (n) | L | L | L | L | — | L | L C M (n) | — | — |

Le responsable de centre et son adjoint voient les partenaires, opportunités, conventions et contributions qui concernent leur centre seulement ; le périmètre (c) s'applique donc aussi à ces lignes (RG-PAR-07).

### 3.5 Boutique et salle d'exposition

Le module boutique et salle d'exposition (PRD § 6.10, BOU-01 à BOU-11), ajout du porteur de projet absent du DM et du CDC, fait partie du lot 1 et est actif dès le pilote (H14 tranchée). Le RA y exerce en propre les mêmes droits que le RC, sans intérim, sauf pour la clôture mensuelle du centre (SRC-02), qu'il ne valide qu'en intérim ; cette ligne couvre aussi les contributions financières reçues.

| Objet | ADM | DG | RC | RA | AA | RP | FO | RSE | SE | CPT | VB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Catalogue et prix | — | — | L C M A | L C M A | — | — | — | — | — | L | L |
| Entrées en stock et dépôts | — | — | L C | L C | — | — | — | — | — | L | L C, entrées et sorties courantes motivées |
| Ventes et reçus | — | — | L | L | — | — | — | — | — | L | L C |
| Annulation de vente | — | — | L | L | — | — | — | — | — | A, contre-écriture motivée | — |
| Caisse (ouverture et comptage) | — | — | L | L | — | — | — | — | — | L | C, ouverture et comptage |
| Clôture de caisse (validation) | — | — | L V, à défaut de CPT | L V, à défaut de CPT | — | — | — | — | — | L V, écarts motivés | — |
| Inventaire (comptage) | — | — | L C | L C | — | — | — | — | — | L | C |
| Inventaire (validation de l'ajustement) | — | — | L V | L V | — | — | — | — | — | L | — |
| Reversements (préparation) | — | — | L | L | — | — | — | — | — | L C | — |
| Reversements (validation et paiement) | — | — | L V, validation | L V, validation | — | — | — | — | — | M, paiement (date, pièce) | — |
| Volet boutique du tableau de bord | — | L (ag) (n), lot 2 | L E | L E | — | — | — | — | L (ag) | L E | — |
| Export journal des ventes, clôtures et reversements | — | — | E | E | — | — | — | — | — | E | — |
| Clôture mensuelle du centre (SRC-02) | — | L (ag) (n) | L V | L V (intérim) | — | — | — | — | L | L C, vérification | — |
| Salle d'exposition (articles exposés, transferts depuis et vers la réserve) | — | — | L | L | — | — | — | — | — | L | L C |

Un RC, un RA ou un AA peut détenir le rôle VB par cumul. Le module entier, ou la seule salle d'exposition, peut être désactivé pour un centre (règle 9). Les ventes ne contiennent aucune donnée sur l'acheteur ; les indicateurs boutique nationaux (DG, SE) restent agrégés, sans nom de productrice (BOU-12, P2). Chaque export est journalisé (BOU-10). Chaque montant (vente, encaissement, reversement, contribution reçue) n'a qu'une source : il est saisi une seule fois dans CAEF Connect, et la vue du CPT, le tableau de bord du RC et les rapports lisent les mêmes enregistrements (SRC-01).

### 3.6 Scolarité et paiements

Le module paiements (PRD § 6.12, PAY-01 à PAY-11) répond à la demande du porteur de projet du 13/10/2026, à formaliser par la Direction Générale ; ses écrans sont décrits dans la SFD (section 12). Les règlements Mobile Money des ventes de boutique suivent la ligne « Ventes et reçus » (3.5).

| Objet | ADM | DG | RC | RA | AA | RP | FO | RSE | SE | CPT | VB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Services et tarifs | L C M A (n), sur décision de la DG | L (n) | L | L | L | — | — | — | L (n) | L | — |
| Échéances et situation de paiement d'une bénéficiaire | — | L (ag) | L | L | L, avis d'échéance | — | — | — | L | L, identité minimale | — |
| Exonérations et prises en charge | — | L (ag) | L V | L V (intérim) | L C | — | — | — | L | L C | — |
| Encaissement (espèces, demande de paiement, déclaration Mobile Money) | — | — | L | L | L C | — | — | — | — | L C | — |
| Paiements à affecter | — | — | L | L | — | — | — | — | — | L M, affectation motivée | — |
| Rapprochement quotidien avec l'opérateur | — | — | L | L | — | — | — | — | — | L M, écarts motivés | — |
| Remboursements | — | — | L V | L V (intérim) | — | — | — | — | — | L C, demande motivée | — |
| Export des paiements | — | — | E | E | — | — | — | — | — | E | — |

Seule la confirmation de l'opérateur fait d'un paiement un encaissement : aucun rôle ne saisit ni ne modifie un statut « Confirmé » ou un montant confirmé (RG-PAY-03). Aucun rôle ne voit le code secret ni le solde de la payeuse, que CAEF Connect ne reçoit jamais.

## 4. Règles particulières

Neuf règles complètent la matrice là où un simple droit par rôle ne suffit pas ; elles sont contrôlées par le système, pas seulement par procédure.

1. **Séparation des tâches.** Le système refuse qu'un même utilisateur saisisse et valide : la réception d'une contribution (RG-CTR-04), la proposition qu'il a préparée, une dérogation de capacité ou d'achèvement qu'il a demandée, la fusion de deux dossiers qu'il a créés le jour même. En boutique, il refuse aussi : la validation de la clôture de caisse d'une journée par un utilisateur qui a saisi des ventes ce jour-là ; la validation de l'ajustement d'un inventaire par celui qui l'a compté ; le marquage « payé » d'un reversement par celui qui l'a préparé et validé (circuit : préparé par le CPT, validé par le RC ou le RA). Pour la clôture mensuelle du centre (SRC-02, RG-SRC-02), il refuse que celui qui l'a vérifiée la valide : le CPT vérifie, le RC (ou le RA en intérim) valide ; une fois validé, le mois est verrouillé et toute correction passe par une écriture de régularisation datée du mois courant (RG-SRC-03). Pour la scolarité, il refuse la validation d'une exonération par son auteur et celle d'un remboursement par son demandeur (RG-PAY-09, RG-PAY-10).
2. **Habilitation nominative nationale.** Un utilisateur DG ou RSE qui doit consulter des dossiers nominatifs (contrôle, audit, rapport partenaire exceptionnel) reçoit une habilitation datée, limitée à un objet et à une durée de 30 jours au plus, accordée par l'ADM sur demande écrite de la Direction ; chaque consultation est journalisée.
3. **Délégation temporaire.** En cas d'absence, un RC peut déléguer ses validations à un autre utilisateur de son centre pour une période bornée ; au MVP, la délégation est configurée par l'ADM à la demande du RC, l'interface de délégation en libre-service étant P2 (USR-08).
4. **Accès d'urgence technique.** Une intervention de l'équipe technique sur des données de production exige un ticket, l'accord de la Direction, un compte nominatif dédié et une revue du journal après intervention.
5. **Données d'enfants.** Aucun rôle n'a de droit sur des données d'enfants au MVP ; le module crèches arrivera après le MVP (écart A3, tranché le 12/10/2026) ; ses droits feront l'objet d'une section distincte validée avec avis juridique.
6. **Intérim du responsable de centre.** Le RA n'exerce les droits de validation du RC (cellules « V (intérim) ») que pendant un intérim déclaré par le RC ou l'ADM, avec dates de début et de fin, motif et trace (USR-09) ; hors de cette période, la validation lui est refusée. En boutique, il valide en propre clôtures de caisse (à défaut de CPT), inventaires et reversements, et ne valide jamais une opération qu'il a lui-même saisie.
7. **Accès minimal du comptable.** Le CPT n'accède à aucun dossier bénéficiaire ; pour les reversements boutique, il voit seulement le nom, le prénom, le code et le téléphone des productrices déposantes. Pour la scolarité, il voit l'identité minimale (nom, prénom, code) et l'onglet Paiements des bénéficiaires, jamais le reste du dossier. Le VB ne voit que le nom et le code de la déposante sur l'article. Le CPT ne tient ni comptabilité générale ni paie dans l'outil (exclusions A6) : il exporte vers la comptabilité tenue ailleurs.
8. **Hors ligne.** Le mode hors ligne n'existe que sur un appareil enrôlé et pour les rôles de terrain du centre (RC, RA, AA, RP, FO, VB, CPT) ; ADM, DG, RSE et SE travaillent en ligne seulement. L'appareil ne garde que le jeu de données du rôle et du périmètre, sans données restreintes ; chaque opération envoyée est revérifiée au serveur avec les droits en vigueur à sa réception, et une opération devenue hors droits est refusée et journalisée (OFF-04, OFF-06, RG-OFF-08).
9. **Modules désactivés.** Un module optionnel (boutique et salle d'exposition, salle d'exposition seule, scolarité et paiements, volet RSE du centre, puis les modules à venir) est activé ou désactivé pour un centre par l'ADM sur décision datée de la Direction Générale (PRD ADM-08). Pour un centre où un module est désactivé, toutes ses cellules valent « — » pour tous les rôles, sauf la consultation de l'historique, en lecture seule, par la DG, le RC, le RA, le CPT et le SE ; un rôle propre au module (VB) ne peut pas y être affecté et ses affectations existantes sont suspendues. Le refus est appliqué côté serveur, y compris pour l'API et la synchronisation, et journalisé.

## 5. Attribution, revue et tests des droits

Les droits sont attribués sur demande écrite, revus chaque trimestre et testés cellule par cellule avant la mise en service du pilote (DAT § 6.1, SEC-12).

| Processus | Règle | Responsable |
| --- | --- | --- |
| Création de compte | Demande du RC (ou de la Direction pour un rôle national) précisant rôle, centre et date de fin éventuelle ; création par l'ADM. Les comptes RA, CPT, VB et CMT suivent ce circuit (demande du RC ou du RA) ; un compte VB n'est créé que si le module boutique est activé pour le centre ; un compte CPT n'est activé qu'avec la double authentification, obligatoire | RC, RA ou DG, ADM |
| Changement de rôle | Même circuit ; l'ancien droit est retiré le jour du nouveau | ADM |
| Départ ou mutation | Le RC signale le départ ; désactivation le jour même, historique conservé | RC, ADM |
| Revue trimestrielle | Liste des comptes actifs par centre, envoyée à chaque RC qui confirme ou corrige sous 10 jours ; comptes non confirmés suspendus | ADM, RC |
| Revue des droits nationaux | Liste des affectations nationales et habilitations nominatives, confirmée par la Direction | DG |
| Contrôle du journal | Revue mensuelle des accès refusés, exports nominatifs et habilitations exceptionnelles | SE, avec le référent données |

**Tests.** Pour chaque cellule de la section 3, la campagne de sécurité vérifie le droit accordé (l'action réussit) et le droit refusé (l'action échoue par l'interface et par appel direct à l'API, y compris celle de synchronisation), sur deux centres de test : CAEF Cameroun (Dixinn) et Centre de test B, avec des données fictives. Une seule cellule non conforme bloque la mise en service (DAT § 12).

**Validation.** Cette matrice est validée par la Direction Générale et le référent données et protection ; toute modification suit la procédure de gestion des changements (Plan § 11).

### 5.1 Transcription dans le backend (14/10/2026)

Le backend du lot 1 lit les droits dans un seul fichier de données, `backend/caef/habilitations/matrice.yaml`, transcrit de la section 3 cellule par cellule (rôle, objet, action, périmètre, condition) ; aucun droit n'est écrit en dur dans le code, et une action absente du fichier est refusée. Le test automatisé `caef/habilitations/tests/test_matrice.py` vérifie que le fichier reproduit ce document, puis que chaque cellule est appliquée par le moteur de droits dans le centre de l'utilisateur et refusée dans un autre centre ; il vérifie aussi l'intérim du RA (règle 6), la validation de caisse à défaut de CPT et la suspension d'un rôle propre à un module désactivé (règle 9). Toute modification de ce document doit donc être reportée dans `matrice.yaml`, sans quoi l'intégration continue échoue.

Là où la SFD et la Matrice divergent, ou se taisent, le backend a retenu la lecture la plus restrictive. Ces lectures sont listées dans `backend/DECISIONS.md` et dans le test, et sont à confirmer à la validation de cette matrice :

| Point | Lecture retenue |
| --- | --- |
| Annulation d'une vente | Réservée au CPT (`vente_annulation`, A pour le CPT seul) |
| Annulation d'une candidature | Exige le droit A : RC, ou RA en intérim |
| Mise en liste d'attente | Relève du droit C sur l'inscription |
| « À défaut de CPT » (V~) | Aucun comptable actif affecté au centre ce jour-là |
| Comptage de l'inventaire par l'AA | Seulement si l'AA cumule le rôle VB |
| Ouverture d'un inventaire | RC ou RA seulement |
| Fiche projet | Rattachée au module optionnel `rse_centre` |
| Déclaration d'intérim | Objet `interim` tiré de RG-ADM-13, sans ligne propre dans les tableaux de la section 3 |
| Cheffe de classe | Désignée au titre du droit M sur la présence (FO ou RP) |
| File « À résoudre » | Scindée en deux objets : `conflit_synchronisation` (RC, RA) et `ecriture_tardive` (CPT) |
| Transfert | Le côté accueil (C) ou origine (V) est contrôlé par le service, la matrice ne portant qu'un droit par objet |
| Volet boutique du tableau de bord national pour la DG | Prévu au lot 2, non ouvert |
| Rôle CMT | Absent des tableaux de la section 3 ; ses droits viennent du texte (consultation des appareils, sans donnée nominative, en ligne seulement) |

Deux points restent hors du lot 1 : après un transfert, le centre d'origine n'a pas de lecture de l'historique du dossier ; et le cloisonnement par centre est contrôlé dans les services et la couche d'accès aux données, pas encore par des règles de sécurité au niveau des lignes (RLS) de PostgreSQL.

**Comptes de test.** La commande `generer_donnees_fictives` crée les deux centres de test (CAEF Cameroun, code CMR, et Centre de test B, code TSB, marqué fictif) et un compte par rôle : `adm.national`, `dg.direction`, `rse.national`, `se.national`, puis `rc.cmr`, `ra.cmr`, `aa.cmr`, `rp.cmr`, `fo.cmr`, `cpt.cmr`, `vb.cmr`, `cmt.cmr`, et `rc.tsb`, `aa.tsb` pour le second centre. Elle est refusée en production.
