"""Gestion des affectations, intérims, habilitations exceptionnelles et modules par centre
(USR-02, USR-07, USR-09, ADM-08)."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from caef.commun.exceptions import RegleMetier, SeparationDesTaches
from caef.journal.models import ActionJournal
from caef.journal.services import instantane, journaliser

from .matrice import matrice
from .models import (Affectation, HabilitationExceptionnelle, InterimResponsable, ModuleCentre,
                     ModuleOptionnel, StatutModule)
from .services import aujourd_hui, invalider_cache, module_actif, verifier


# --------------------------------------------------------------------------- affectations

def affecter(acteur, *, utilisateur, role, centre=None, national=False, date_debut=None, date_fin=None, motif=""):
    """RG-ADM-06 et RG-ADM-12 : affectation journalisée avec l'auteur et le motif."""
    verifier(acteur, "utilisateur", "C", centre=centre)
    if not motif:
        raise RegleMetier("Le motif de l'affectation est obligatoire (RG-ADM-12).")
    role_code = getattr(role, "pk", role)
    if role_code not in matrice().roles:
        raise RegleMetier("Rôle inconnu.")
    if national and centre is not None:
        raise RegleMetier("Une affectation nationale ne porte pas de centre.")
    if not national and centre is None:
        raise RegleMetier("Le centre est obligatoire, sauf pour une affectation nationale sur décision tracée.")
    role_module = matrice().roles[role_code].module
    if role_module != "socle" and centre is not None and not module_actif(getattr(centre, "pk", centre), role_module):
        raise RegleMetier("Le module de ce rôle n'est pas activé pour le centre (Matrice § 5).")
    with transaction.atomic():
        aff = Affectation.objects.create(
            utilisateur=utilisateur, role_id=role_code, centre=centre, national=national,
            date_debut=date_debut or aujourd_hui(), date_fin=date_fin, motif=motif, cree_par=acteur,
        )
        journaliser(ActionJournal.DROITS, utilisateur=acteur, objet=aff, centre=centre,
                    apres=instantane(aff), motif=motif)
    invalider_cache(utilisateur)
    return aff


def retirer_affectation(acteur, affectation, motif):
    """L'ancien droit est retiré le jour même (Matrice § 5)."""
    verifier(acteur, "utilisateur", "M", centre=affectation.centre_id)
    if not motif:
        raise RegleMetier("Le motif du retrait est obligatoire (RG-ADM-12).")
    avant = instantane(affectation)
    with transaction.atomic():
        affectation.date_fin = aujourd_hui() - timedelta(days=1)
        if affectation.date_fin < affectation.date_debut:
            affectation.date_fin = affectation.date_debut
            affectation.archive = True
            affectation.archive_le = timezone.now()
        affectation.marquer_modifie(acteur)
        affectation.save()
        journaliser(ActionJournal.DROITS, utilisateur=acteur, objet=affectation, centre=affectation.centre_id,
                    avant=avant, apres=instantane(affectation), motif=motif)
    invalider_cache(affectation.utilisateur)


# --------------------------------------------------------------------------- intérims

def declarer_interim(acteur, *, centre, adjoint, date_debut, date_fin, motif):
    """RG-ADM-13 : déclaré par le RC ou l'ADM, au profit d'un RA actif du même centre."""
    verifier(acteur, "interim", "C", centre=centre)
    if not (date_debut and date_fin and motif):
        raise RegleMetier("Les dates de début et de fin et le motif sont obligatoires (RG-ADM-13).")
    if date_fin < date_debut:
        raise RegleMetier("La date de fin doit suivre la date de début.")
    centre_id = getattr(centre, "pk", centre)
    jour = aujourd_hui()
    est_ra = Affectation.objects.filter(
        utilisateur=adjoint, role_id="RA", centre_id=centre_id, archive=False, date_debut__lte=date_debut,
    ).filter(Q(date_fin__isnull=True) | Q(date_fin__gte=date_fin)).exists()
    if not est_ra:
        raise RegleMetier("Le bénéficiaire doit avoir une affectation de responsable adjoint active sur ce centre.")
    chevauchement = InterimResponsable.objects.filter(
        centre_id=centre_id, archive=False, date_debut__lte=date_fin, date_fin__gte=date_debut,
    ).filter(Q(interrompu_le__isnull=True) | Q(interrompu_le__gt=date_debut))
    if chevauchement.exists():
        raise RegleMetier("Un centre n'a qu'un intérim actif à la fois (RG-ADM-13).")
    from caef.referentiels.models import Centre

    responsable = Centre.objects.get(pk=centre_id).responsable or acteur
    with transaction.atomic():
        interim = InterimResponsable.objects.create(
            centre_id=centre_id, responsable_remplace=responsable, adjoint=adjoint, date_debut=date_debut,
            date_fin=date_fin, motif=motif, declare_par=acteur, cree_par=acteur,
        )
        journaliser(ActionJournal.DROITS, utilisateur=acteur, objet=interim, centre=centre_id,
                    apres=instantane(interim), motif=motif)
        _notifier_interim(interim, "interim_declare", f"Intérim déclaré du {date_debut:%d/%m/%Y} au {date_fin:%d/%m/%Y}")
    del jour
    return interim


