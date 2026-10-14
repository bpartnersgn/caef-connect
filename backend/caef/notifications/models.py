"""Notifications dans l'application (NOT-01) ; courriel et SMS prévus comme canaux activables."""

from django.conf import settings
from django.db import models

from caef.commun.models import ModeleMetier


class Canal(models.TextChoices):
    APPLICATION = "application", "Application"
    COURRIEL = "courriel", "Courriel"
    SMS = "sms", "SMS"


class Notification(ModeleMetier):
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="notifications")
    type_evenement = models.CharField(max_length=60)
    objet_type = models.CharField(max_length=60, blank=True, default="")
    objet_id = models.UUIDField(null=True, blank=True)
    message = models.CharField(max_length=300)  # sans donnée sensible
    canal = models.CharField(max_length=12, choices=Canal.choices, default=Canal.APPLICATION)
    lue_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notification"
        ordering = ["-cree_le"]
