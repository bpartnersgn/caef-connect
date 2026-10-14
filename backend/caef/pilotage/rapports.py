"""Rapports de centre, national et partenaire (RAP-01 à 04). Le contenu est figé à la génération,
tiré des valeurs d'indicateurs ; aucun nom de bénéficiaire, jamais (RG-RAP-02)."""

from django.db import transaction
from django.utils import timezone

from caef.commun.exceptions import RegleMetier
from caef.commun.services import enregistrer, exiger_statut
from caef.habilitations.services import verifier
from caef.journal.models import ActionJournal
from caef.journal.services import journaliser

from .indicateurs import calculer
from .models import FicheIndicateur, Rapport, StatutRapport, TypeRapport, ValeurIndicateur

OBJETS = {TypeRapport.CENTRE: "rapport_centre", TypeRapport.NATIONAL: "rapport_national",
          TypeRapport.PARTENAIRE: "rapport_partenaire"}


def _valeurs(centre_id, debut, fin, national=False):
    if not ValeurIndicateur.objects.filter(centre_id=centre_id, periode_debut=debut, periode_fin=fin).exists():
        calculer(debut, fin)
    valides = set(FicheIndicateur.objects.filter(statut="validee").values_list("code", flat=True))
    lignes = []
    for v in ValeurIndicateur.objects.filter(centre_id=centre_id, periode_debut=debut, periode_fin=fin) \
            .order_by("indicateur", "ventilation"):
        if national and v.indicateur not in valides:
            continue  # au national, seules les fiches validées s'affichent (TDB-01)
        lignes.append(valeur_publique(v))
    return lignes


def valeur_publique(v: ValeurIndicateur) -> dict:
    """Une valeur absente s'affiche « non renseigné », jamais 0 (RG-GEN-03)."""
    return {"indicateur": v.indicateur, "ventilation": v.ventilation,
            "valeur": str(v.valeur) if v.valeur is not None else None,
            "affichage": ("module non activé" if v.module_non_active else
                          "non renseigné" if v.valeur is None else str(v.valeur)),
            "valeur_declarative": str(v.valeur_declarative) if v.valeur_declarative is not None else None,
            "niveau": v.niveau, "nb_non_renseignes": v.nb_non_renseignes, "fige": v.fige,
            "details": {k: d for k, d in v.details.items() if k != "noms"}}


def _contenu_partenaire(convention, debut, fin):
    from caef.conventions.services import totaux_contributions

    return {
        "convention": convention.reference, "partenaire": convention.partenaire.raison_sociale,
        "statut": convention.get_statut_display(),
        "contributions": totaux_contributions(convention.contributions.all()),
        "engagements": list(convention.engagements.values("partie", "description", "echeance", "etat")),
        "centres": {str(c.pk): {"nom": c.nom, "indicateurs": _valeurs(c.pk, debut, fin)}
                    for c in convention.centres.all()},
    }


def generer_rapport(acteur, *, type, debut, fin, centre=None, convention=None, commentaire=""):
    if type not in OBJETS:
        raise RegleMetier("Type de rapport attendu : R-02, R-03 ou R-04 (le rapport de session est produit à "
                          "la clôture de la session).")
    if fin < debut:
        raise RegleMetier("La fin de période doit suivre son début.")
    objet = OBJETS[type]
    if type == TypeRapport.CENTRE:
        if centre is None:
            raise RegleMetier("Le centre est obligatoire.")
        verifier(acteur, objet, "C", centre=centre)
        contenu = {"indicateurs": _valeurs(centre.pk, debut, fin)}
    elif type == TypeRapport.NATIONAL:
        verifier(acteur, objet, "C")
        contenu = {"indicateurs": _valeurs(None, debut, fin, national=True)}
    else:
        if convention is None:
            raise RegleMetier("La convention est obligatoire.")
        verifier(acteur, objet, "C")
        contenu = _contenu_partenaire(convention, debut, fin)
    with transaction.atomic():
        r = Rapport.objects.create(type=type, centre=centre, convention=convention, periode_debut=debut,
                                   periode_fin=fin, contenu=contenu, commentaire=commentaire, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=r, centre=centre,
                    apres={"type": type, "debut": debut, "fin": fin})
    return r


def valider_rapport(acteur, rapport):
    verifier(acteur, OBJETS[rapport.type], "V", centre=rapport.centre_id)
    exiger_statut(rapport, (StatutRapport.BROUILLON,), "Valider")
    with transaction.atomic():
        rapport.statut = StatutRapport.VALIDE
        rapport.valide_par = acteur
        rapport.valide_le = timezone.now()
        enregistrer(rapport, acteur, ["statut", "valide_par", "valide_le"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=rapport, centre=rapport.centre_id,
                    avant={"statut": "brouillon"}, apres={"statut": "valide"})
    return rapport


def transmettre_rapport(acteur, rapport):
    verifier(acteur, OBJETS[rapport.type], "E" if rapport.type != TypeRapport.PARTENAIRE else "C",
             centre=rapport.centre_id)
    exiger_statut(rapport, (StatutRapport.VALIDE,), "Transmettre")
    with transaction.atomic():
        rapport.statut = StatutRapport.TRANSMIS
        rapport.transmis_le = timezone.now()
        enregistrer(rapport, acteur, ["statut", "transmis_le"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=rapport, centre=rapport.centre_id,
                    avant={"statut": "valide"}, apres={"statut": "transmis"})
    return rapport
