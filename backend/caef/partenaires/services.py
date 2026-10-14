"""Partenaires, opportunités, pipeline RSE et fiches projet (SFD § 6, RG-PAR-01 à 07)."""

from datetime import timedelta
from difflib import SequenceMatcher

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from caef.commun.codes import code_simple, normaliser
from caef.commun.exceptions import RegleMetier
from caef.commun.services import enregistrer, exiger_statut, verifier_version
from caef.habilitations.services import aujourd_hui, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import difference, instantane, journaliser
from caef.notifications.services import notifier

from .models import (
    DERNIERE_ETAPE_MANUELLE,
    ETAPES_PIPELINE,
    FicheProjet,
    HistoriqueEtape,
    Interaction,
    Interlocuteur,
    Opportunite,
    Partenaire,
    StatutFicheProjet,
    StatutOpportunite,
)


def _raison_normalisee(texte):
    mots_vides = {"sa", "sarl", "sas", "suarl", "ong", "la", "le", "les", "de", "des", "du", "et"}
    return " ".join(m for m in normaliser(texte).split() if m not in mots_vides)


def partenaires_proches(raison_sociale, sigle="") -> list[Partenaire]:
    """RG-PAR-01 : partenaires de nom ou sigle proche, affichés avant la création."""
    cible = _raison_normalisee(raison_sociale)
    q = Q(raison_sociale_normalisee=cible)
    if sigle:
        q |= Q(sigle__iexact=sigle.strip())
    premiers = cible.split()[:1]
    if premiers:
        q |= Q(raison_sociale_normalisee__contains=premiers[0])
    proches = []
    for p in Partenaire.objects.filter(q)[:200]:
        ratio = SequenceMatcher(None, cible, p.raison_sociale_normalisee).ratio()
        if ratio >= 0.8 or (sigle and p.sigle.lower() == sigle.strip().lower()):
            proches.append(p)
    return proches


def creer_partenaire(acteur, *, raison_sociale, confirme_nouveau=False, **champs):
    verifier(acteur, "partenaire", "C")
    proches = partenaires_proches(raison_sociale, champs.get("sigle", ""))
    if proches and not confirme_nouveau:
        raise RegleMetier("Des partenaires proches existent : confirmez qu'il s'agit d'une nouvelle organisation.",
                          code="partenaire_proche",
                          details={"proches": [{"id": str(p.pk), "code": p.code, "raison_sociale": p.raison_sociale}
                                               for p in proches]})
    with transaction.atomic():
        p = Partenaire.objects.create(code=code_simple("PAR"), raison_sociale=raison_sociale,
                                      raison_sociale_normalisee=_raison_normalisee(raison_sociale), cree_par=acteur,
                                      **champs)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=p, apres=instantane(p))
    return p


def modifier_partenaire(acteur, partenaire, version=None, **champs):
    verifier(acteur, "partenaire", "M")
    verifier_version(partenaire, version)
    avant = instantane(partenaire)
    for k, v in champs.items():
        setattr(partenaire, k, v)
    partenaire.raison_sociale_normalisee = _raison_normalisee(partenaire.raison_sociale)
    with transaction.atomic():
        enregistrer(partenaire, acteur)
        av, ap = difference(avant, instantane(partenaire))
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=partenaire, avant=av, apres=ap)
    return partenaire


def ajouter_interlocuteur(acteur, partenaire, *, principal=False, **champs):
    """Coordonnées professionnelles seulement (PAR-02)."""
    verifier(acteur, "interlocuteur", "C")
    with transaction.atomic():
        if principal:
            partenaire.interlocuteurs.filter(principal=True).update(principal=False)
        i = Interlocuteur.objects.create(partenaire=partenaire, principal=principal, cree_par=acteur, **champs)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=i, apres=instantane(i))
    return i