def interrompre_interim(acteur, interim, motif):
    """RG-ADM-15 : interruption anticipée motivée par le RC ou l'ADM."""
    verifier(acteur, "interim", "M", centre=interim.centre_id)
    if not motif:
        raise RegleMetier("Le motif de l'interruption est obligatoire.")
    avant = instantane(interim)
    with transaction.atomic():
        interim.interrompu_le = aujourd_hui()
        interim.motif_interruption = motif
        interim.marquer_modifie(acteur)
        interim.save()
        journaliser(ActionJournal.DROITS, utilisateur=acteur, objet=interim, centre=interim.centre_id,
                    avant=avant, apres=instantane(interim), motif=motif)
        _notifier_interim(interim, "interim_interrompu", "Intérim interrompu")
    return interim


def _notifier_interim(interim, evenement, message):
    from caef.notifications.services import notifier

    notifier([interim.responsable_remplace, interim.adjoint], evenement, message, interim)


# --------------------------------------------------------------------------- habilitation exceptionnelle

def accorder_habilitation(acteur, *, utilisateur, objet_type, objet_id, date_debut, date_fin, demande_par, motif):
    """Matrice § 4 règle 2 : datée, limitée à un objet, 30 jours au plus, accordée par l'ADM."""
    verifier(acteur, "utilisateur", "C")
    if (date_fin - date_debut).days > settings.CAEF["HABILITATION_EXCEPTIONNELLE_JOURS_MAX"]:
        raise RegleMetier("Une habilitation exceptionnelle dure 30 jours au plus.")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        h = HabilitationExceptionnelle.objects.create(
            utilisateur=utilisateur, objet_type=objet_type, objet_id=objet_id, date_debut=date_debut,
            date_fin=date_fin, demande_par=demande_par, accorde_par=acteur, motif=motif, cree_par=acteur,
        )
        journaliser(ActionJournal.DROITS, utilisateur=acteur, objet=h, apres=instantane(h), motif=motif)
    return h


def habilitation_en_cours(utilisateur, objet_type, objet_id, jour=None):
    jour = jour or aujourd_hui()
    return HabilitationExceptionnelle.objects.filter(
        utilisateur=utilisateur, objet_type=objet_type, objet_id=objet_id, date_debut__lte=jour,
        date_fin__gte=jour, archive=False,
    ).exists()


# --------------------------------------------------------------------------- modules par centre

