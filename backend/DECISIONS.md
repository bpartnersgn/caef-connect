# Décisions et points ouverts du backend

Ce fichier liste les choix faits là où les spécifications (SFD 03, Matrice 04, modèle 05, DAT 06) se taisent ou se contredisent. Règle suivie : en cas de doute, la lecture la plus restrictive, et tout point ouvert devient un paramètre réglable sans code (`settings.CAEF`, variables d'environnement).

## Points ouverts devenus paramètres

| Point | Paramètre | Valeur par défaut |
| --- | --- | --- |
| H4, champs obligatoires du dossier | `CHAMPS_REQUIS_DOSSIER` | nom, prénoms, sexe, zone, consentement (date et mode), naissance |
| H5, seuil de seconde validation DG d'une proposition | `CAEF_SEUIL_SECONDE_VALIDATION_PROPOSITION` | vide : pas de seconde validation |
| H15, tarifs de scolarité | table `tarif_service`, saisie par l'ADM sur décision DG | aucun tarif : aucune échéance créée |
| H16, passerelle Mobile Money | `CAEF_PASSERELLE_MOBILE_MONEY` | `declaratif` (paiements déclarés par identifiant, confirmés au rapprochement) |
| H16, centre des paiements sans référence valide | `CAEF_CENTRE_PAIEMENTS_NON_REFERENCES` | vide : la transaction reste orpheline, rattachée quand le paiement est déclaré avec son identifiant |
| R1, fenêtre « bénéficiaire active » | `CAEF_JOURS_BENEFICIAIRE_ACTIVE` | 90 jours |
| Inactivité d'un dossier | `CAEF_JOURS_INACTIVITE_DOSSIER` | 365 jours |

## Lectures restrictives où SFD et Matrice divergent

- L'annulation d'une vente est réservée au CPT (Matrice : `vente_annulation` A pour le CPT seul).
- L'annulation d'une candidature exige le droit A (RC, ou RA en intérim).
- La mise en liste d'attente relève du droit C sur l'inscription.
- « À défaut de CPT » (V~) signifie : aucun comptable actif affecté au centre ce jour-là.
- L'AA ne compte l'inventaire que s'il cumule le rôle VB.
- La fiche projet relève du module `rse_centre`.
- L'objet `interim` (déclaration d'intérim) est tiré de RG-ADM-13, et n'a pas de ligne dans les tableaux de la Matrice.
- La cheffe de classe est désignée au titre du droit M sur la présence (FO ou RP).
- Un inventaire est ouvert par le RC ou le RA seulement.
- La file « À résoudre » est scindée en deux objets : `conflit_synchronisation` (RC, RA) et `ecriture_tardive` (CPT).
- Pour un transfert, le côté accueil (C) ou origine (V) est contrôlé par le service, la Matrice ne portant qu'un droit par objet.
- Le volet boutique du tableau de bord national pour la DG est prévu au lot 2 et n'est pas ouvert.

Le test `caef/habilitations/tests/test_matrice.py` compare `matrice.yaml` au document 04 et liste explicitement ces écarts.

## Choix de modèle et de mise en œuvre

- **Fusion de dossiers :** une table `fusion` garde l'état avant fusion, pour pouvoir l'annuler pendant 30 jours.
- **Doublons :** une date de naissance connue à l'année près ne compare que l'année, et seulement si les deux dossiers sont à cette précision. Le téléphone seul ne donne aucun point.
- **Reversements :** l'arrondi au franc se fait à la fin du calcul, au demi supérieur.
- **Numérotation des reçus :**
  - par série d'appareil, avec un numéro continu ;
  - en ligne sans appareil, la série est `<centre>-W` pour les ventes et `<centre>-P` pour les paiements ;
  - un numéro sauté est consigné comme vente annulée de total nul ;
  - les contre-écritures d'annulation prennent la série `ANN`.
- **Écriture tardive régularisée :** elle est rejouée au nom de l'auteur d'origine, dans la série web, et datée du mois courant avec le mois corrigé. Le numéro d'appareil non utilisé est consigné comme annulé.
- **Jeton d'appareil :** il n'ouvre que les routes de synchronisation. Toute autre route le refuse.
- **Notification de passerelle :** une signature invalide renvoie 401 et est journalisée. Un doublon renvoie 200 sans effet. Le montant retenu est celui de l'opérateur.
- **Import des relevés opérateur :** par fichier (CSV ou JSON). La tâche `importer_releves` attend le contrat de la passerelle (H16).

## Non couvert par ce lot

- Indicateurs non calculés : 11, 12, 25, 29, 32, 35 et 41 à 44 (lot 3, ou pas de source de données au MVP). Ils s'affichent « non renseigné ».
- Après un transfert, le centre d'origine n'a pas de lecture de l'historique.
- RLS PostgreSQL et contraintes d'exclusion de périodes en base : le contrôle se fait dans les services et la couche d'accès aux données.
- Gabarits HTMX et application PWA : hors du périmètre backend.
- Rôle CMT : absent des tableaux de la Matrice. Ses droits viennent du texte (consultation des appareils).
