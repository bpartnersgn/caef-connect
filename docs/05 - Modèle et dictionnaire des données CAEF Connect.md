# Modèle et dictionnaire des données CAEF Connect

Oct 12, 2026 · @Bangoura

## 1. Objet et conventions

Ce document fixe les 64 entités du MVP (dont les 12 du module boutique, dans le lot 1 (H14 tranchée), les 2 de la clôture mensuelle, SRC-02, et les 13 ajoutées le 13/10/2026 : 4 pour la synchronisation hors ligne, OFF-01 à OFF-08, et 9 pour la scolarité et les paiements, PAY-01 à PAY-11, puis l'entité module\_centre pour les modules activés par centre, ADM-08), leurs relations et la définition de chaque champ ; il sert de base à la base de données relationnelle prévue par le DAT et aux contrôles de saisie décrits dans la SFD.

**Nommage.** Tables et champs en français, minuscules, sans accent, séparés par des tirets bas (`session_formation`, `date_debut`). Clé primaire `id`, clé étrangère `<entite>_id`.

**Types utilisés.**

| Type | Définition |
| --- | --- |
| UUID | Identifiant interne immuable, généré par le serveur ou, pour un objet créé hors ligne, par l'appareil (UUID v7, ordonné dans le temps), jamais affiché comme référence métier |
| Code | Texte lisible généré (ex. BEN-CMR-2026-00042), unique, immuable |
| Texte(n) | Chaîne de n caractères au plus |
| Liste(R) | Valeur d'un référentiel R administré dans l'outil |
| Énum | Liste fermée définie par la conception (statuts) |
| Date, DateHeure | ISO 8601 ; DateHeure en UTC, affichée à l'heure de Conakry |
| Montant | Décimal (18,2) accompagné d'un champ devise ISO 4217, GNF par défaut (devise de travail) ; USD ou EUR possibles pour les contributions de partenaires internationaux |
| Booléen | Vrai ou faux, jamais nul |
| Fichier | Référence vers un objet du stockage documentaire (entité Document) |

**Colonnes communes à toutes les entités métier** (non répétées dans les tables) : `id` (UUID), `cree_le`, `cree_par`, `modifie_le`, `modifie_par`, `archive` (booléen), `archive_le`, `version` (entier, verrou optimiste contre les saisies concurrentes), `cle_idempotence` (texte, unicité des envois après coupure réseau, NET-02), `origine_saisie` (énum : en\_ligne, hors\_ligne, import), `appareil_id` (FK appareil, renseigné pour une saisie hors ligne) et `horodatage_appareil` (DateHeure de la saisie sur l'appareil) (OFF-03, OFF-05).

**Valeur « non renseigné ».** Un champ facultatif vide est nul en base ; un champ requis inconnu (cas d'import) prend la valeur spéciale du référentiel « Non renseigné » ou « À vérifier » et porte l'indicateur `qualite = a_verifier`. Les statistiques comptent ces cas séparément de zéro (TDB-09, MIG-01). Reprise des registres papier (livrets, feuilles volantes) : une divergence non résolue entre les chiffres de la comptable et ceux de la responsable est importée avec le statut « à vérifier » (qualite = a\_verifier), jamais arbitrée par supposition (SRC-03).

**Colonne Sens.** Niveau de sensibilité du champ : **P** public ou institutionnel ; **I** interne ; **N** nominatif (donnée personnelle) ; **R** restreint (donnée personnelle à accès limité, voir section 7).

## 2. Modèle conceptuel

L'inscription relie la bénéficiaire à la session, et la convention porte à la fois les engagements et les contributions ; ce sont les deux pivots des indicateurs de formation et de RSE.

&#91;embedded content: modèle conceptuel · 18 entités principales sur 50\]

Non dessinés pour la lisibilité : le centre de rattachement de la bénéficiaire, le formateur des sessions et séances, l'attestation issue de l'inscription, la fiche projet liée à l'opportunité, le programme financeur d'une session, et les entités transverses document, notification, validation et historique\_etape, rattachées à tout objet métier. Le schéma ne couvre pas non plus interim\_responsable ni les 12 entités du module boutique et les 2 entités de la clôture mensuelle, dont les relations sont données en section 6, ni les 13 entités de la synchronisation et des paiements (sections 8 et 9).

| Relation | Cardinalité | Règle |
| --- | --- | --- |
| centre, session | 1 à n | Une session appartient à un seul centre |
| formation, session | 1 à n |  |
| session, inscription ; bénéficiaire, inscription | 1 à n chacune | Une bénéficiaire au plus une fois par session |
| bénéficiaire, candidature | 1 à n | Une candidature donne au plus une inscription active |
| séance, présence ; inscription, présence | 1 à n chacune | Une présence par séance et inscription |
| partenaire, opportunité | 1 à n |  |
| opportunité, proposition | 1 à n | Plusieurs versions ou propositions successives |
| proposition, convention | 1 à 0 ou 1 | Une convention peut aussi naître sans proposition (reprise de l'existant) |
| convention, engagement ; convention, contribution | 1 à n chacune |  |
| programme, contribution | 1 à n | Une contribution, un programme au MVP |
| utilisateur, affectation ; centre, affectation | 1 à n chacune | Le rôle est porté par l'affectation |
| centre, module\_centre | 1 à n | Une ligne par changement de statut d'un module optionnel ; le statut en vigueur est la ligne de date d'effet la plus récente (ADM-08) |

## 3. Administration et sécurité

Douze entités portent l'organisation du réseau, les comptes, les droits et la traçabilité.

### centre

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code | Texte(3) | O | P | Unique, immuable après première donnée (RG-ADM-01) |
| nom | Texte(150) | O | P | Unique |
| zone\_territoriale\_id | FK zone\_territoriale | O | P | Niveau commune ou quartier |
| adresse, telephone, courriel | Texte | F | P | Téléphone au format +224 |
| responsable\_id | FK utilisateur | O | I | Rôle RC actif |
| date\_ouverture | Date | F | P |  |
| capacite\_indicative | Entier | F | I | Supérieur à 0 |
| statut | Énum (actif, inactif) | O | I | RG-ADM-02 |

### zone\_territoriale

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| niveau | Énum (région, préfecture, commune, quartier) | O | P |  |
| nom, code | Texte | O | P | Code officiel si disponible |
| parent\_id | FK zone\_territoriale | C | P | Obligatoire sauf pour une région |

### utilisateur

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| identifiant\_connexion | Texte(120) | O | I | Unique, jamais réattribué |
| nom, prenom | Texte(100) | O | N |  |
| telephone\_pro | Texte(20) | F | N |  |
| empreinte\_mot\_de\_passe | Texte | O | R | Hachage fort avec sel (algorithme fixé au DAT) ; jamais lisible |
| double\_auth\_active, secret\_double\_auth | Booléen, Texte chiffré | C | R | Obligatoire pour ADM, DG et CPT ; recommandée pour RA |
| statut | Énum (actif, suspendu, désactivé) | O | I |  |
| derniere\_connexion, echecs\_consecutifs, bloque\_jusqua | DateHeure, Entier, DateHeure | S | I | RG-ADM-08, RG-ADM-09 |

### role et permission

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| role.code, role.libelle | Texte | O | I | ADM, DG, RC, RA, AA, CPT, RP, FO, RSE, SE, VB, CMT (VB actif avec le module boutique ; RA, CPT et VB ajoutés à la demande du porteur de projet ; CMT, chef matériels, ajouté le 13/10/2026 avec l'organigramme, en consultation ; les écrans affichent les titres de l'organigramme, Matrice § 2.1) |
| role.actif | Booléen | O | I | Rôles futurs désactivés |
| permission.role\_id, objet, action, perimetre | FK, Texte, Énum (L, C, M, V, E, A), Énum (s, c, n, ag, p) | O | I | Une ligne par cellule de la Matrice des rôles |

### affectation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| utilisateur\_id, role\_id | FK | O | I |  |
| centre\_id | FK centre | C | I | Nul seulement si `national` est vrai |
| national | Booléen | O | I | Sur décision tracée (RG-ADM-06) |
| date\_debut, date\_fin | Date | O, F | I |  |
| motif | Texte | O | I | Journalisé |

### habilitation\_exceptionnelle

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| utilisateur\_id, objet\_type, objet\_id | FK, Texte, UUID | O | I | Objet précis visé |
| date\_debut, date\_fin | Date | O | I | 30 jours au plus |
| demande\_par, accorde\_par, motif | FK, FK, Texte | O | I | Matrice § 4 règle 2 |

### interim\_responsable

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I |  |
| responsable\_remplace\_id, adjoint\_id | FK utilisateur | O | I | Rôle RC actif ; rôle RA actif sur le même centre (USR-09) |
| date\_debut, date\_fin | Date | O | I | Fin après début ; hors de la période, les validations réservées au RC sont refusées au RA |
| motif | Texte | O | I | Journalisé |
| declare\_par | FK utilisateur | S | I | RC remplacé ou ADM |

### referentiel\_valeur

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| referentiel | Texte | O | P | Ex. motif\_rejet, categorie\_formation, nature\_contribution, motif\_abandon, niveau\_etudes |
| code, libelle, ordre | Texte, Texte, Entier | O | P | Code unique par référentiel |
| actif, date\_effet | Booléen, Date | O | P | Désactivation au lieu de suppression (RG-ADM-03) |

### periode

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| type | Énum (mois, trimestre, année, campagne) | O | P |  |
| libelle, date\_debut, date\_fin | Texte, Date, Date | O | P | Pas de chevauchement pour un même type |
| statut | Énum (ouverte, clôturée, rouverte) | O | I | RG-ADM-04 |

### journal\_audit

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| horodatage | DateHeure | S | I |  |
| utilisateur\_id, adresse\_ip, centre\_id | FK, Texte, FK | S | N |  |
| action | Énum (creation, modification, statut, validation, export, connexion, echec\_connexion, acces\_refuse, consultation\_sensible, fusion, droits) | S | I |  |
| objet\_type, objet\_id | Texte, UUID | S | I |  |
| avant, apres | JSON | S | N | Valeurs modifiées uniquement |
| motif, nb\_lignes | Texte, Entier | C | I | Obligatoires pour un export (RG-EXP-02) |

Le journal est en ajout seul : aucune mise à jour ni suppression n'est possible, y compris par l'administrateur (SEC-04).

### module\_centre

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I |  |
| module | Énum (boutique, salle\_exposition, scolarite\_paiements, rse\_centre, puis les modules à venir) | O | I | Modules optionnels seulement ; le socle n'a pas de ligne et reste toujours actif (RG-ADM-17) |
| statut | Énum (actif, inactif) | O | I | Unique (centre, module, date\_effet) ; salle\_exposition actif seulement si boutique est actif |
| date\_effet | Date | O | I | Au plus tôt le jour de la validation |
| decision\_reference, decision\_date | Texte(50), Date | O | I | Décision de la Direction Générale (RG-ADM-18) |
| motif | Texte | O | I |  |
| saisi\_par, valide\_par, valide\_le | FK utilisateur, FK utilisateur, DateHeure | S | I | Saisie par l'ADM, validation par la DG ; deux personnes distinctes |

La table est en ajout seul : chaque activation ou désactivation crée une ligne. Le serveur refuse une ligne « inactif » tant que le module a des opérations en cours (RG-ADM-19). Au pilote, une ligne « actif » par module optionnel est créée pour le CAEF Cameroun. Le filtre des habilitations lit le statut en vigueur à chaque requête et à chaque opération de synchronisation (DAT détaillé, sections 4.1 et 4.7).

## 4. Bénéficiaires et formation

Onze entités suivent la bénéficiaire de la candidature à l'attestation ; aucune donnée sensible n'est collectée par défaut (BEN-01).

### beneficiaire

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code | Code | S | I | BEN-\<centre>-\<année>-\<n°>, immuable après transfert |
| nom, prenoms, autres\_noms | Texte(100) | O, O, F | N |  |
| nom\_normalise, cle\_phonetique | Texte | S | N | Pour la détection des doublons (RG-BEN-02) |
| date\_naissance, annee\_naissance, precision\_naissance | Date, Entier, Énum (exacte, année, tranche) | C | N | Au moins l'année ou la tranche |
| sexe | Énum (F, M) | O | N | F par défaut |
| telephone | Texte(20) | F | N | Jamais identifiant ; non unique (DAT-01) |
| zone\_residence\_id | FK zone\_territoriale | O | N |  |
| niveau\_etudes, situation\_entree | Liste | F | N | Situation de référence pour l'insertion future |
| contact\_urgence\_nom, contact\_urgence\_tel | Texte | C | R | Si le programme le justifie |
| piece\_identite\_type, piece\_identite\_numero | Liste, Texte chiffré | C | R | Si le programme l'exige |
| centre\_rattachement\_id | FK centre | S | I | Change par transfert seulement |
| consentement\_date, consentement\_mode | Date, Énum (écrit, oral\_temoin) | O | N | PO-07 |
| autorisation\_image | Booléen | O | N | Faux par défaut |
| statut | Énum (actif, inactif, clôturé, archivé, fusionné) | S | I | SFD 4.4 |
| fusionne\_dans\_id | FK beneficiaire | C | I | Si statut fusionné |
| completude | Entier (%) | S | I |  |
| source\_import, ligne\_source | Texte | C | I | Traçabilité de migration (RG-BEN-09) |

### candidature

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code | Code | S | I |  |
| beneficiaire\_id, centre\_id | FK | O | I |  |
| formation\_id | FK formation | O | I | Formation souhaitée |
| date\_reception | Date | O | I |  |
| statut | Énum (brouillon, soumise, incomplète, validée, rejetée, en\_attente, inscrite, annulée) | S | I | SFD 4.3 |
| motif\_id, commentaire | Liste, Texte | C | I | Obligatoire pour incomplète, rejetée, annulée |
| doublon\_decision | Énum (aucun, dossier\_existant\_utilise, personne\_differente) | S | I | Avec commentaire si personne différente |
| valide\_par, valide\_le | FK, DateHeure | S | I |  |

### transfert

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| beneficiaire\_id, centre\_origine\_id, centre\_accueil\_id | FK | O | I | Centres distincts |
| motif | Texte | O | I |  |
| statut | Énum (demandé, accepté, refusé) | S | I | RG-BEN-06 |
| demande\_par, decide\_par, decide\_le | FK, FK, DateHeure | S | I |  |

### formation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code, intitule | Code, Texte(200) | S, O | P | Intitulé unique par catégorie |
| portee | Énum (nationale, centre) | O | P |  |
| centre\_id | FK | C | P | Si portée centre |
| categorie\_id | Liste | O | P |  |
| objectifs, prerequis, contenu | Texte long | O, F, F | P |  |
| duree\_heures | Décimal | O | P | Supérieur à 0 |
| seuil\_presence\_pct | Entier | O | P | Défaut 80 (PO-03) |
| evaluation\_requise, attestation\_prevue | Booléen | O | P |  |
| absence\_justifiee\_exclue | Booléen | O | P | RG-FOR-08 |
| statut | Énum (active, inactive) | O | P |  |

### session\_formation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code | Code | S | I |  |
| formation\_id, centre\_id, periode\_id | FK | O | I | RG-FOR-01 |
| date\_debut, date\_fin | Date | O | I | Fin après début |
| lieu | Texte | O | I |  |
| capacite | Entier | O | I | Supérieur à 0 |
| formateur\_principal\_id | FK formateur | O | I |  |
| programme\_id | FK programme | F | I | Financeur éventuel |
| statut | Énum (brouillon, ouverte, en\_cours, clôturée, annulée) | S | I | SFD 5.3 |
| rapport\_cloture | Texte long | C | I | À la clôture |

### seance

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| session\_id, date, heure\_debut, heure\_fin | FK, Date, Heure, Heure | O | I | Dans les dates de la session |
| formateur\_id | FK formateur | O | I | Pas de chevauchement (RG-FOR-02) |
| theme | Texte | F | I |  |
| presences\_validees | Booléen | S | I |  |

### formateur

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| utilisateur\_id | FK | F | I | Si le formateur a un compte |
| nom, prenom, telephone\_pro | Texte | O, O, F | N |  |
| statut\_intervenant | Énum (interne, externe, bénévole) | O | I |  |
| competences, domaines | Liste multiple | F | I | FOR-16 |
| centres | FK multiple centre | O | I |  |

### inscription

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| beneficiaire\_id, session\_id, candidature\_id | FK | O | I | Unique (beneficiaire, session) |
| date\_inscription | Date | S | I |  |
| statut\_participation | Énum (inscrite, commencée, suspendue, abandonnée, achevée, non\_achevée) | S | I | SFD 5.4 |
| motif\_sortie\_id | Liste | C | I | Si abandonnée ou suspendue |
| taux\_presence | Décimal | S | I | RG-FOR-08 |
| derogation\_motif, derogation\_par | Texte, FK | C | I | RG-FOR-03, RG-FOR-09 |
| cheffe\_de\_classe | Booléen | F | I | Au plus une inscription « vraie » par session ; désignée par le formateur ou le responsable pédagogique ; la cheffe de classe est une élève sans compte utilisateur (Matrice § 2.1) |

### presence

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| seance\_id, inscription\_id | FK | O | I | Unique (seance, inscription) |
| etat | Énum (présente, absente, retard, absence\_justifiée) | O | I |  |
| justificatif\_id | FK document | F | N |  |
| saisi\_par, saisi\_le, saisie\_tardive\_motif | FK, DateHeure, Texte | S, S, C | I | RG-FOR-06 |

### evaluation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| inscription\_id, intitule, date | FK, Texte, Date | O | I |  |
| type\_resultat | Énum (note, appréciation, acquis) | O | I |  |
| note, note\_max, appreciation | Décimal, Décimal, Liste | C | N | Selon le type |

### attestation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| inscription\_id | FK | O | I | Unique ; participation achevée (FOR-09) |
| numero | Code | S | I | ATT-\<centre>-\<année>-\<n°> |
| date\_delivrance, delivre\_par | Date, FK | O | I |  |
| statut | Énum (délivrée, annulée) | S | I | Annulation motivée |
| document\_id | FK document | F | N | PDF généré en P2 (FOR-11) |

## 5. Partenaires, RSE, programmes et objets transverses

Douze entités portent la chaîne partenaire, opportunité, proposition, convention, engagement et contribution ; deux entités transverses gèrent documents et notifications.

### partenaire

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code, raison\_sociale, sigle | Code, Texte(200), Texte(30) | S, O, F | P | Contrôle de doublon sur nom normalisé et sigle |
| categorie, secteur | Liste | O | P |  |
| adresse, telephone, courriel, site\_web | Texte | F | P | Coordonnées institutionnelles |
| responsable\_suivi\_id | FK utilisateur | O | I |  |
| statut | Énum (prospect, actif, inactif) | S | I | Actif si une convention est en cours |

### interlocuteur

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| partenaire\_id, nom, fonction | FK, Texte, Texte | O | N |  |
| telephone\_pro, courriel\_pro | Texte | F | N | Professionnels uniquement (PAR-02) |
| principal | Booléen | O | I | Un seul principal par partenaire |

### interaction

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| partenaire\_id, opportunite\_id | FK | O, F | I |  |
| type, date | Énum (appel, courriel, rendez\_vous, visite, événement), Date | O | I |  |
| participants\_internes, interlocuteurs | FK multiples | F | I |  |
| compte\_rendu, prochaine\_action, date\_prochaine\_action | Texte, Texte, Date | F | I |  |

### opportunite

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code, intitule | Code, Texte | S, O | I |  |
| partenaire\_id | FK | O | I |  |
| origine, apporteur | Liste, Texte | O, C | I | Traçabilité commerciale (DM § 7.9) |
| centres | FK multiple centre | O | I | Périmètre de visibilité RC |
| fiche\_projet\_id | FK | F | I |  |
| montant\_estime | Montant | F | I |  |
| potentiel | Énum (faible, moyen, fort) | F | I |  |
| etape | Entier 1 à 15 | S | I | Pipeline (SFD 6.3) |
| statut | Énum (ouverte, gagnée, perdue, suspendue) | S | I | Motif si perdue ou suspendue |
| prochaine\_action, date\_prochaine\_action | Texte, Date | C | I | Obligatoires si ouverte |
| contributeurs | Liste (utilisateur, rôle) | F | I | Sans calcul de commission |

### historique\_etape

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| opportunite\_id, etape\_avant, etape\_apres | FK, Entier, Entier | S | I |  |
| date, auteur\_id, commentaire | DateHeure, FK, Texte | S, S, C | I | Commentaire obligatoire si saut ou retour |

### fiche\_projet

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id, intitule, besoin | FK, Texte, Texte long | O | I |  |
| beneficiaires\_vises, objectif\_impact, indicateurs | Texte, Texte, Texte | O | I |  |
| budget\_indicatif | Montant | F | I |  |
| statut | Énum (brouillon, qualifiée, rattachée, abandonnée) | S | I |  |

### programme

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code, intitule, description | Code, Texte, Texte long | S, O, F | P | Fiche minimale (CNV-06) |
| centres | FK multiple centre | O | P |  |
| responsable\_id | FK utilisateur | O | I |  |
| date\_debut, date\_fin | Date | O | P |  |
| statut | Énum (prévu, en\_cours, clôturé) | O | P |  |

### proposition

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code, version | Code, Entier | S | I | Nouvelle version après soumission (RG-CNV-01) |
| opportunite\_id, partenaire\_id, programme\_id | FK | O, O, F | I |  |
| centres\_beneficiaires | FK multiple | O | I |  |
| montant\_sollicite, nature | Montant, Liste multiple | O | I |  |
| budget\_previsionnel | Texte long ou fichier | F | I |  |
| resultats\_attendus, calendrier | Texte long | O | I | Sans promesse non maîtrisée (DM § 7.3) |
| statut | Énum (brouillon, en\_validation, validée, rejetée, soumise, acceptée, refusée, suspendue) | S | I |  |
| date\_envoi, date\_reponse | Date | C | I |  |
| motif\_id, commentaire | Liste, Texte | C | I | Refus, rejet, suspension |

### validation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| objet\_type, objet\_id | Texte, UUID | O | I | Proposition, contribution, fusion, transfert, dérogation |
| etape, valideur\_attendu\_role | Entier, FK role | O | I | Circuit paramétrable (H5) |
| decision, decide\_par, decide\_le, commentaire | Énum (favorable, défavorable, validé, rejeté), FK, DateHeure, Texte | S | I | Décideur différent du saisissant |

### convention

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| reference | Texte | O | I | Unique |
| partenaire\_id, proposition\_id, programme\_id | FK | O, F, F | I |  |
| montant\_accorde | Montant | F | I | Distinct du montant sollicité |
| date\_signature, date\_debut, date\_fin | Date | C | I | Signature obligatoire au statut signée |
| signataires | Texte | C | I |  |
| document\_signe\_id | FK document | C | I | Obligatoire au statut signée (RG-CNV-05) |
| statut | Énum (en\_préparation, signée, en\_exécution, clôturée, résiliée) | S | I |  |

### engagement

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| convention\_id, partie | FK, Énum (partenaire, caef) | O | I |  |
| description, responsable\_id, centre\_id | Texte, FK, FK | O, O, F | I |  |
| echeance | Date | O | I |  |
| etat | Énum (à\_réaliser, en\_cours, en\_retard, réalisé, validé, abandonné) | S | I | en\_retard calculé (RG-CNV-07) |
| justificatif\_id, valide\_par | FK document, FK | C | I |  |

### contribution

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| code | Code | S | I |  |
| convention\_id, partenaire\_id | FK | O | I |  |
| programme\_id, centre\_beneficiaire\_id | FK | F, O | I | Une contribution = un programme au MVP (CTR-08 en P2) |
| nature | Liste (8 natures) | O | I | RG-CTR-01 |
| financiere | Booléen | S | I | Déduit de la nature ; sépare les totaux |
| montant\_promis, date\_prevue | Montant, Date | C | I |  |
| montant\_recu, date\_reception | Montant, Date | C | I | Obligatoires au statut reçue |
| devise\_origine, montant\_origine, taux\_conversion, source\_taux | Texte, Montant, Décimal, Texte | C | I | USD ou EUR (ISO 4217) pour les partenaires internationaux ; RG-CTR-06 |
| description\_bien, quantite | Texte, Décimal | C | I | Contributions non financières |
| valeur\_estimee, methode\_valorisation | Montant, Liste | F, C | I | Méthode obligatoire si valeur saisie |
| justificatifs | FK multiples document | C | I | Au moins un au statut reçue |
| reference\_comptable | Texte | F | I | Renvoi vers la comptabilité (H6) |
| reference\_piece\_comptable, date\_encaissement\_constatee, rapproche\_par | Texte, Date, FK utilisateur | F | I | Rapprochement d'une contribution financière reçue par le comptable du centre, rôle CPT (CTR-09) ; sans droit de validation, qui reste à la DG |
| statut | Énum (promise, reçue, validée, annulée) | S | I |  |
| saisi\_reception\_par, valide\_par | FK | S | I | Doivent différer (RG-CTR-04) |

### document

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| objet\_type, objet\_id | Texte, UUID | O | I | Rattachement métier (DOC-01) |
| type\_document | Liste | O | I |  |
| nom\_fichier, format, taille\_octets, empreinte | Texte, Texte, Entier, Texte | S | I | Formats autorisés : PDF, JPG, PNG, DOCX, XLSX ; 10 Mo au plus |
| chemin\_stockage | Texte | S | R | Jamais exposé ; téléchargement par lien signé de courte durée |
| confidentialite | Énum (interne, nominatif, restreint) | O | I |  |
| version | Entier | S | I |  |

### notification

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| destinataire\_id, type\_evenement | FK, Texte | S | I | SFD 8.4 |
| objet\_type, objet\_id, message | Texte, UUID, Texte | S | I | Sans donnée sensible dans le texte |
| canal | Énum (application, courriel, sms) | S | I | Application seule au MVP |
| lue\_le | DateHeure | S | I |  |

## 6. Boutique

Douze entités enregistrent ce que le centre vend dans sa boutique, le stock, la caisse et la part reversée aux productrices en dépôt-vente (BOU-01 à BOU-11), y compris la salle d'exposition, gérée comme un emplacement de stock (BOU-15). Ce module est une demande du porteur de projet, absente du DM et du CDC ; il est livré pour le pilote dans le lot 1 (H14 tranchée par le porteur de projet le 12/10/2026, à formaliser par la Direction Générale des CAEF). Deux entités de clôture mensuelle complètent la section (SRC-02). Le module, et la seule salle d'exposition, peuvent être désactivés pour un centre (module\_centre, ADM-08).

**Règles propres au module.** Montants en GNF entiers : type Montant, devise GNF imposée, partie décimale nulle contrôlée en base. Aucune suppression physique : une vente ou un mouvement s'annule par contre-écriture motivée et tracée (BOU-06). Le stock n'est jamais un champ modifiable : il est la somme des mouvements, exposée par une vue recalculable (BOU-04). Les ventes ne portent aucune donnée sur l'acheteur.

| Relation | Cardinalité | Règle |
| --- | --- | --- |
| centre, point\_de\_vente | 1 à n | Un seul point de vente actif par centre au MVP (plusieurs en P2, BOU-13) |
| point\_de\_vente, produit ; produit, prix\_produit | 1 à n chacune | Un seul prix en vigueur à une date donnée |
| produit, mouvement\_stock | 1 à n | Stock = somme des quantités signées, par emplacement |
| point\_de\_vente, vente ; vente, ligne\_vente ; vente, reglement | 1 à n chacune | Somme des règlements égale au total de la vente |
| point\_de\_vente, session\_caisse | 1 à n | Une session par point de vente et par jour |
| point\_de\_vente, inventaire ; inventaire, ligne\_inventaire | 1 à n chacune | Une ligne par produit inventorié |
| beneficiaire, produit ; beneficiaire, depot ; beneficiaire, reversement | 1 à n chacune | La déposante est une bénéficiaire existante ou un groupement |

### point\_de\_vente

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I | Un seul point de vente actif par centre au MVP |
| nom | Texte(150) | O | P |  |
| actif | Booléen | O | I | Désactivation au lieu de suppression |

### produit

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| point\_de\_vente\_id | FK point\_de\_vente | O | I |  |
| nom | Texte(150) | O | P | Unique par point de vente |
| categorie\_id, unite | Liste, Liste | O | I | Référentiels categorie\_produit et unite\_vente (pièce, kg, litre, lot) |
| origine | Énum (atelier\_centre, session\_formation, dépôt\_vente, groupement, achat\_revente) | O | I | BOU-01 |
| beneficiaire\_deposante\_id | FK beneficiaire | C | N | Obligatoire si origine dépôt\_vente d'une productrice ; lien nominatif |
| groupement | Texte(150) | C | I | Si le produit vient d'un groupement ; pas d'entité groupement au MVP |
| session\_origine\_id, formation\_origine\_id | FK session\_formation, FK formation | F | I | Atelier ou session d'origine |
| seuil\_alerte | Décimal | F | I | Alerte sous le seuil et sur stock négatif (BOU-04) |
| actif | Booléen | O | I | Pas de champ stock : le stock est calculé |

### prix\_produit

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| produit\_id | FK produit | O | I |  |
| prix | Montant | O | I | GNF entier, supérieur à 0 |
| date\_debut, date\_fin | Date | O, F | I | Pas de chevauchement pour un même produit ; fin nulle = prix en vigueur (BOU-11) |
| auteur\_id | FK utilisateur | S | I | Toute modification crée une ligne ; sans effet sur les ventes passées |

### depot

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| beneficiaire\_id, groupement | FK beneficiaire, Texte(150) | C | N, I | Productrice déposante ou groupement : exactement un des deux |
| produit\_id | FK produit | O | I |  |
| quantite\_deposee | Décimal(12,3) | O | I | Supérieure à 0 ; génère un mouvement entrée\_dépôt |
| part\_centre\_pct | Décimal(5,2) | O | I | Entre 0 et 100 ; part convenue pour le centre (BOU-02) |
| date\_depot | Date | O | I |  |
| statut | Énum (en\_cours, soldé, retiré) | S | I | Valeurs à confirmer au diagnostic |

### mouvement\_stock

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| produit\_id | FK produit | O | I |  |
| type | Énum (entrée\_production, entrée\_dépôt, entrée\_achat, vente, sortie\_perte, sortie\_don, sortie\_échantillon, sortie\_usage\_interne, ajustement\_inventaire, transfert, annulation) | O | I | BOU-04 |
| quantite | Décimal(12,3) signé | O | I | Positive pour une entrée, négative pour une vente ou une sortie ; jamais nulle |
| date\_mouvement | DateHeure | O | I |  |
| motif | Texte | C | I | Obligatoire pour les sorties, ajustements et annulations |
| vente\_id, inventaire\_id, depot\_id | FK | C | I | Pièce d'origine du mouvement |
| mouvement\_annule\_id | FK mouvement\_stock | C | I | Pour une annulation : le mouvement contre-passé |
| emplacement | Énum (boutique, salle\_exposition) | O | I | Boutique par défaut ; salle\_exposition seulement si elle est activée pour le centre ; stock calculé par produit et emplacement (BOU-15, RG-BOU-16) |
| transfert\_lie\_id | FK mouvement\_stock | C | I | Pour un transfert : le mouvement de sens opposé, de même quantité, sur l'autre emplacement |
| auteur\_id | FK utilisateur | S | I | Ajout seul : ni modification ni suppression |

### vente

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| point\_de\_vente\_id | FK point\_de\_vente | O | I |  |
| numero\_recu | Entier | S | I | Numéro continu attribué sur l'appareil dans sa série (serie\_recu), sans trou dans la série ; unique (point\_de\_vente\_id, serie\_recu, numero\_recu) ; un numéro dont l'enregistrement échoue est consigné annulé |
| numero\_recu\_papier | Texte(30) | C | I | Saisie différée depuis le carnet de secours, en cas de panne de l'appareil |
| date\_heure\_vente | DateHeure | O | I | Date réelle de la vente, même en saisie différée |
| vendeur\_id | FK utilisateur | S | I | Rôle VB, ou RC, RA, AA par cumul |
| session\_caisse\_id | FK session\_caisse | S | I | Session ouverte du jour |
| total | Montant | S | I | Somme des lignes après remise |
| statut | Énum (validée, annulée) | S | I | Aucun champ sur l'acheteur |
| motif\_annulation | Texte | C | I | Obligatoire si annulée |
| vente\_annulation\_id | FK vente | C | I | Contre-écriture liée (BOU-06) |
| serie\_recu | Texte(12) | S | I | Série de l'appareil enrôlé qui a validé la vente (ex. CMR-B) (OFF-08) |
| emplacement | Énum (boutique, salle\_exposition) | O | I | Emplacement d'où sortent les articles ; mêmes reçus et même caisse (RG-BOU-16) |

### ligne\_vente

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| vente\_id, produit\_id | FK | O | I |  |
| quantite | Décimal(12,3) | O | I | Supérieure à 0 ; génère un mouvement de type vente |
| prix\_unitaire\_applique | Montant | S | I | Prix en vigueur à la date de la vente, figé |
| remise | Montant | F | I | Au plus le montant de la ligne |
| motif\_remise | Texte | C | I | Obligatoire si remise (BOU-03) |

### reglement

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| vente\_id | FK vente | O | I |  |
| mode | Énum (espèces, mobile\_money, virement, chèque) | O | I | Mobile Money confirmé par l'opérateur ou déclaré (section 9) ; aucun autre paiement électronique (A6, PAY-13) |
| montant | Montant | O | I | Supérieur à 0 ; somme des règlements = total de la vente |
| reference\_externe | Texte(60) | C | I | Obligatoire pour virement, chèque et Mobile Money déclaré (identifiant de transaction) |
| paiement\_id | FK paiement | C | I | Obligatoire pour mobile\_money : paiement qui porte le statut et la transaction de l'opérateur (section 9) |
| statut | Énum (confirme, declare, non\_retrouve) | S | I | Repris du paiement ; espèces, virement et chèque sont confirmés à la saisie ; seuls les règlements confirmés entrent dans les encaissements confirmés |

### session\_caisse

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| point\_de\_vente\_id, date | FK, Date | O | I | Unique (point\_de\_vente\_id, date) |
| ouverte\_par, fond\_de\_caisse | FK utilisateur, Montant | O | I |  |
| montants\_theoriques, montants\_comptes | Montant par mode de règlement | S, O | I | Théorique calculé sur les règlements ; compté saisi en fin de journée |
| ecart, motif\_ecart | Montant signé, Texte | S, C | I | Compté moins théorique ; motif obligatoire si écart non nul |
| compte\_par, valide\_par, valide\_le | FK, FK, DateHeure | S | I | Validation par le CPT, à défaut le RC ou le RA ; jamais par l'auteur d'une vente de la journée (BOU-05) |
| statut | Énum (ouverte, comptée, validée, validée\_avec\_écart) | S | I |  |

### inventaire

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| point\_de\_vente\_id, date\_inventaire | FK, Date | O | I |  |
| compte\_par, valide\_par, valide\_le | FK, FK, DateHeure | S | I | Validation par le RC ou le RA, distinct de celui qui a compté (BOU-07) |
| statut | Énum (en\_cours, compté, validé) | S | I | La validation génère les mouvements ajustement\_inventaire |

### ligne\_inventaire

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| inventaire\_id, produit\_id | FK | O | I | Unique (inventaire\_id, produit\_id) |
| quantite\_theorique | Décimal(12,3) | S | I | Stock calculé au moment du comptage |
| quantite\_comptee | Décimal(12,3) | O | I |  |
| ecart | Décimal(12,3) signé | S | I | Comptée moins théorique |

### reversement

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| beneficiaire\_id, groupement | FK beneficiaire, Texte(150) | C | N, I | Productrice ou groupement : exactement un des deux |
| periode\_debut, periode\_fin | Date | O | I |  |
| montant\_du | Montant | S | I | Ventes de ses produits sur la période moins la part du centre (BOU-08) |
| montant\_reverse | Montant | C | I | Obligatoire au statut payé ; le solde restant dû est calculé |
| date\_paiement, mode | Date, Énum (espèces, mobile\_money, virement, chèque) | C | I | Obligatoires au statut payé |
| piece\_justificative\_id | FK document | C | N | Obligatoire au statut payé |
| statut | Énum (préparé, validé, payé) | S | I |  |
| prepare\_par, valide\_par | FK | S | I | Préparé par le CPT, validé par le RC ou le RA, toujours distincts |

Accès aux déposantes : le VB ne voit que le nom et le code de la productrice sur l'article ; le CPT voit son identité minimale (nom, prénom, code, téléphone) pour les reversements, sans accès à la fiche bénéficiaire (Matrice des rôles).

**Clôture mensuelle et rapprochement (SRC-01, SRC-02).** Chaque montant (vente, encaissement de caisse, reversement, contribution financière reçue) n'est saisi qu'une fois ; la vue du CPT, le tableau de bord du RC et les rapports lisent les mêmes enregistrements. Chaque mois, l'outil génère l'état de rapprochement du centre : le CPT le vérifie, le RC (ou le RA en intérim) le valide, puis le mois est verrouillé (RG-SRC-02).

| Relation | Cardinalité | Règle |
| --- | --- | --- |
| centre, cloture\_mensuelle | 1 à n | Une seule clôture par centre et par mois |
| cloture\_mensuelle, ligne\_rapprochement | 1 à n | Une ligne par flux et par devise |

### cloture\_mensuelle

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id, mois | FK centre, Texte(7) AAAA-MM | O | I | Unique (centre\_id, mois) ; mois écoulé uniquement |
| statut | Énum (à\_faire, vérifiée, validée, validée\_avec\_écart) | S | I | Affiché sur le tableau de bord de centre (SRC-04) |
| totaux | Montant par flux (ventes, caisses, paiements de scolarité et services, reversements, contributions financières reçues) et par devise | S | I | Calculés par l'outil sur le mois à partir des enregistrements ; jamais saisis ; aucun total multi-devises |
| ecart, motif\_ecart | Montant signé par devise, Texte | S, C | I | Somme des écarts des lignes ; motif obligatoire si écart non nul |
| verifiee\_par, verifiee\_le | FK utilisateur, DateHeure | S | I | Rôle CPT |
| validee\_par, validee\_le | FK utilisateur, DateHeure | S | I | RC, ou RA en intérim ; toujours distinct de verifiee\_par (séparation des tâches, RG-SRC-02) |
| verrouillee | Booléen | S | I | Vrai dès la validation ; plus aucune écriture datée du mois n'est acceptée |
| cloture\_corrigee\_id | FK cloture\_mensuelle | F | I | Renseigné sur les régularisations : le mois corrigé (RG-SRC-03) |

### ligne\_rapprochement

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| cloture\_mensuelle\_id | FK cloture\_mensuelle | O | I |  |
| flux | Énum (ventes, caisses, paiements\_scolarite, reversements, contributions\_financieres\_recues) | O | I | Unique (cloture\_mensuelle\_id, flux, devise) |
| devise | Texte(3) ISO 4217 | O | I | GNF, USD ou EUR |
| montant\_outil | Montant | S | I | Calculé à partir des enregistrements du mois |
| montant\_piece | Montant | O | I | Saisi par le CPT d'après les pièces (caisse physique, relevés, carnet de reçus) |
| ecart | Montant signé | S | I | Pièce moins outil |
| motif | Texte | C | I | Obligatoire si écart non nul |
| piece\_justificative\_id | FK document | F | I | Relevé ou pièce de contrôle |

## 7. Intégrité, anti double comptage, sensibilité et conservation

Les règles ci-dessous sont imposées par la base elle-même (contraintes, clés uniques, vues de calcul), pas seulement par l'interface.

### 7.1 Contraintes d'intégrité

1. Clés uniques : `beneficiaire.code`, `(inscription.beneficiaire_id, session_id)`, `(presence.seance_id, inscription_id)`, `attestation.inscription_id`, `convention.reference`, `(referentiel_valeur.referentiel, code)`.
2. Aucune suppression en cascade sur un objet métier ; une clé étrangère vers un objet archivé reste valide.
3. Contrôles de cohérence en base : dates de fin postérieures aux dates de début, capacité et montants positifs, séance dans les dates de sa session, statut de contribution « reçue » impossible sans `date_reception` ni `montant_recu` ou `quantite`.
4. Verrou optimiste par le champ `version` : une modification basée sur une version périmée est refusée avec un message invitant à recharger.
5. Boutique : clés uniques (vente.point\_de\_vente\_id, serie\_recu, numero\_recu), (session\_caisse.point\_de\_vente\_id, date) et (ligne\_inventaire.inventaire\_id, produit\_id) ; numérotation des reçus continue et sans trou dans chaque série d'appareil ; stock jamais stocké dans un champ modifiable, toujours égal à la somme de mouvement\_stock.quantite ; mouvements, ventes, règlements et clôtures validées en ajout seul, sans suppression physique ni modification, l'annulation passant par une contre-écriture ; montants en GNF entiers ; somme des règlements égale au total de la vente ; un seul des champs beneficiaire\_id et groupement renseigné sur depot et reversement.
6. Clôture mensuelle : clés uniques (cloture\_mensuelle.centre\_id, mois) et (ligne\_rapprochement.cloture\_mensuelle\_id, flux, devise) ; verifiee\_par différent de validee\_par ; après validation, la clôture et ses lignes sont verrouillées et la base refuse toute écriture financière (vente, règlement, session de caisse, reversement, contribution reçue) datée du mois verrouillé ; toute correction passe par une écriture de régularisation datée du mois courant, référencée au mois corrigé (RG-SRC-03) ; totaux et écarts tenus par devise, sans total multi-devises.
7. Synchronisation : clé unique `operation_synchronisation.id` (UUID généré sur l'appareil), si bien qu'une opération reçue deux fois n'est appliquée qu'une fois ; `journal_changements` numéroté de façon croissante par centre, en ajout seul ; une opération rejetée ou en conflit n'écrit rien dans les tables métier ; un appareil révoqué ne peut plus envoyer d'opération (OFF-03 à OFF-06).
8. Paiements : clés uniques (transaction\_passerelle.fournisseur, identifiant\_operateur), (ligne\_releve\_operateur.fournisseur, identifiant\_operateur) et echeance.reference\_paiement ; montants en GNF entiers ; somme des affectations d'un paiement et somme de ses remboursements au plus égales à son montant confirmé ; paiements, affectations, transactions et remboursements en ajout seul ; auteur et valideur d'une exonération, demandeur et valideur d'un remboursement toujours distincts (PAY-03, PAY-08, PAY-11).
9. Modules : module\_centre en ajout seul ; toute écriture dans une table d'un module dont le statut en vigueur est « inactif » pour le centre est refusée par le serveur, y compris par la synchronisation, et les données existantes restent en lecture seule (RG-ADM-19).

### 7.2 Règles anti double comptage

| Risque | Règle de données |
| --- | --- |
| Une même personne comptée deux fois | Indicateurs de personnes calculés sur `beneficiaire.id` distincts, dossiers « fusionné » exclus |
| Promis compté comme reçu | Les montants reçus ne lisent que `montant_recu` des contributions « reçue » ou « validée » |
| Nature additionnée au financier | Totaux séparés par `contribution.financiere` ; aucune vue ne somme les deux |
| Sollicité, accordé, reçu mélangés | Trois sources distinctes : `proposition.montant_sollicite` (dernière version acceptée ou en cours), `convention.montant_accorde`, `contribution.montant_recu` |
| Versions de proposition cumulées | Seule la dernière version d'une proposition entre dans les totaux |
| Contribution répartie entre programmes | Une contribution porte un seul programme au MVP ; la répartition (CTR-08) créera des lignes d'affectation dont la somme est contrôlée égale au total |
| Devises | Totaux par devise (GNF devise de travail ; USD ou EUR pour les contributions de partenaires internationaux) ; aucun total multi-devises sans taux daté ; une conversion en GNF utilise le taux enregistré à la réception, jamais recalculé au taux du jour |
| Vente annulée comptée dans le chiffre d'affaires | Le chiffre d'affaires ne lit que les ventes au statut « validée » sans contre-écriture liée ; les ventes d'annulation n'entrent dans aucun total (IND-45, IND-46) |
| Chiffres différents entre comptable et responsable de centre | Chaque montant est saisi une seule fois (SRC-01) ; la vue du CPT, le tableau de bord du RC et les rapports lisent les mêmes enregistrements ; la clôture mensuelle rapproche l'outil et les pièces (SRC-02) |
| Paiement Mobile Money compté avant confirmation ou deux fois | Les encaissements ne lisent que les paiements « confirme » ; une transaction de l'opérateur n'est enregistrée qu'une fois ; les paiements déclarés s'affichent à part (PAY-08) |
| Paiement de la boutique compté deux fois | Le chiffre d'affaires lit les ventes ; les paiements Mobile Money de la boutique sont lus par le règlement lié ; les encaissements de scolarité ne lisent que les affectations à des échéances |
| Opération hors ligne appliquée deux fois | Unicité de l'identifiant d'opération généré sur l'appareil (OFF-03) |

### 7.3 Sensibilité et protection

| Niveau | Exemples | Protection |
| --- | --- | --- |
| P public ou institutionnel | Centres, formations, programmes | Lecture par tout utilisateur authentifié |
| I interne | Sessions, opportunités, conventions, ventes, stock et caisse de la boutique (aucune donnée sur l'acheteur), clôtures mensuelles et lignes de rapprochement, appareils, opérations de synchronisation, échéances et paiements, modules activés par centre | Droits de la Matrice |
| N nominatif | Identité et coordonnées des bénéficiaires, interlocuteurs, journal, lien vers la productrice déposante (produit, dépôt, reversement), numéro de téléphone de la payeuse (paiement) | Droits de la Matrice, périmètre centre, journalisation des exports |
| R restreint | Pièce d'identité, contact d'urgence, secrets d'authentification, chemins de stockage | Chiffrement au niveau du champ, droits limités, consultation journalisée |

Les environnements de développement et de préproduction n'utilisent que des données fictives ou anonymisées : noms remplacés, dates décalées, numéros supprimés (SEC-07).

### 7.4 Conservation (propositions à valider)

Les durées ci-dessous sont des propositions de travail ; elles doivent être arrêtées par la Direction avec un avis juridique sur les textes guinéens applicables (DM § 12.2, DAT § 6.3).

| Données | Durée proposée | Sort final |
| --- | --- | --- |
| Dossier bénéficiaire et parcours | 10 ans après la dernière activité | Anonymisation : l'historique statistique est conservé sans identité |
| Pièces justificatives nominatives | 5 ans après la clôture du dossier | Suppression du fichier |
| Candidature rejetée ou annulée | 2 ans | Anonymisation |
| Conventions, contributions et justificatifs | 10 ans après la fin de la convention | Archivage |
| Journal d'audit | 5 ans | Suppression |
| Comptes utilisateurs désactivés | Durée du journal qui les cite | Pseudonymisation |
| Rapports validés | Sans limite | Archivage |
| Boutique : ventes, règlements, clôtures de caisse, inventaires, mouvements de stock, dépôts, reversements et leurs pièces | 10 ans après la fin de l'exercice concerné (à valider) | Archivage ; le lien vers la productrice déposante suit ensuite la règle du dossier bénéficiaire (anonymisation) |
| Clôtures mensuelles, lignes de rapprochement et leurs pièces | 10 ans après la fin de l'exercice concerné (à valider) | Archivage |
| Intérims du responsable de centre | 5 ans, comme le journal d'audit | Suppression |
| Paiements, affectations, transactions de la passerelle, remboursements, relevés de l'opérateur et leurs pièces | 10 ans après la fin de l'exercice concerné (à valider) | Archivage ; le numéro de la payeuse est pseudonymisé après 2 ans |
| Opérations de synchronisation, journal des changements, conflits | 90 jours après application ou résolution | Suppression ; l'effet métier reste dans les tables et le journal d'audit |
| Appareils révoqués | Durée du journal qui les cite | Archivage |
| Décisions d'activation et de désactivation des modules | Sans limite | Archivage |

## 8. Synchronisation hors ligne

Quatre entités tracent les appareils de terrain et les opérations saisies hors ligne (OFF-01 à OFF-08, demande du porteur de projet du 13/10/2026) ; la mécanique est décrite au DAT détaillé, section 4.5. La base locale de l'appareil reprend un sous-ensemble des entités métier, limité au rôle et au périmètre de l'utilisateur, sans aucun champ R, et n'est jamais la référence.

| Relation | Cardinalité | Règle |
| --- | --- | --- |
| centre, appareil | 1 à n | Un appareil est enrôlé sur un seul centre |
| appareil, operation\_synchronisation ; utilisateur, operation\_synchronisation | 1 à n chacune | Une opération vient d'un seul appareil et d'un seul utilisateur |
| operation\_synchronisation, conflit\_synchronisation | 1 à 0 ou n | Un conflit par champ en conflit |
| centre, journal\_changements | 1 à n | Numéro croissant par centre |

### appareil

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I | Centre d'enrôlement |
| libelle | Texte(60) | O | I | Ex. « Tablette boutique » |
| utilisateur\_principal\_id | FK utilisateur | F | I |  |
| point\_de\_vente\_id, serie\_recu | FK point\_de\_vente, Texte(12) | C | I | Obligatoires si l'appareil vend ou encaisse ; série unique par point de vente (ex. CMR-B) |
| dernier\_numero\_recu | Entier | S | I | Dernier numéro accusé par le serveur ; contrôle de continuité de la série |
| enrole\_par, enrole\_le | FK utilisateur, DateHeure | S | I | RC ou admin. national |
| statut | Énum (actif, revoque) | S | I | Un appareil révoqué efface ses données locales au premier contact (OFF-06) |
| revoque\_par, revoque\_le, motif\_revocation | FK utilisateur, DateHeure, Texte | C | I | Obligatoires si révoqué |
| derniere\_synchronisation | DateHeure | S | I | Affichée sur E-OFF-01 ; alerte au RC après 48 heures d'opérations en attente (OFF-07) |
| ecart\_horloge\_secondes | Entier | S | I | Mesuré à la dernière synchronisation ; au-delà de 300, « horloge à vérifier » |

### operation\_synchronisation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| id | UUID | O | I | Généré sur l'appareil ; clé unique, donc une opération reçue deux fois n'est appliquée qu'une fois (OFF-03) |
| appareil\_id, utilisateur\_id | FK | O | I |  |
| type\_operation | Texte(60) | O | I | Ex. presence.saisir, vente.valider, paiement.declarer |
| objet\_type, objet\_id | Texte, UUID | O | I | Objet visé ; UUID généré sur l'appareil pour une création |
| donnees | JSON | O | N | Contenu de l'opération ; mêmes règles de sensibilité que l'objet visé, aucun champ R |
| version\_base | Entier | C | I | Version de l'objet sur l'appareil au moment de la saisie (modification) |
| horodatage\_appareil, recu\_le | DateHeure | O, S | I | Heure de saisie sur l'appareil ; heure de réception au serveur |
| resultat | Énum (appliquee, rejetee, en\_conflit, ecriture\_tardive) | S | I | Revérification au serveur (OFF-04) |
| motif\_rejet | Texte | C | I | Obligatoire si rejetée ; affiché dans « Mes rejets » |
| horloge\_a\_verifier | Booléen | S | I | Vrai si l'horloge de l'appareil s'écarte de plus de 5 minutes |

### journal\_changements

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I |  |
| numero | Entier | S | I | Croissant par centre ; curseur de réception des appareils ; unique (centre\_id, numero) |
| objet\_type, objet\_id | Texte, UUID | S | I |  |
| nature | Énum (creation, modification, archivage, retrait\_droit) | S | I | Un archivage ou un retrait de droit efface la copie locale |
| version | Entier | S | I | Version de l'objet après le changement |
| survenu\_le | DateHeure | S | I |  |

### conflit\_synchronisation

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| operation\_id | FK operation\_synchronisation | O | I |  |
| objet\_type, objet\_id, champ | Texte, UUID, Texte | O | I |  |
| valeur\_serveur, valeur\_appareil | Texte | O | Selon le champ | Valeur conservée et valeur proposée |
| statut | Énum (a\_resoudre, garde\_serveur, remplace, regularise) | S | I | File « À résoudre » (E-OFF-02) |
| resolu\_par, resolu\_le, motif | FK utilisateur, DateHeure, Texte | C | I | RC ou RA ; CPT pour une écriture tardive (OFF-05) |

## 9. Scolarité et paiements

Neuf entités enregistrent les services payants, ce que chaque bénéficiaire doit, et les paiements en espèces ou par Mobile Money avec leur rapprochement (PAY-01 à PAY-11, demande du porteur de projet du 13/10/2026). CAEF Connect ne détient jamais les fonds : `transaction_passerelle` reflète ce que l'opérateur a confirmé, et seule cette confirmation fait d'un paiement un encaissement (DAT détaillé, section 4.6). Les montants sont en GNF entiers, comme dans la boutique.

| Relation | Cardinalité | Règle |
| --- | --- | --- |
| centre, service\_payant ; service\_payant, tarif\_service | 1 à n chacune | Un seul tarif en vigueur par service et par date |
| beneficiaire, echeance ; inscription, echeance | 1 à n chacune | Une échéance par versement prévu par le tarif |
| echeance, exoneration | 1 à n | Exonérations validées au plus égales au montant de l'échéance |
| paiement, affectation\_paiement ; echeance, affectation\_paiement | 1 à n chacune | Un paiement peut régler plusieurs échéances ; un règlement de vente se lie au paiement par reglement.paiement\_id |
| paiement, transaction\_passerelle | 1 à 0 ou n | Notifications et consultations d'un même paiement ; une seule le confirme |
| paiement, remboursement | 1 à n |  |
| transaction\_passerelle, ligne\_releve\_operateur | 0 ou 1 à 0 ou 1 | Appariement du rapprochement quotidien |

### service\_payant

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I |  |
| code, libelle | Code, Texte(150) | O | P |  |
| nature | Énum (inscription, scolarite, examen, attestation, service\_associe) | O | I |  |
| formation\_id | FK formation | C | I | Obligatoire pour la scolarité |
| actif | Booléen | O | I | Désactivation au lieu de suppression |

### tarif\_service

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| service\_payant\_id | FK service\_payant | O | I |  |
| montant | Montant | O | I | GNF entier, supérieur à 0 |
| nombre\_versements, calendrier | Entier, Texte | O | I | Ex. 2 versements : à l'inscription et à mi-session |
| date\_debut, date\_fin | Date | O, S | I | Un seul tarif en vigueur à une date donnée (PAY-01) |
| decision\_reference | Texte(100) | O | I | Référence de la décision de la Direction Générale (H15) |

### echeance

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| beneficiaire\_id | FK beneficiaire | O | N |  |
| inscription\_id | FK inscription | C | I | Pour la scolarité d'une session |
| service\_payant\_id, tarif\_service\_id | FK | O | I | Tarif figé à la création |
| montant, date\_limite | Montant, Date | S | I |  |
| reference\_paiement | Texte(20) | S | I | Unique ; imprimée sur l'avis d'échéance (ex. CMR-26-04217) ; sert au paiement à l'initiative de la payeuse |
| montant\_exonere, montant\_paye, restant\_du | Montant | S | I | Calculés à partir des exonérations validées et des affectations de paiements confirmés ; jamais saisis |
| statut | Énum (a\_payer, partiellement\_payee, payee, exoneree, annulee) | S | I |  |

### exoneration

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| echeance\_id | FK echeance | O | I |  |
| type | Énum (bourse, reduction, partenaire, programme) | O | I |  |
| montant, motif | Montant, Texte | O | I | Au plus le restant dû |
| partenaire\_id, programme\_id | FK | C | I | Selon le type |
| piece\_justificative\_id | FK document | C | I | Obligatoire pour une bourse ou un partenaire |
| statut, valide\_par, valide\_le | Énum (proposee, validee, refusee), FK utilisateur, DateHeure | S | I | Valideur RC, toujours distinct de cree\_par (PAY-03) |

### paiement

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I |  |
| canal | Énum (especes, mobile\_money\_demande, mobile\_money\_payeuse, mobile\_money\_declare) | O | I | Parcours A, B ou C du DAT détaillé, section 4.6 |
| montant\_attendu | Montant | C | I | Montant demandé ou déclaré |
| montant\_confirme | Montant | S | I | Montant de l'opérateur, jamais celui de l'appareil (SEC-14) |
| commission, montant\_net | Montant | S | I | Selon la passerelle ; le brut est montant\_confirme |
| telephone\_payeuse | Texte(20) | C | N | Mobile Money ; jamais utilisé comme identifiant de personne (DAT-01) |
| identifiant\_transaction | Texte(60) | C | I | Saisi pour un paiement déclaré, repris de l'opérateur sinon |
| statut | Énum (initie, en\_attente, confirme, echoue, expire, declare, non\_retrouve, rembourse\_partiellement, rembourse) | S | I | Transitions de la SFD, section 12.3 |
| serie\_recu, numero\_recu | Texte(12), Entier | S | I | Reçu dans la série de l'appareil (OFF-08) |
| encaisse\_par, confirme\_le | FK utilisateur, DateHeure | S | I |  |

### affectation\_paiement

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| paiement\_id, echeance\_id | FK | O | I |  |
| montant | Montant | O | I | Somme par paiement au plus égale au montant confirmé |
| affecte\_par, motif | FK utilisateur, Texte | S, C | I | Motif obligatoire pour une affectation manuelle (PAY-06) |

### transaction\_passerelle

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| paiement\_id | FK paiement | O | I |  |
| fournisseur | Texte(30) | O | I | Agrégateur ou opérateur (H16) |
| identifiant\_operateur | Texte(60) | O | I | Unique (fournisseur, identifiant\_operateur) (PAY-08) |
| type | Énum (notification, consultation, remboursement) | O | I |  |
| statut\_operateur, montant, commission | Texte, Montant, Montant | O | I | Tels que reçus de l'opérateur |
| signature\_valide | Booléen | S | I | Faux : message rejeté et journalisé (SEC-14) |
| recu\_le | DateHeure | S | I |  |
| donnees\_brutes | JSON | S | N | Message de l'opérateur, sans secret, conservé pour l'audit |

### remboursement

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| paiement\_id | FK paiement | O | I |  |
| montant, motif | Montant, Texte | O | I | Somme des remboursements au plus égale au montant confirmé |
| demande\_par, valide\_par | FK utilisateur | S | I | Toujours distincts (PAY-11) |
| execution | Énum (passerelle, hors\_outil) | O | I |  |
| piece\_justificative\_id | FK document | C | I | Obligatoire hors outil |
| statut | Énum (demande, valide, refuse, execute) | S | I |  |

### ligne\_releve\_operateur

| Champ | Type | Obl. | Sens | Description et contrôle |
| --- | --- | --- | --- | --- |
| centre\_id | FK centre | O | I |  |
| fournisseur, date\_releve | Texte(30), Date | O | I | Relevé importé chaque nuit (API ou fichier) |
| identifiant\_operateur | Texte(60) | O | I | Unique (fournisseur, identifiant\_operateur) |
| montant, commission | Montant | O | I |  |
| transaction\_passerelle\_id | FK transaction\_passerelle | S | I | Appariement ; vide si la transaction manque côté outil |
| statut\_rapprochement | Énum (apparie, absent\_outil, absent\_releve, ecart\_montant) | S | I |  |
| motif | Texte | C | I | Obligatoire pour un écart, saisi par le CPT (PAY-10) |
