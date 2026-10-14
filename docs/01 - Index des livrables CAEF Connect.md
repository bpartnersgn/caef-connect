# Index des livrables CAEF Connect

Oct 12, 2026 · @Bangoura · mis à jour le 14/10/2026

## 1. Documents de conception produits

Cette page rassemble le dossier de conception de CAEF Connect. Les huit documents sont rédigés, cohérents entre eux et à valider ; ils reprennent les mêmes identifiants d'exigences, de rôles, d'entités et d'indicateurs, si bien qu'une exigence du PRD se suit jusqu'à son cas de test. Mise à jour du 12/10/2026 : tous intègrent le module boutique et les rôles de responsable adjoint de centre, de comptable de centre et de vendeur ou vendeuse de boutique, demandés par le porteur de projet ; la place de la boutique dans les lots est tranchée (H14). Mise à jour suivante du 12/10/2026 : pilote dans un seul centre, le CAEF Cameroun à Dixinn (A1), RSE et boutique dans le lot 1 du pilote (A14, H14), crèche reportée (A3), source unique des chiffres entre comptable et responsable (SRC-01 à SRC-04), et ajout du document Budget et modèle économique ; ces décisions du porteur de projet sont à formaliser par la Direction Générale. Mise à jour du 13/10/2026 : le hors ligne d'abord avec synchronisation automatique (OFF-01 à OFF-08) et le paiement par Mobile Money de la scolarité et des services associés (PAY-01 à PAY-13, H15, H16), demandés par le porteur de projet comme exigences d'architecture, sont intégrés dans tous les documents, à commencer par le DAT ; ils restent à formaliser par la Direction Générale. Le même jour, les rôles de l'outil ont été calés sur l'organigramme des centres, avec l'ajout du chef matériels (CMT), et les modules optionnels, dont la boutique et la salle d'exposition, peuvent être désactivés par centre (ADM-08, BOU-15). Mise à jour du 14/10/2026 : le backend du lot 1 est écrit (Django, API REST `/api/v1`, données fictives, tests de la Matrice, Docker, intégration continue), et les documents sont alignés sur ce qui a réellement été implémenté. Chaque document signale les écarts et les choix de mise en œuvre dans une section datée du 14/10/2026 : paramètres des points ouverts (Brief § 5), lectures restrictives de la Matrice (Matrice § 5), tables techniques ajoutées (Modèle § 10), routes de l'API et déploiement (DAT § 4.2 et § 7), indicateurs calculés (Référentiel § 1) et tests automatisés (Plan de tests § 4).

