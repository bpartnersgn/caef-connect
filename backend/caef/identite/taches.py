from celery import shared_task


@shared_task(name="caef.identite.taches.suspendre_comptes_inactifs")
def suspendre_comptes_inactifs():
    from .services import suspendre_comptes_inactifs as suspendre

    return suspendre()
