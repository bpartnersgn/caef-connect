"""Propositions, conventions, engagements et contributions (SFD § 7).

Promis, signé, reçu et exécuté restent quatre états distincts, jamais additionnés entre eux ;
financier et en nature restent deux totaux séparés (DM § 9.3, CTR-07).
"""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from caef.commun.champs import verifier_gnf_entier
from caef.commun.codes import code_annuel, code_simple
from caef.commun.exceptions import RegleMetier, SeparationDesTaches
from caef.commun.services import enregistrer, exiger_statut, parametre, verifier_version
from caef.habilitations.services import aujourd_hui, roles_de, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import difference, instantane, journaliser
from caef.notifications.services import notifier, notifier_role
from caef.partenaires.services import avancer_etape_derivee
from caef.pilotage.verrou import verifier_mois_ouvert

from .models import (
    Contribution,
    Convention,
    DecisionValidation,
    Engagement,
    EtatEngagement,
    Proposition,
    StatutContribution,
    StatutConvention,
    StatutProposition,
    Validation,
)

METHODES_VALORISATION = ("facture", "devis", "prix_marche", "declaration_partenaire")


# --------------------------------------------------------------------------- propositions

CHAMPS_PROPOSITION = {"programme", "montant_sollicite", "devise", "nature", "budget_previsionnel",
                      "resultats_attendus", "calendrier"}


def creer_proposition(acteur, opportunite, *, centres_beneficiaires, **champs):
    """RG-CNV-01 : naît d'une opportunité, version 1."""
    verifier(acteur, "proposition", "C")
    if set(champs) - CHAMPS_PROPOSITION:
        raise RegleMetier("Champ inconnu.")
    if champs.get("devise", "GNF") == "GNF":
        verifier_gnf_entier(champs.get("montant_sollicite"))
    with transaction.atomic():
        prop = Proposition.objects.create(code=code_simple("PRO"), opportunite=opportunite,
                                          partenaire=opportunite.partenaire, cree_par=acteur, **champs)
        prop.centres_beneficiaires.set(centres_beneficiaires or opportunite.centres.all())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=prop, apres=instantane(prop))
        avancer_etape_derivee(acteur, opportunite, 6, "Proposition en préparation")
    return prop


def modifier_proposition(acteur, prop, version=None, **champs):
    """Un brouillon se modifie ; après soumission au circuit, toute modification crée une version."""
    verifier(acteur, "proposition", "M")
    verifier_version(prop, version)
    if prop.version_suivante_id:
        raise RegleMetier("Seule la dernière version d'une proposition se modifie.")
    if set(champs) - CHAMPS_PROPOSITION:
        raise RegleMetier("Champ inconnu.")
    if prop.statut == StatutProposition.BROUILLON:
        avant = instantane(prop)
        for k, v in champs.items():
            setattr(prop, k, v)
        with transaction.atomic():
            enregistrer(prop, acteur)
            av, ap = difference(avant, instantane(prop))
            journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=prop, avant=av, apres=ap)
        return prop
    if prop.statut in (StatutProposition.ACCEPTEE, StatutProposition.REFUSEE):
        raise RegleMetier("Une proposition acceptée ou refusée ne se modifie plus.")
    with transaction.atomic():
        nouvelle = Proposition.objects.create(
            code=prop.code, numero_version=prop.numero_version + 1, opportunite=prop.opportunite,
            partenaire=prop.partenaire, programme=champs.get("programme", prop.programme),
            montant_sollicite=champs.get("montant_sollicite", prop.montant_sollicite),
            devise=champs.get("devise", prop.devise), nature=champs.get("nature", prop.nature),
            budget_previsionnel=champs.get("budget_previsionnel", prop.budget_previsionnel),
            resultats_attendus=champs.get("resultats_attendus", prop.resultats_attendus),
            calendrier=champs.get("calendrier", prop.calendrier), cree_par=acteur)
        nouvelle.centres_beneficiaires.set(prop.centres_beneficiaires.all())
        prop.version_suivante = nouvelle
        enregistrer(prop, acteur, ["version_suivante"])
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=nouvelle, apres=instantane(nouvelle),
                    motif=f"Version {nouvelle.numero_version} de {prop.code}")
    return nouvelle


