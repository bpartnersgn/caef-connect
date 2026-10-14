"""Alerte sur les appareils en retard de synchronisation (OFF-04, RG-OFF-08)."""

from datetime import timedelta

from celery import shared_task
from django.db.models import Q
from django.utils import timezone


@shared_task(name="caef.synchronisation.taches.alerter_appareils_en_retard")
def alerter_appareils_en_retard():
    from caef.commun.services import parametre
    from caef.notifications.services import notifier_role

    from .models import Appareil, StatutAppareil

    limite = timezone.now() - timedelta(hours=parametre("ALERTE_SYNCHRO_HEURES"))
    n = 0
    for a in Appareil.objects.filter(statut=StatutAppareil.ACTIF).filter(
            Q(plus_ancienne_operation_en_attente__lt=limite) | Q(derniere_synchronisation__lt=limite)):
        notifier_role(a.centre_id, ("RC", "RA"), "appareil_non_synchronise",
                      f"L'appareil {a.libelle} n'a pas synchronisé depuis plus de 48 heures.", a)
        n += 1
    return n
