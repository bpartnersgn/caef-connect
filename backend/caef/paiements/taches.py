"""Tâches de la passerelle Mobile Money (RG-PAY-05, RG-PAY-07, RG-PAY-11)."""

from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task(name="caef.paiements.taches.consulter_paiement")
def consulter_paiement(paiement_id, minutes):
    from caef.commun.services import parametre

    from .models import Paiement
    from .services import consulter

    p = Paiement.objects.filter(pk=paiement_id).first()
    if p is not None:
        consulter(p, derniere=minutes >= max(parametre("PAIEMENT_CONSULTATIONS_MINUTES")))


@shared_task(name="caef.paiements.taches.marquer_non_retrouves")
def marquer_non_retrouves():
    """Paiements déclarés depuis 24 heures, et rattrapage des demandes restées en attente."""
    from .models import Paiement, StatutPaiement
    from .services import consulter
    from .services import marquer_non_retrouves as marquer

    limite = timezone.now() - timedelta(minutes=61)
    for p in Paiement.objects.filter(statut__in=[StatutPaiement.INITIE, StatutPaiement.EN_ATTENTE], cree_le__lt=limite):
        consulter(p, derniere=True)
    return marquer()


@shared_task(name="caef.paiements.taches.importer_releves")
def importer_releves():
    """Le relevé est lu par l'adaptateur de la passerelle retenue (H16) ; l'adaptateur déclaratif n'en
    fournit pas : le CPT importe alors le relevé par fichier (E-PAY-06)."""
    return 0
