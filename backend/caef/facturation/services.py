"""Services payants, tarifs datés, échéances et exonérations (SFD § 12, RG-PAY-01, 02, 10).

La politique tarifaire (H15) n'est pas décidée : aucun montant n'est codé ici. Les tarifs sont
saisis par l'admin. national sur décision de la DG ; sans tarif en vigueur, aucune échéance.
"""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from caef.commun.champs import verifier_gnf_entier
from caef.commun.codes import prochain_numero
from caef.commun.exceptions import RegleMetier, SeparationDesTaches
from caef.commun.services import enregistrer, exiger_statut, origine
from caef.habilitations.services import aujourd_hui, module_actif, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import instantane, journaliser
from caef.notifications.services import notifier_role

from .models import (Echeance, Exoneration, ServicePayant, StatutEcheance, StatutExoneration, TarifService,
                     TypeExoneration)


def _gnf(v, libelle):
    from django.core.exceptions import ValidationError

    try:
        verifier_gnf_entier(v, libelle)
    except ValidationError as e:
        raise RegleMetier(e.messages[0], code="montant_non_entier")
    return Decimal(v)


def creer_service(acteur, *, centre, code, libelle, nature, formation=None):
    verifier(acteur, "service_tarif", "C", centre=centre)
    with transaction.atomic():
        s = ServicePayant.objects.create(centre=centre, code=code, libelle=libelle, nature=nature,
                                         formation=formation, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=s, centre=centre, apres=instantane(s))
    return s


def tarif_en_vigueur(service, jour=None) -> TarifService | None:
    jour = jour or aujourd_hui()
    return (TarifService.objects.filter(service_payant=service, date_debut__lte=jour, archive=False)
            .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=jour)).order_by("-date_debut").first())


def definir_tarif(acteur, service, *, montant, date_debut, decision_reference, nombre_versements=1, calendrier=None):
    """RG-PAY-01 : nouvelle période datée et tracée ; les échéances existantes gardent leur montant."""
    verifier(acteur, "service_tarif", "M", centre=service.centre_id)
    montant = _gnf(montant, "Le montant")
    if montant <= 0:
        raise RegleMetier("Le montant doit être supérieur à 0.")
    if not decision_reference:
        raise RegleMetier("La référence de la décision de la Direction Générale est obligatoire.")
    calendrier = list(calendrier or [0] * nombre_versements)
    if len(calendrier) != nombre_versements:
        raise RegleMetier("Le calendrier doit donner un délai pour chaque versement.")
    with transaction.atomic():
        courant = TarifService.objects.select_for_update().filter(service_payant=service, date_fin__isnull=True).first()
        if courant is not None:
            if courant.date_debut >= date_debut:
                raise RegleMetier("Un tarif plus récent existe déjà.")
            courant.date_fin = date_debut - timedelta(days=1)
            enregistrer(courant, acteur, ["date_fin"])
        t = TarifService.objects.create(service_payant=service, montant=montant, nombre_versements=nombre_versements,
                                        calendrier=calendrier, date_debut=date_debut,
                                        decision_reference=decision_reference, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=t, centre=service.centre_id, apres=instantane(t),
                    motif=decision_reference)
    return t


def reference_paiement(centre) -> str:
    """Courte et facile à dicter (ex. CMR-26-04217)."""
    annee = aujourd_hui().year % 100
    n = prochain_numero(f"REFPAY-{centre.code}-{annee}")
    return f"{centre.code}-{annee:02d}-{n:05d}"


def creer_echeances_inscription(acteur, inscription) -> list[Echeance]:
    """RG-PAY-02 : l'inscription crée les échéances des services liés à la formation, si le module
    est activé et qu'un tarif est en vigueur. Un impayé n'empêche ni l'inscription ni la présence."""
    session = inscription.session
    centre = session.centre
    if not module_actif(centre.pk, "scolarite_paiements"):
        return []
    creees = []
    jour = inscription.date_inscription
    services = ServicePayant.objects.filter(centre=centre, actif=True, archive=False).filter(
        Q(formation=session.formation) | Q(formation__isnull=True, nature="inscription"))
    for service in services:
        tarif = tarif_en_vigueur(service, jour)
        if tarif is None:
            continue
        parts = _repartir(tarif.montant, tarif.nombre_versements)
        for rang, (part, delai) in enumerate(zip(parts, tarif.calendrier), start=1):
            e = Echeance.objects.create(
                beneficiaire=inscription.beneficiaire, centre=centre, inscription=inscription, service_payant=service,
                tarif_service=tarif, rang=rang, montant=part, date_limite=jour + timedelta(days=int(delai)),
                reference_paiement=reference_paiement(centre), restant_du=part, cree_par=acteur, **origine())
            journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=e, centre=centre, apres=instantane(e))
            creees.append(e)
    return creees