def soumettre_au_circuit(acteur, prop):
    """RG-CNV-02 : avis du responsable de chaque centre bénéficiaire, puis validation de la DG ;
    au-dessus du seuil fixé par la Direction, seconde validation de la DG."""
    verifier(acteur, "proposition", "M")
    exiger_statut(prop, (StatutProposition.BROUILLON,), "Soumettre au circuit de validation")
    with transaction.atomic():
        etape = 1
        for centre in prop.centres_beneficiaires.all():
            Validation.objects.create(objet_type="proposition", objet_id=prop.pk, etape=etape,
                                      valideur_attendu_role_id="RC", centre=centre, cree_par=acteur)
        etape += 1
        Validation.objects.create(objet_type="proposition", objet_id=prop.pk, etape=etape,
                                  valideur_attendu_role_id="DG", cree_par=acteur)
        seuil = parametre("SEUIL_SECONDE_VALIDATION_PROPOSITION")
        if seuil is not None and prop.devise == "GNF" and prop.montant_sollicite > Decimal(seuil):
            Validation.objects.create(objet_type="proposition", objet_id=prop.pk, etape=etape + 1,
                                      valideur_attendu_role_id="DG", cree_par=acteur)
        _statut_proposition(acteur, prop, StatutProposition.EN_VALIDATION)
        for centre in prop.centres_beneficiaires.all():
            notifier_role(centre.pk, ("RC",), "proposition_avis", f"Proposition {prop.code} : votre avis est attendu.",
                          prop)
    return prop


def validations_en_attente(prop):
    return Validation.objects.filter(objet_type="proposition", objet_id=prop.pk, decision="").order_by("etape")


def donner_decision(acteur, prop, decision, commentaire="", motif=None):
    """Avis du RC (favorable ou défavorable), puis validation ou rejet par la DG."""
    exiger_statut(prop, (StatutProposition.EN_VALIDATION,), "Décider")
    attente = list(validations_en_attente(prop))
    if not attente:
        raise RegleMetier("Aucune validation en attente.")
    etape_courante = attente[0].etape
    candidates = [v for v in attente if v.etape == etape_courante]
    ligne = None
    for v in candidates:
        if v.valideur_attendu_role_id in roles_de(acteur, v.centre_id):
            ligne = v
            break
    if ligne is None:
        from caef.commun.exceptions import AccesRefuse

        raise AccesRefuse("Cette étape du circuit attend un autre valideur.", objet="proposition", action="V")
    d = verifier(acteur, "proposition", "V", centre=ligne.centre_id)
    if Validation.objects.filter(objet_type="proposition", objet_id=prop.pk, decide_par=acteur).exists():
        raise SeparationDesTaches("Une même personne ne décide qu'une fois dans le circuit.", objet="proposition",
                                  action="V")
    negatif = decision in (DecisionValidation.DEFAVORABLE, DecisionValidation.REJETE)
    if negatif and (motif is None or not commentaire):
        raise RegleMetier("Un rejet ou un avis défavorable exige un motif et un commentaire (RG-CNV-04).")
    attendues = (DecisionValidation.FAVORABLE, DecisionValidation.DEFAVORABLE) if ligne.valideur_attendu_role_id == "RC" \
        else (DecisionValidation.VALIDE, DecisionValidation.REJETE)
    if decision not in attendues:
        raise RegleMetier("Décision attendue : " + " ou ".join(attendues))
    with transaction.atomic():
        ligne.decision = decision
        ligne.decide_par = acteur
        ligne.decide_le = timezone.now()
        ligne.commentaire = commentaire
        enregistrer(ligne, acteur)
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=prop, centre=ligne.centre_id,
                    apres={"etape": ligne.etape, "decision": decision}, motif=commentaire, interim=d.interim)
        if decision == DecisionValidation.REJETE:
            prop.motif = motif
            prop.commentaire = commentaire
            _statut_proposition(acteur, prop, StatutProposition.REJETEE)
        elif not validations_en_attente(prop).exists():
            _statut_proposition(acteur, prop, StatutProposition.VALIDEE)
    return prop


