"""Journal d'audit en ajout seul (SEC-04, Modèle § 3)."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from caef.commun.exceptions import RegleMetier
from caef.commun.models import uuid7


class ActionJournal(models.TextChoices):
    CREATION = "creation", "Création"
    MODIFICATION = "modification", "Modification"
    STATUT = "statut", "Changement de statut"
    VALIDATION = "validation", "Validation"
    EXPORT = "export", "Export"
    CONNEXION = "connexion", "Connexion"
    ECHEC_CONNEXION = "echec_connexion", "Échec de connexion"
    ACCES_REFUSE = "acces_refuse", "Accès refusé"
    CONSULTATION_SENSIBLE = "consultation_sensible", "Consultation sensible"
    FUSION = "fusion", "Fusion"
    DROITS = "droits", "Droits"


class JournalAudit(models.Model):
    """Aucune mise à jour ni suppression, y compris par l'administrateur : un déclencheur
    PostgreSQL le garantit (migration 0002)."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    horodatage = models.DateTimeField(default=timezone.now, db_index=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    adresse_ip = models.CharField(max_length=45, blank=True, default="")
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    action = models.CharField(max_length=24, choices=ActionJournal.choices, db_index=True)
    objet_type = models.CharField(max_length=60, blank=True, default="", db_index=True)
    objet_id = models.UUIDField(null=True, blank=True, db_index=True)
    avant = models.JSONField(null=True, blank=True)
    apres = models.JSONField(null=True, blank=True)
    motif = models.TextField(blank=True, default="")
    nb_lignes = models.PositiveIntegerField(null=True, blank=True)
    appareil_id = models.UUIDField(null=True, blank=True)
    interim = models.BooleanField(default=False)  # validation faite par un RA en intérim (RG-ADM-16)

    class Meta:
        db_table = "journal_audit"
        ordering = ["-horodatage"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise RegleMetier("Le journal d'audit n'est jamais modifiable (SEC-04).")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RegleMetier("Le journal d'audit n'est jamais modifiable (SEC-04).")