def enregistrer_interaction(acteur, partenaire, *, participants=(), interlocuteurs=(), **champs):
    verifier(acteur, "interlocuteur", "C")
    if champs.get("date_prochaine_action") and champs["date_prochaine_action"] < aujourd_hui():
        raise RegleMetier("La prochaine action doit être datée dans le futur.")
    with transaction.atomic():
        i = Interaction.objects.create(partenaire=partenaire, cree_par=acteur, **champs)
        i.participants_internes.set(participants)
        i.interlocuteurs.set(interlocuteurs)
        opp = i.opportunite
        if opp is not None and champs.get("prochaine_action"):
            opp.prochaine_action = champs["prochaine_action"]
            opp.date_prochaine_action = champs.get("date_prochaine_action")
            enregistrer(opp, acteur, ["prochaine_action", "date_prochaine_action"])
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=i, apres=instantane(i))
    return i


# --------------------------------------------------------------------------- opportunités

def creer_opportunite(acteur, *, partenaire, intitule, origine, centres, responsable, prochaine_action,
                      date_prochaine_action, fiches_projet=(), **champs):
    verifier(acteur, "opportunite", "C")
    if not centres:
        raise RegleMetier("Au moins un centre concerné est obligatoire.")
    _controler_prochaine_action(prochaine_action, date_prochaine_action)
    with transaction.atomic():
        opp = Opportunite.objects.create(
            code=code_simple("OPP"), partenaire=partenaire, intitule=intitule, origine=origine,
            responsable=responsable, prochaine_action=prochaine_action, date_prochaine_action=date_prochaine_action,
            cree_par=acteur, **champs)
        opp.centres.set(centres)
        for fiche in fiches_projet:
            rattacher_fiche_projet(acteur, opp, fiche)
        HistoriqueEtape.objects.create(opportunite=opp, etape_avant=None, etape_apres=opp.etape,
                                       date=timezone.now(), auteur=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=opp, apres=instantane(opp))
    return opp


def _controler_prochaine_action(action, date):
    if not action or date is None:
        raise RegleMetier("La prochaine action et sa date sont obligatoires tant que l'opportunité n'est pas close.")
    if date < aujourd_hui():
        raise RegleMetier("La prochaine action doit être datée dans le futur.")


def changer_etape(acteur, opp, etape: int, commentaire=""):
    """RG-PAR-02 et 03 : étapes 1 à 8 à la main ; sauter en avant exige un commentaire, reculer
    un motif ; 9 à 15 dérivées des statuts."""
    verifier(acteur, "opportunite", "M")
    exiger_statut(opp, (StatutOpportunite.OUVERTE,), "Changer d'étape")
    if etape not in ETAPES_PIPELINE:
        raise RegleMetier("Étape inconnue.")
    if etape > DERNIERE_ETAPE_MANUELLE or opp.etape > DERNIERE_ETAPE_MANUELLE:
        raise RegleMetier("Les étapes 9 à 15 suivent les statuts de la proposition, de la convention et des "
                          "contributions : elles ne se modifient pas à la main.", code="etape_derivee")
    if etape == opp.etape:
        return opp
    if etape > opp.etape + 1 and not commentaire:
        raise RegleMetier("Sauter une étape exige un commentaire.")
    if etape < opp.etape and not commentaire:
        raise RegleMetier("Revenir en arrière exige un motif.")
    return _poser_etape(acteur, opp, etape, commentaire)


def _poser_etape(acteur, opp, etape, commentaire=""):
    avant = opp.etape
    with transaction.atomic():
        opp.etape = etape
        enregistrer(opp, acteur, ["etape"])
        HistoriqueEtape.objects.create(opportunite=opp, etape_avant=avant, etape_apres=etape, date=timezone.now(),
                                       auteur=acteur, commentaire=commentaire)
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=opp, avant={"etape": avant},
                    apres={"etape": etape}, motif=commentaire)
    return opp