def marquer_soumise(acteur, prop, date_envoi):
    """RG-CNV-03 : seule une proposition « Validée » est envoyée ; date d'envoi obligatoire."""
    verifier(acteur, "proposition", "M")
    exiger_statut(prop, (StatutProposition.VALIDEE,), "Marquer soumise")
    if date_envoi is None:
        raise RegleMetier("La date d'envoi est obligatoire.")
    prop.date_envoi = date_envoi
    _statut_proposition(acteur, prop, StatutProposition.SOUMISE)
    avancer_etape_derivee(acteur, prop.opportunite, 7, "Proposition soumise")
    return prop


def enregistrer_reponse(acteur, prop, statut, date_reponse, motif=None, commentaire=""):
    verifier(acteur, "proposition", "M")
    if statut == StatutProposition.SUSPENDUE:
        if prop.statut in (StatutProposition.ACCEPTEE, StatutProposition.REFUSEE):
            raise RegleMetier("Proposition déjà tranchée.")
    else:
        exiger_statut(prop, (StatutProposition.SOUMISE,), "Enregistrer la réponse")
    if statut not in (StatutProposition.ACCEPTEE, StatutProposition.REFUSEE, StatutProposition.SUSPENDUE):
        raise RegleMetier("Réponse attendue : acceptée, refusée ou suspendue.")
    if statut != StatutProposition.ACCEPTEE and (motif is None or not commentaire):
        raise RegleMetier("Un refus ou une suspension exige un motif et un commentaire (RG-CNV-04).")
    prop.date_reponse = date_reponse
    prop.motif = motif
    prop.commentaire = commentaire
    _statut_proposition(acteur, prop, statut)
    if statut == StatutProposition.ACCEPTEE:
        avancer_etape_derivee(acteur, prop.opportunite, 8, "Proposition acceptée, négociation")
    return prop


def _statut_proposition(acteur, prop, statut):
    avant = prop.statut
    with transaction.atomic():
        prop.statut = statut
        enregistrer(prop, acteur)
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=prop, avant={"statut": avant},
                    apres={"statut": statut}, motif=prop.commentaire)
    return prop


# --------------------------------------------------------------------------- conventions

def creer_convention(acteur, *, partenaire, centres, proposition=None, **champs):
    verifier(acteur, "convention", "C")
    if proposition is not None and proposition.statut != StatutProposition.ACCEPTEE:
        raise RegleMetier("Une convention naît d'une proposition acceptée.")
    if champs.get("devise", "GNF") == "GNF":
        verifier_gnf_entier(champs.get("montant_accorde"))
    with transaction.atomic():
        conv = Convention.objects.create(reference=code_annuel("CNV", "NAT", aujourd_hui().year, 4),
                                         partenaire=partenaire, proposition=proposition, cree_par=acteur, **champs)
        conv.centres.set(centres)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=conv, apres=instantane(conv))
    return conv


def approuver_partenariat(acteur, conv):
    """Étape 9 « Partenariat approuvé » : validation de la Direction Générale."""
    verifier(acteur, "convention", "V")
    exiger_statut(conv, (StatutConvention.EN_PREPARATION,), "Approuver")
    journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=conv, apres={"approuve": True})
    if conv.proposition_id:
        avancer_etape_derivee(acteur, conv.proposition.opportunite, 9, "Partenariat approuvé")
    return conv