def _repartir(montant: Decimal, n: int) -> list[Decimal]:
    """Versements entiers en GNF ; le reste de la division va au premier versement."""
    base = (montant // n)
    parts = [base] * n
    parts[0] += montant - base * n
    return parts


def recalculer_echeance(echeance: Echeance) -> Echeance:
    """Exonéré, payé et restant dû sont calculés, jamais saisis (Modèle § 9)."""
    from caef.paiements.models import STATUTS_ENCAISSES, AffectationPaiement, Remboursement

    exonere = Exoneration.objects.filter(echeance=echeance, statut=StatutExoneration.VALIDEE).aggregate(
        t=Sum("montant"))["t"] or Decimal(0)
    paye = AffectationPaiement.objects.filter(echeance=echeance, paiement__statut__in=STATUTS_ENCAISSES).aggregate(
        t=Sum("montant"))["t"] or Decimal(0)
    rembourse = Remboursement.objects.filter(echeance=echeance, statut="execute").aggregate(
        t=Sum("montant"))["t"] or Decimal(0)
    paye -= rembourse
    echeance.montant_exonere = exonere
    echeance.montant_paye = paye
    echeance.restant_du = max(echeance.montant - exonere - paye, Decimal(0))
    if echeance.statut != StatutEcheance.ANNULEE:
        if echeance.restant_du == 0 and exonere >= echeance.montant:
            echeance.statut = StatutEcheance.EXONEREE
        elif echeance.restant_du == 0:
            echeance.statut = StatutEcheance.PAYEE
        elif paye > 0:
            echeance.statut = StatutEcheance.PARTIELLEMENT_PAYEE
        else:
            echeance.statut = StatutEcheance.A_PAYER
    echeance.save(update_fields=["montant_exonere", "montant_paye", "restant_du", "statut"])
    return echeance


def proposer_exoneration(acteur, echeance, *, type, montant=None, pourcentage=None, motif, piece_justificative=None,
                         partenaire=None, programme=None):
    verifier(acteur, "exoneration", "C", centre=echeance.centre_id)
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    if montant is None and pourcentage is not None:
        montant = (Decimal(echeance.montant) * Decimal(pourcentage) / 100).quantize(Decimal(1))
    montant = _gnf(montant, "Le montant de l'exonération")
    recalculer_echeance(echeance)
    if montant <= 0 or montant > echeance.restant_du:
        raise RegleMetier("L'exonération est positive et au plus égale au restant dû.",
                          details={"restant_du": str(echeance.restant_du)})
    if type in (TypeExoneration.BOURSE, TypeExoneration.PARTENAIRE) and piece_justificative is None:
        raise RegleMetier("Une bourse ou une prise en charge partenaire exige une pièce.")
    with transaction.atomic():
        ex = Exoneration.objects.create(echeance=echeance, type=type, montant=montant, motif=motif,
                                        piece_justificative=piece_justificative, partenaire=partenaire,
                                        programme=programme, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=ex, centre=echeance.centre_id,
                    apres=instantane(ex), motif=motif)
        notifier_role(echeance.centre_id, ("RC",), "exoneration_a_valider", "Exonération proposée : à valider.", ex)
    return ex


def decider_exoneration(acteur, ex, valider: bool, motif=""):
    """RG-PAY-10 : validée par le RC (ou le RA en intérim), jamais par son auteur ; réduit le restant
    dû sans créer d'encaissement."""
    echeance = ex.echeance
    decision = verifier(acteur, "exoneration", "V", centre=echeance.centre_id)
    exiger_statut(ex, (StatutExoneration.PROPOSEE,), "Décider")
    if ex.cree_par_id == acteur.pk:
        raise SeparationDesTaches("L'auteur de l'exonération ne la valide pas (RG-PAY-10).", objet="exoneration",
                                  action="V", centre_id=echeance.centre_id, objet_type="exoneration", objet_id=ex.pk)
    if valider:
        recalculer_echeance(echeance)
        if ex.montant > echeance.restant_du:
            raise RegleMetier("L'exonération dépasse désormais le restant dû.")
    elif not motif:
        raise RegleMetier("Le motif du refus est obligatoire.")
    with transaction.atomic():
        ex.statut = StatutExoneration.VALIDEE if valider else StatutExoneration.REFUSEE
        ex.valide_par = acteur
        ex.valide_le = timezone.now()
        enregistrer(ex, acteur, ["statut", "valide_par", "valide_le"])
        recalculer_echeance(echeance)
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=ex, centre=echeance.centre_id,
                    avant={"statut": "proposee"}, apres={"statut": ex.statut}, motif=motif, interim=decision.interim)
    return ex


def situation(beneficiaire, centre_ids=None) -> dict:
    """E-PAY-02 : échéances, exonérations, paiements et restant dû."""
    echeances = Echeance.objects.filter(beneficiaire=beneficiaire).exclude(statut=StatutEcheance.ANNULEE)
    if centre_ids is not None:
        echeances = echeances.filter(centre_id__in=centre_ids)
    return {
        "echeances": [
            {"id": str(e.pk), "service": e.service_payant.libelle, "rang": e.rang, "montant": str(e.montant),
             "date_limite": e.date_limite.isoformat(), "reference_paiement": e.reference_paiement,
             "exonere": str(e.montant_exonere), "paye": str(e.montant_paye), "restant_du": str(e.restant_du),
             "statut": e.statut}
            for e in echeances.select_related("service_payant")
        ],
        "restant_du": str(echeances.aggregate(t=Sum("restant_du"))["t"] or 0),
    }
