from django.apps import AppConfig
from django.db.models.signals import post_migrate


class HabilitationsConfig(AppConfig):
    name = "caef.habilitations"
    label = "habilitations"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from .synchronisation_matrice import synchroniser_matrice

        post_migrate.connect(synchroniser_matrice, sender=self)