def signer_convention(acteur, conv, *, date_signature, signataires, document_signe, date_debut, date_fin,
                      echeancier=()):
    """RG-CNV-05 : date, signataires et document signé ; RG-CTR-02 : chaque apport prévu est créé
    « Promise » avec sa date prévue."""
    verifier(acteur, "convention", "M")
    exiger_statut(conv, (StatutConvention.EN_PREPARATION,), "Signer")
    if not (date_signature and signataires and document_signe):
        raise RegleMetier("Date de signature, signataires et document signé sont obligatoires (RG-CNV-05).")
    if document_signe.objet_type != "convention" or document_signe.objet_id != conv.pk:
        raise RegleMetier("Le document signé doit être déposé sur cette convention.")
    if date_fin < date_debut:
        raise RegleMetier("La date de fin doit suivre la date de début.")
    with transaction.atomic():
        conv.date_signature = date_signature
        conv.signataires = signataires
        conv.document_signe = document_signe
        conv.date_debut = date_debut
        conv.date_fin = date_fin
        conv.statut = StatutConvention.SIGNEE
        enregistrer(conv, acteur)
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=conv, avant={"statut": "en_preparation"},
                    apres={"statut": "signee", "date_signature": date_signature})
        for apport in echeancier:
            creer_contribution_promise(acteur, conv, **apport)
        if conv.proposition_id:
            opp = conv.proposition.opportunite
            avancer_etape_derivee(acteur, opp, 10, "Convention signée")
            from caef.partenaires.models import StatutOpportunite

            opp.statut = StatutOpportunite.GAGNEE
            enregistrer(opp, acteur, ["statut"])
    return conv


def ajouter_engagement(acteur, conv, *, partie, description, responsable, echeance, centre=None):
    verifier(acteur, "engagement", "C")
    with transaction.atomic():
        e = Engagement.objects.create(convention=conv, partie=partie, description=description,
                                      responsable=responsable, echeance=echeance, centre=centre, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=e, centre=centre, apres=instantane(e))
    return e


def declarer_engagement_realise(acteur, engagement, justificatif):
    """RG-CNV-08 : « Réalisé » avec justificatif."""
    verifier(acteur, "engagement", "M", centre=engagement.centre_id)
    exiger_statut(engagement, (EtatEngagement.A_REALISER, EtatEngagement.EN_COURS, EtatEngagement.EN_RETARD),
                  "Déclarer réalisé", champ="etat")
    if justificatif is None:
        raise RegleMetier("Un engagement réalisé doit porter un justificatif.")
    return _etat_engagement(acteur, engagement, EtatEngagement.REALISE, justificatif=justificatif)


def valider_engagement(acteur, engagement):
    verifier(acteur, "engagement", "V", centre=engagement.centre_id)
    exiger_statut(engagement, (EtatEngagement.REALISE,), "Valider", champ="etat")
    r = _etat_engagement(acteur, engagement, EtatEngagement.VALIDE, valide_par=acteur, validation=True)
    _avancer_execution(acteur, engagement.convention)
    return r


def abandonner_engagement(acteur, engagement, motif):
    verifier(acteur, "engagement", "M", centre=engagement.centre_id)
    if not motif:
        raise RegleMetier("Le motif d'abandon est obligatoire.")
    return _etat_engagement(acteur, engagement, EtatEngagement.ABANDONNE, motif_abandon=motif)


def _etat_engagement(acteur, engagement, etat, validation=False, **champs):
    avant = engagement.etat
    with transaction.atomic():
        engagement.etat = etat
        for k, v in champs.items():
            setattr(engagement, k, v)
        enregistrer(engagement, acteur)
        journaliser(ActionJournal.VALIDATION if validation else ActionJournal.STATUT, utilisateur=acteur,
                    objet=engagement, centre=engagement.centre_id, avant={"etat": avant}, apres={"etat": etat},
                    motif=champs.get("motif_abandon", ""))
        conv = engagement.convention
        if conv.statut == StatutConvention.SIGNEE and etat in (EtatEngagement.EN_COURS, EtatEngagement.REALISE):
            conv.statut = StatutConvention.EN_EXECUTION
            enregistrer(conv, acteur, ["statut"])
            if conv.proposition_id:
                avancer_etape_derivee(acteur, conv.proposition.opportunite, 11, "Engagement en cours d'exécution")
    return engagement


def _avancer_execution(acteur, conv):
    if conv.proposition_id and not conv.engagements.exclude(
            etat__in=[EtatEngagement.VALIDE, EtatEngagement.ABANDONNE]).exists():
        avancer_etape_derivee(acteur, conv.proposition.opportunite, 13, "Programme exécuté")


