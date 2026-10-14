"""Tâches quotidiennes du suivi RSE (RG-CNV-07, RG-CNV-09, RG-PAR-04)."""

from celery import shared_task


@shared_task(name="caef.conventions.taches.marquer_engagements_en_retard")
def marquer_engagements_en_retard():
    from caef.partenaires.services import alerter_opportunites_sans_suite

    from .services import marquer_engagements_en_retard as marquer, rappels_echeances

    n = marquer()
    rappels_echeances()
    alerter_opportunites_sans_suite()
    return n
