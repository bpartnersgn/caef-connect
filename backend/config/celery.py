import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("caef")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Tâches périodiques (DAT § 2, § 4.5, § 4.6) ; heures de Conakry (GMT).
app.conf.beat_schedule = {
    "indicateurs-nocturnes": {"task": "caef.pilotage.taches.calculer_indicateurs", "schedule": crontab(hour=1, minute=0)},
    "doublons-nocturnes": {"task": "caef.beneficiaires.taches.recalculer_doublons", "schedule": crontab(hour=1, minute=30)},
    "generer-clotures-mensuelles": {"task": "caef.pilotage.taches.generer_clotures_du_mois", "schedule": crontab(day_of_month=1, hour=0, minute=30)},
    "rapprochement-operateur": {"task": "caef.paiements.taches.importer_releves", "schedule": crontab(hour=2, minute=0)},
    "paiements-non-retrouves": {"task": "caef.paiements.taches.marquer_non_retrouves", "schedule": crontab(minute=15)},
    "engagements-en-retard": {"task": "caef.conventions.taches.marquer_engagements_en_retard", "schedule": crontab(hour=0, minute=10)},
    "alertes-synchronisation": {"task": "caef.synchronisation.taches.alerter_appareils_en_retard", "schedule": crontab(minute=0)},
    "sessions-demarrees": {"task": "caef.formations.taches.demarrer_sessions", "schedule": crontab(hour=0, minute=5)},
    "comptes-inactifs": {"task": "caef.identite.taches.suspendre_comptes_inactifs", "schedule": crontab(hour=3, minute=0)},
}