def operations_en_cours(centre_id, module) -> list[str]:
    """RG-ADM-19 : ce qui bloque une désactivation."""
    from caef.boutique.models import (Emplacement, Inventaire, MouvementStock, Reversement, SessionCaisse,
                                      StatutCaisse, StatutInventaire, StatutReversement)
    from caef.paiements.models import Paiement, StatutPaiement

    blocages = []
    if module == ModuleOptionnel.BOUTIQUE:
        if SessionCaisse.objects.filter(point_de_vente__centre_id=centre_id,
                                        statut__in=[StatutCaisse.OUVERTE, StatutCaisse.COMPTEE]).exists():
            blocages.append("Une caisse n'est pas validée.")
        if Inventaire.objects.filter(point_de_vente__centre_id=centre_id).exclude(
                statut=StatutInventaire.VALIDE).exists():
            blocages.append("Un inventaire n'est pas validé.")
        if Reversement.objects.filter(point_de_vente__centre_id=centre_id).exclude(
                statut=StatutReversement.PAYE).exists():
            blocages.append("Un reversement préparé n'est pas payé.")
    if module in (ModuleOptionnel.BOUTIQUE, ModuleOptionnel.SALLE_EXPOSITION):
        from django.db.models import Sum

        expose = (MouvementStock.objects.filter(produit__point_de_vente__centre_id=centre_id,
                                                emplacement=Emplacement.SALLE_EXPOSITION)
                  .aggregate(t=Sum("quantite"))["t"] or 0)
        if expose > 0:
            blocages.append("Des articles sont encore exposés dans la salle d'exposition.")
    if module in (ModuleOptionnel.SCOLARITE_PAIEMENTS, ModuleOptionnel.BOUTIQUE):
        en_attente = Paiement.objects.filter(
            centre_id=centre_id, statut__in=[StatutPaiement.INITIE, StatutPaiement.EN_ATTENTE, StatutPaiement.DECLARE])
        if module == ModuleOptionnel.BOUTIQUE:
            en_attente = en_attente.filter(usage_boutique=True)
        else:
            en_attente = en_attente.filter(usage_boutique=False)
        if en_attente.exists():
            blocages.append("Un paiement attend sa confirmation.")
        if module == ModuleOptionnel.SCOLARITE_PAIEMENTS:
            from caef.paiements.services import paiements_a_affecter

            if paiements_a_affecter(centre_id).exists():
                blocages.append("Un paiement reste à affecter.")
    return blocages


def saisir_changement_module(acteur, *, centre, module, statut, date_effet, decision_reference, decision_date, motif):
    """RG-ADM-18 : saisi par l'ADM avec la décision de la DG, puis validé par la DG."""
    verifier(acteur, "module_centre", "M", centre=centre)
    if module not in ModuleOptionnel.values:
        raise RegleMetier("Module inconnu ; le socle n'a pas de ligne et reste toujours actif (RG-ADM-17).")
    if not decision_reference or not decision_date:
        raise RegleMetier("La référence et la date de la décision de la Direction Générale sont obligatoires.")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    centre_id = getattr(centre, "pk", centre)
    if statut == StatutModule.ACTIF and module == ModuleOptionnel.SALLE_EXPOSITION and \
            not module_actif(centre_id, ModuleOptionnel.BOUTIQUE, date_effet):
        raise RegleMetier("La salle d'exposition ne s'active qu'avec la boutique.")
    if statut == StatutModule.INACTIF:
        blocages = operations_en_cours(centre_id, module)
        if blocages:
            raise RegleMetier("Désactivation refusée : " + " ".join(blocages), details={"blocages": blocages})
    with transaction.atomic():
        ligne = ModuleCentre.objects.create(
            centre_id=centre_id, module=module, statut=statut, date_effet=date_effet,
            decision_reference=decision_reference, decision_date=decision_date, motif=motif, saisi_par=acteur,
            cree_par=acteur,
        )
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=ligne, centre=centre_id,
                    apres=instantane(ligne), motif=motif)
    return ligne


def valider_changement_module(acteur, ligne: ModuleCentre):
    verifier(acteur, "module_centre", "V", centre=ligne.centre_id)
    if ligne.valide_par_id:
        raise RegleMetier("Ce changement est déjà validé.")
    if ligne.saisi_par_id == acteur.pk:
        raise SeparationDesTaches("La personne qui a saisi le changement ne peut pas le valider (RG-ADM-18).",
                                  objet="module_centre", action="V", centre_id=ligne.centre_id,
                                  objet_type="module_centre", objet_id=ligne.pk)
    if ligne.date_effet < aujourd_hui():
        raise RegleMetier("La date d'effet est au plus tôt le jour de la validation.")
    if ligne.statut == StatutModule.INACTIF:
        blocages = operations_en_cours(ligne.centre_id, ligne.module)
        if blocages:
            raise RegleMetier("Désactivation refusée : " + " ".join(blocages), details={"blocages": blocages})
    with transaction.atomic():
        ligne.valide_par = acteur
        ligne.valide_le = timezone.now()
        ligne._mise_a_jour_autorisee = True
        ligne.save(update_fields=["valide_par", "valide_le"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=ligne, centre=ligne.centre_id,
                    apres={"module": ligne.module, "statut": ligne.statut, "date_effet": ligne.date_effet},
                    motif=ligne.motif)
        from caef.notifications.services import notifier_role

        notifier_role(ligne.centre_id, ("RC",), "module_centre",
                      f"Module {ligne.get_module_display()} : {ligne.get_statut_display().lower()}", ligne)
    return ligne
