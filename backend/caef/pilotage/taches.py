"""Tâches de fond du pilotage (DAT § 2)."""

from celery import shared_task


@shared_task(name="caef.pilotage.taches.calculer_indicateurs")
def calculer_indicateurs():
    from .indicateurs import calculer_indicateurs as calculer

    calculer()


@shared_task(name="caef.pilotage.taches.generer_clotures_du_mois")
def generer_clotures_du_mois():
    from .cloture import generer_clotures_du_mois as generer

    return len(generer())