| Document | Ce qu'il fixe | Statut | Lien |
| --- | --- | --- | --- |
| PRD | Vision, objectifs, exigences priorisées P0 à P3 et lots, hypothèses H1 à H16, écarts entre sources A1 à A16 (A1, A3, A14 et H14 tranchés), module boutique et salle d'exposition BOU-01 à BOU-15, modules activables par centre ADM-08, source unique SRC-01 à SRC-04, hors ligne OFF-01 à OFF-08, scolarité et paiements PAY-01 à PAY-13 | Rédigé, à valider | [PRD CAEF Connect](https://claude.ai/code/artifact/035a2318-82b8-4a50-8f38-7dc9d9afd6ac) |
| SFD du MVP | Écrans, règles de gestion, statuts, rapports, scénarios SC-01 à SC-09 et critères d'acceptation, module boutique et salle d'exposition, hors ligne et synchronisation, scolarité et paiements, organigramme et modules par centre | Rédigée, à valider | [SFD du MVP](https://claude.ai/code/artifact/cdf7bc38-c41b-4c5d-86b4-199c6cc0b1a8) |
| Matrice des rôles et permissions | Onze rôles internes calés sur l'organigramme des centres, dont le chef matériels, plus la gérante de la salle d'exposition et de la boutique, 67 objets en six domaines, dont la scolarité et les paiements, et les droits hors ligne, actions et périmètres | Rédigée, à valider | [Matrice des rôles et permissions](https://claude.ai/code/artifact/8003870c-82da-4846-8792-ff5691f82549) |
| Modèle et dictionnaire des données | 64 entités, dont douze pour la boutique et la salle d'exposition, deux pour la clôture mensuelle, quatre pour la synchronisation hors ligne et neuf pour la scolarité et les paiements, une pour les modules activés par centre, relations, champs, contrôles et sensibilité | Rédigé, à valider | [Modèle et dictionnaire des données](https://claude.ai/code/artifact/79209dfa-9f14-4b89-9f46-313fea0b2044) |
| DAT détaillé | Architecture cible, hors ligne d'abord et synchronisation, paiements Mobile Money, modules activables par centre, pile technique proposée, sécurité, sauvegarde, exploitation, décisions techniques à valider | Rédigé, à valider | [DAT détaillé](https://claude.ai/code/artifact/3498888f-f2dd-4793-8acc-f9ab385e2f15) |
| Référentiel des indicateurs | 39 fiches en cinq familles, dont six pour la boutique, les revenus des productrices et la clôture mensuelle, aux rubriques du DM § 10.4, règles communes de calcul, dont l'affichage « Module non activé », points R1 à R7 | Rédigé, à valider | [Référentiel des indicateurs](https://claude.ai/code/artifact/fbf60b80-9db4-465d-a3da-0c4deb4a4048) |
| Plan de tests et de recette | Cinq campagnes C1 à C5, scénarios SC-01 à SC-09 avec les cas hors ligne, paiements et modules par centre, jeux de données, critères d'entrée et de sortie, procès-verbal | Rédigé, à valider | [Plan de tests et de recette](https://claude.ai/code/artifact/7dd1d811-41ff-46ce-bb8d-51a2cac267c0) |
| Budget et modèle économique | Quatre composantes de coût, postes à chiffrer sur devis (dont le hors ligne et les paiements Mobile Money), scénarios S1 à S3, financement du pilote par TIKA et des coûts récurrents | Structure rédigée, montants à chiffrer sur devis | [Budget et modèle économique](https://claude.ai/code/artifact/db8b4384-b72d-48a7-8b4c-e738e6403657) |

Ordre de lecture conseillé : le PRD pour le pourquoi et le quoi, la SFD pour le comment fonctionnel, puis la Matrice et le Modèle qui la précisent, le DAT pour le comment technique, le Référentiel pour les chiffres, le Plan de tests pour la preuve, et le Budget pour le coût et le financement.

**Pour l'équipe de réalisation :** le [Brief de démarrage développeur](https://claude.ai/code/artifact/b71523e7-1a3a-4944-8f60-ab0ae4ff66fc) se lit en premier. Il donne les règles non négociables, l'ordre de construction du lot 1, son avancement et les positions d'attente à coder en attendant les décisions.

**Code.** Le dépôt `bpartnersgn/caef-connect` contient ces documents (dossier `docs/`) et le backend (dossier `backend/`, branche `backend-lot1`, demande de fusion n° 1). Trois fichiers y complètent le dossier de conception :

| Fichier | Ce qu'il fixe |
| --- | --- |
| `AGENTS.md` (et `CLAUDE.md`, qui y renvoie) | Les treize règles non négociables et la façon de travailler, pour les développeurs et les assistants de code IA |
| `backend/README.md` | Démarrage local, tests, organisation des applications |
| `backend/DECISIONS.md` | Points ouverts devenus paramètres, lectures restrictives là où la SFD et la Matrice divergent, choix de mise en œuvre, ce que le lot ne couvre pas |

## 2. Documents sources

Les huit documents ci-dessus s'appuient sur quatre sources fournies par l'équipe CAEF, complétées par les demandes du porteur de projet. Quand elles divergent, l'écart est noté dans le PRD (A1 à A16) avec une position d'attente, sans trancher à la place des instances.

| Source | Rôle dans le dossier | Abréviation |
| --- | --- | --- |
| Document Maître CAEF Connect | Référence de vision, de périmètre et de gouvernance ; fait foi en cas de doute | DM |
| Cahier des charges fonctionnel | Modules M01 à M14 et règles métier, comparés au DM | CDC |
| Dossier d'architecture technique v1.0 | Exigences non fonctionnelles et options techniques, détaillées dans le DAT détaillé | DAT v1.0 |
| Plan de déploiement, de gouvernance et de conduite du changement | Phasage, lots, pilote, reprise des données, formation, risques | Plan |
| Demandes du porteur de projet (12 et 13/10/2026) | Boutique des centres, responsable adjoint de centre et comptable de centre, hors ligne d'abord, paiements Mobile Money de la scolarité, organigramme des centres et modules désactivables par centre ; absents du DM et du CDC, signalés comme tels | PP |

## 3. Couverture des vingt livrables du DM § 21

Sur les vingt livrables attendus à l'issue du cadrage et de la conception, onze sont couverts par un document dédié (dont deux sources fournies), six le sont en partie dans des documents existants, et trois restent à produire, la plupart parce qu'ils dépendent du diagnostic terrain, d'une décision ou du développement.

| N° | Livrable | Où il se trouve | État |
| --- | --- | --- | --- |
| 1 | Document Maître validé | Source DM | Fourni, validation institutionnelle à obtenir |
| 2 | PRD complet | PRD | Rédigé |
| 3 | Cartographie des processus métier | Processus du DM § 9 et scénarios de la SFD | Partiel ; cartographie à établir au diagnostic |
| 4 | Spécifications fonctionnelles détaillées | SFD du MVP | Rédigées pour le MVP ; lot 3 à spécifier |
| 5 | Modèle de données | Modèle et dictionnaire des données | Rédigé |
| 6 | Dictionnaire des données | Modèle et dictionnaire des données | Rédigé |
| 7 | Matrice des rôles et permissions | Matrice | Rédigée |
| 8 | Maquettes fonctionnelles | Inventaire des écrans E-xxx dans la SFD | À produire à partir de la SFD |
| 9 | Dossier d'architecture technique | DAT v1.0 et DAT détaillé | Rédigé |
| 10 | Plan de sécurité et de protection des données | Exigences SEC et DAT du PRD, sécurité du DAT détaillé, Matrice, sensibilité des champs du Modèle | Partiel ; politique de confidentialité et de conservation à rédiger |
| 11 | Stratégie de migration | Plan § 7, exigence MIG-01, Plan de tests § 7.2 | Partiel ; inventaire des sources à faire au diagnostic |
| 12 | Plan de tests et de recette | Plan de tests et de recette | Rédigé |
| 13 | Plan de déploiement | Source Plan | Fourni |
| 14 | Plan de formation | Volet formation du Plan | Partiel ; supports par rôle à produire |
| 15 | Plan de maintenance | Éléments d'exploitation et de sauvegarde du DAT détaillé | Partiel ; niveaux de service et organisation du support à fixer |
| 16 | Budget et modèle économique | Budget et modèle économique | Structure et scénarios rédigés ; montants à chiffrer sur devis |
| 17 | Tableau des risques | Risques produit du PRD § 9.2, risques du Plan § 10 | Partiel ; tableau unique à consolider |
| 18 | Référentiel des indicateurs | Référentiel des indicateurs | Rédigé |
| 19 | Documentation utilisateur | Aucun ; documentation technique du backend dans le dépôt (README, DECISIONS.md, schéma OpenAPI) | À produire avec les écrans |
| 20 | Procès-verbal de validation institutionnelle | Aucun | À établir en fin de conception |

## 4. Ce qu'il reste à décider et ordre de validation

Le dossier est construit pour avancer sans attendre les arbitrages : chaque point ouvert a une position d'attente. Le développement du backend a commencé sur ces positions, chacune réglable sans code (Brief § 5). Elles doivent toutefois être confirmées ou corrigées avant la recette, dans cet ordre.

1. **Décisions du DM § 22**, présentées dans le PRD comme hypothèses H1 à H16 (autorité institutionnelle, périmètre du MVP, hébergement, circuit de validation RSE, comptabilité, indicateurs, place du module boutique, politique tarifaire de la scolarité, passerelle Mobile Money et compte marchand) ; A1, A3, A14 et H14 ont été tranchés par le porteur de projet le 12/10/2026, le hors ligne (H11) et le Mobile Money (H9, A6) demandés le 13/10/2026 ; tous restent à formaliser, tout comme l'offre de TIKA pour financer le pilote. Instance : comité de pilotage et Direction Générale.
2. **Écarts entre sources A1 à A16**, listés dans le PRD, dont la place du module RSE dans le lot 1 ou le lot 2 (A14).
3. **Validation du PRD**, puis de la SFD, de la Matrice et du Modèle, qui en découlent.
4. **Décisions techniques** du DAT détaillé (§ 10), dont la pile technique (Django retenu pour le backend, à confirmer), l'hébergement, les objectifs de reprise, la durée maximale de travail hors ligne et la passerelle Mobile Money (option 2 proposée : 15 minutes de perte au plus, 8 heures ouvrées de reprise).
5. **Points R1 à R7** du Référentiel des indicateurs et validation des fiches du lot 1.
6. **Points à arbitrer du Plan de tests** (responsable de la recette, utilisateurs clés, test d'intrusion).

Une fois ces validations obtenues, le procès-verbal de validation institutionnelle (livrable 20) peut être établi et la phase de réalisation ouverte.
