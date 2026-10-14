"""Tâches nocturnes des dossiers (RG-BEN-04, SFD 4.4)."""

from celery import shared_task


@shared_task(name="caef.beneficiaires.taches.recalculer_doublons")
def recalculer_doublons():
    from .services import recalculer_paires, recalculer_statuts_dossiers

    return {"paires": recalculer_paires(), "inactifs": recalculer_statuts_dossiers()}