def marquer_engagements_en_retard(jour=None):
    """RG-CNV-07 : « En retard » le lendemain de l'échéance si non réalisé ; alerte au responsable."""
    jour = jour or aujourd_hui()
    qs = Engagement.objects.filter(echeance__lt=jour, etat__in=[EtatEngagement.A_REALISER, EtatEngagement.EN_COURS])
    n = 0
    for e in qs.select_related("responsable"):
        e.etat = EtatEngagement.EN_RETARD
        enregistrer(e, None, ["etat"])
        journaliser(ActionJournal.STATUT, objet=e, centre=e.centre_id, avant={"etat": "a_realiser"},
                    apres={"etat": "en_retard"}, motif="Échéance dépassée")
        notifier([e.responsable], "engagement_en_retard", f"Engagement en retard : {e.description[:120]}", e)
        n += 1
    return n


def rappels_echeances(jour=None):
    """RG-CNV-09 : rappels 30 et 7 jours avant l'échéance, 60 jours avant la fin de la convention."""
    jour = jour or aujourd_hui()
    for delai in (30, 7):
        for e in Engagement.objects.filter(echeance=jour + timedelta(days=delai)).exclude(
                etat__in=[EtatEngagement.REALISE, EtatEngagement.VALIDE, EtatEngagement.ABANDONNE]):
            notifier([e.responsable], "engagement_echeance", f"Échéance dans {delai} jours : {e.description[:120]}", e)
    for conv in Convention.objects.filter(date_fin=jour + timedelta(days=60),
                                          statut__in=[StatutConvention.SIGNEE, StatutConvention.EN_EXECUTION]):
        from caef.notifications.services import utilisateurs_du_role

        notifier(utilisateurs_du_role(None, "RSE"), "convention_fin", f"Convention {conv.reference} : fin dans 60 jours.",
                 conv)