def avancer_etape_derivee(acteur, opp, etape: int, commentaire=""):
    """Appelé par les services de proposition, convention et contribution (étapes 7, 9 à 15)."""
    if opp is None or etape <= opp.etape:
        return opp
    return _poser_etape(acteur, opp, etape, commentaire)


def clore_opportunite(acteur, opp, statut, motif, commentaire=""):
    """« Perdue » ou « Suspendue » à tout moment, motif du référentiel obligatoire."""
    verifier(acteur, "opportunite", "A")
    if statut not in (StatutOpportunite.PERDUE, StatutOpportunite.SUSPENDUE):
        raise RegleMetier("Statut de clôture attendu : Perdue ou Suspendue.")
    if motif is None:
        raise RegleMetier("Le motif est obligatoire.")
    avant = opp.statut
    with transaction.atomic():
        opp.statut = statut
        opp.motif_cloture = motif
        enregistrer(opp, acteur, ["statut", "motif_cloture"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=opp, avant={"statut": avant},
                    apres={"statut": statut}, motif=commentaire or motif.libelle)
    return opp


def durees_par_etape(opp) -> dict:
    """RG-PAR-03 : durée passée dans chaque étape, en jours."""
    historique = list(opp.historique.order_by("date"))
    durees = {}
    for i, h in enumerate(historique):
        fin = historique[i + 1].date if i + 1 < len(historique) else timezone.now()
        durees[h.etape_apres] = durees.get(h.etape_apres, 0) + (fin - h.date).days
    return durees


def alerter_opportunites_sans_suite(jour=None):
    """RG-PAR-04 : sans prochaine action, ou action dépassée de 7 jours."""
    jour = jour or aujourd_hui()
    qs = Opportunite.objects.filter(statut=StatutOpportunite.OUVERTE, archive=False).filter(
        Q(date_prochaine_action__isnull=True) | Q(date_prochaine_action__lt=jour - timedelta(days=7)))
    for opp in qs.select_related("responsable"):
        notifier([opp.responsable], "opportunite_sans_suite",
                 f"Opportunité {opp.code} : prochaine action absente ou dépassée.", opp)
    return qs.count()


# --------------------------------------------------------------------------- fiches projet

def creer_fiche_projet(acteur, *, centre, **champs):
    verifier(acteur, "fiche_projet", "C", centre=centre)
    with transaction.atomic():
        f = FicheProjet.objects.create(centre=centre, cree_par=acteur, **champs)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=f, centre=centre, apres=instantane(f))
    return f


def qualifier_fiche_projet(acteur, fiche, qualifiee=True, motif=""):
    verifier(acteur, "fiche_projet", "V", centre=fiche.centre_id)
    exiger_statut(fiche, (StatutFicheProjet.BROUILLON,), "Qualifier")
    statut = StatutFicheProjet.QUALIFIEE if qualifiee else StatutFicheProjet.ABANDONNEE
    if not qualifiee and not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        fiche.statut = statut
        enregistrer(fiche, acteur, ["statut"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=fiche, centre=fiche.centre_id,
                    avant={"statut": "brouillon"}, apres={"statut": statut}, motif=motif)
    return fiche


def rattacher_fiche_projet(acteur, opp, fiche):
    """RG-PAR-06 : une fiche « Qualifiée » rattachée passe « Rattachée »."""
    verifier(acteur, "opportunite", "M")
    if fiche.statut not in (StatutFicheProjet.QUALIFIEE, StatutFicheProjet.RATTACHEE):
        raise RegleMetier("Seule une fiche projet qualifiée se rattache à une opportunité.")
    with transaction.atomic():
        opp.fiches_projet.add(fiche)
        if fiche.statut == StatutFicheProjet.QUALIFIEE:
            fiche.statut = StatutFicheProjet.RATTACHEE
            enregistrer(fiche, acteur, ["statut"])
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=opp,
                    apres={"fiche_projet_rattachee": str(fiche.pk)})
    return opp
