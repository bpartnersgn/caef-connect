from django.apps import AppConfig


class SynchronisationConfig(AppConfig):
    name = "caef.synchronisation"
    label = "synchronisation"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from .signaux import connecter

        connecter()