def cloturer_convention(acteur, conv, rapport_transmis=False):
    """RG-CNV-10 : tous les engagements validés ou abandonnés avec motif."""
    verifier(acteur, "convention", "A")
    exiger_statut(conv, (StatutConvention.SIGNEE, StatutConvention.EN_EXECUTION), "Clôturer")
    if conv.engagements.exclude(etat__in=[EtatEngagement.VALIDE, EtatEngagement.ABANDONNE]).exists():
        raise RegleMetier("Tous les engagements doivent être validés ou abandonnés avec motif (RG-CNV-10).")
    avant = conv.statut
    with transaction.atomic():
        conv.statut = StatutConvention.CLOTUREE
        enregistrer(conv, acteur, ["statut"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=conv, avant={"statut": avant},
                    apres={"statut": "cloturee"})
        if conv.proposition_id:
            opp = conv.proposition.opportunite
            if rapport_transmis:
                avancer_etape_derivee(acteur, opp, 14, "Rapport d'impact transmis")
            avancer_etape_derivee(acteur, opp, 15, "Partenariat clôturé")
    return conv


# --------------------------------------------------------------------------- contributions

def creer_contribution_promise(acteur, conv, *, nature, centre_beneficiaire, date_prevue, montant_promis=None,
                               devise="GNF", programme=None, description_bien="", quantite=None,
                               valeur_estimee=None, methode_valorisation=""):
    verifier(acteur, "contribution", "C", centre=centre_beneficiaire)
    if nature == "financiere":
        if montant_promis is None:
            raise RegleMetier("Le montant promis est obligatoire pour une contribution financière.")
        if devise == "GNF":
            verifier_gnf_entier(montant_promis)
    elif valeur_estimee is not None and methode_valorisation not in METHODES_VALORISATION:
        raise RegleMetier("Méthode de valorisation obligatoire si une valeur est saisie (RG-CTR-05).")
    with transaction.atomic():
        c = Contribution.objects.create(
            code=code_simple("CTR"), convention=conv, partenaire=conv.partenaire, programme=programme or conv.programme,
            centre_beneficiaire=centre_beneficiaire, nature=nature, devise=devise, montant_promis=montant_promis,
            date_prevue=date_prevue, description_bien=description_bien, quantite=quantite,
            valeur_estimee=valeur_estimee, methode_valorisation=methode_valorisation, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=c, centre=centre_beneficiaire,
                    apres=instantane(c))
    return c


def enregistrer_reception(acteur, contribution, *, date_reception, justificatifs, montant_recu=None, quantite=None,
                          devise_origine="", montant_origine=None, taux_conversion=None, source_taux="",
                          valeur_estimee=None, methode_valorisation=""):
    """RG-CTR-03 : date, montant ou quantité reçus et justificatif obligatoires ; RG-CTR-06 :
    devise d'origine, taux et source conservés."""
    verifier(acteur, "contribution", "M", centre=contribution.centre_beneficiaire_id)
    exiger_statut(contribution, (StatutContribution.PROMISE,), "Enregistrer la réception")
    if not justificatifs:
        raise RegleMetier("Un justificatif (relevé, reçu, bon de livraison, procès-verbal) est obligatoire.",
                          code="justificatif_obligatoire")
    if date_reception is None or (montant_recu is None and quantite is None):
        raise RegleMetier("Date de réception et montant ou quantité reçus sont obligatoires.")
    if date_reception > aujourd_hui():
        raise RegleMetier("La date de réception ne peut être dans le futur.")
    if contribution.financiere:
        if montant_recu is None:
            raise RegleMetier("Le montant reçu est obligatoire pour une contribution financière.")
        if contribution.devise == "GNF":
            verifier_gnf_entier(montant_recu)
        if devise_origine and devise_origine != contribution.devise and (taux_conversion is None or not source_taux):
            raise RegleMetier("Une devise étrangère exige le taux de conversion et sa source (RG-CTR-06).")
        verifier_mois_ouvert(contribution.centre_beneficiaire_id, date_reception)
    elif valeur_estimee is not None and methode_valorisation not in METHODES_VALORISATION:
        raise RegleMetier("Méthode de valorisation obligatoire si une valeur est saisie (RG-CTR-05).")
    for doc in justificatifs:
        if doc.objet_type != "contribution" or doc.objet_id != contribution.pk:
            raise RegleMetier("Le justificatif doit être déposé sur cette contribution.")
    avant = instantane(contribution)
    with transaction.atomic():
        contribution.date_reception = date_reception
        contribution.montant_recu = montant_recu
        contribution.quantite = quantite if quantite is not None else contribution.quantite
        contribution.devise_origine = devise_origine
        contribution.montant_origine = montant_origine
        contribution.taux_conversion = taux_conversion
        contribution.source_taux = source_taux
        if valeur_estimee is not None:
            contribution.valeur_estimee = valeur_estimee
            contribution.methode_valorisation = methode_valorisation
        contribution.statut = StatutContribution.RECUE
        contribution.saisi_reception_par = acteur
        enregistrer(contribution, acteur)
        contribution.justificatifs.set(justificatifs)
        av, ap = difference(avant, instantane(contribution))
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=contribution,
                    centre=contribution.centre_beneficiaire_id, avant=av, apres=ap)
        avancer_etape_derivee(acteur, _opportunite_de(contribution), 12, "Contribution reçue")
        from caef.notifications.services import utilisateurs_du_role

        notifier(utilisateurs_du_role(None, "DG"), "contribution_a_valider",
                 f"Contribution {contribution.code} reçue : à valider.", contribution)
    return contribution


def _opportunite_de(contribution):
    prop = contribution.convention.proposition
    return prop.opportunite if prop else None


