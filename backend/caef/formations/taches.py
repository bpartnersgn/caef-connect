from celery import shared_task


@shared_task(name="caef.formations.taches.demarrer_sessions")
def demarrer_sessions():
    """Ouverte → En cours, automatiquement à la première séance passée (SFD 5.3)."""
    from .services import demarrer_sessions_echues

    return len(demarrer_sessions_echues())