def valider_contribution(acteur, contribution):
    """RG-CTR-04 : par un responsable habilité autre que la personne qui a saisi la réception."""
    verifier(acteur, "contribution_validation", "V", centre=contribution.centre_beneficiaire_id)
    exiger_statut(contribution, (StatutContribution.RECUE,), "Valider")
    if contribution.saisi_reception_par_id == acteur.pk:
        raise SeparationDesTaches("La personne qui a saisi la réception ne peut pas la valider (RG-CTR-04).",
                                  objet="contribution_validation", action="V",
                                  centre_id=contribution.centre_beneficiaire_id, objet_type="contribution",
                                  objet_id=contribution.pk)
    with transaction.atomic():
        contribution.statut = StatutContribution.VALIDEE
        contribution.valide_par = acteur
        contribution.valide_le = timezone.now()
        enregistrer(contribution, acteur, ["statut", "valide_par", "valide_le"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=contribution,
                    centre=contribution.centre_beneficiaire_id, avant={"statut": "recue"}, apres={"statut": "validee"})
    return contribution


def rapprocher_contribution(acteur, contribution, *, reference_piece_comptable, date_encaissement_constatee):
    """RG-CTR-08 à 10 : le comptable du centre renvoie à la pièce comptable ; ne change pas le statut,
    ne vaut pas validation ; contributions financières seulement."""
    verifier(acteur, "contribution", "M", centre=contribution.centre_beneficiaire_id)
    if "CPT" not in roles_de(acteur, contribution.centre_beneficiaire_id):
        from caef.commun.exceptions import AccesRefuse

        raise AccesRefuse("Le rapprochement est fait par le comptable du centre (RG-CTR-08).",
                          objet="contribution", action="M", centre_id=contribution.centre_beneficiaire_id)
    if not contribution.financiere:
        raise RegleMetier("Les contributions non financières ne se rapprochent pas (RG-CTR-10).")
    exiger_statut(contribution, (StatutContribution.RECUE, StatutContribution.VALIDEE), "Rapprocher")
    if not reference_piece_comptable or date_encaissement_constatee is None:
        raise RegleMetier("Référence de pièce comptable et date d'encaissement constatée sont obligatoires.")
    avant = instantane(contribution, ["reference_piece_comptable", "date_encaissement_constatee"])
    with transaction.atomic():
        contribution.reference_piece_comptable = reference_piece_comptable
        contribution.date_encaissement_constatee = date_encaissement_constatee
        contribution.rapproche_par = acteur
        contribution.rapproche_le = timezone.now()
        enregistrer(contribution, acteur, ["reference_piece_comptable", "date_encaissement_constatee",
                                           "rapproche_par", "rapproche_le"])
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=contribution,
                    centre=contribution.centre_beneficiaire_id, avant=avant,
                    apres=instantane(contribution, ["reference_piece_comptable", "date_encaissement_constatee"]))
    return contribution


def annuler_contribution(acteur, contribution, motif):
    verifier(acteur, "contribution", "M", centre=contribution.centre_beneficiaire_id)
    if contribution.statut == StatutContribution.ANNULEE:
        raise RegleMetier("Déjà annulée.")
    if contribution.statut == StatutContribution.VALIDEE:
        raise RegleMetier("Une contribution validée ne s'annule pas : passez par une régularisation.")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    avant = contribution.statut
    with transaction.atomic():
        contribution.statut = StatutContribution.ANNULEE
        contribution.motif_annulation = motif
        enregistrer(contribution, acteur, ["statut", "motif_annulation"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=contribution,
                    centre=contribution.centre_beneficiaire_id, avant={"statut": avant}, apres={"statut": "annulee"},
                    motif=motif)
    return contribution


def totaux_contributions(qs) -> dict:
    """Quatre états distincts et deux familles séparées, par devise ; jamais additionnés entre eux.
    Signé = montant accordé des conventions signées (calculé ailleurs)."""
    resultat = {"financier": {}, "nature": {}}
    for famille, filtre in (("financier", True), ("nature", False)):
        sous = qs.filter(financiere=filtre).exclude(statut=StatutContribution.ANNULEE)
        champ_valeur = "montant_recu" if filtre else "valeur_estimee"
        for devise in sous.values_list("devise", flat=True).distinct():
            d = sous.filter(devise=devise)
            resultat[famille][devise] = {
                "promis": d.filter(statut=StatutContribution.PROMISE).aggregate(
                    t=Sum("montant_promis" if filtre else "valeur_estimee"))["t"],
                "recu": d.filter(statut=StatutContribution.RECUE).aggregate(t=Sum(champ_valeur))["t"],
                "valide": d.filter(statut=StatutContribution.VALIDEE).aggregate(t=Sum(champ_valeur))["t"],
                "non_valorise": d.filter(**{f"{champ_valeur}__isnull": True}).count() if not filtre else 0,
            }
    return resultat
