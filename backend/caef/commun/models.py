"""Socle commun des entités métier (Modèle de données § 1).

Chaque entité métier porte les colonnes communes : identifiant UUID, auteurs et dates,
archivage logique, verrou optimiste, clé d'idempotence, origine de la saisie et appareil.
Aucune suppression physique n'est possible (RG-GEN-03).
"""

import os
import time
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .exceptions import RegleMetier


def uuid7() -> uuid.UUID:
    """UUID version 7, ordonné dans le temps (RFC 9562)."""
    ms = time.time_ns() // 1_000_000
    aleatoire = int.from_bytes(os.urandom(10), "big")
    valeur = (ms & ((1 << 48) - 1)) << 80
    valeur |= 0x7 << 76
    valeur |= ((aleatoire >> 62) & 0xFFF) << 64
    valeur |= 0b10 << 62
    valeur |= aleatoire & ((1 << 62) - 1)
    return uuid.UUID(int=valeur)


class OrigineSaisie(models.TextChoices):
    EN_LIGNE = "en_ligne", "En ligne"
    HORS_LIGNE = "hors_ligne", "Hors ligne"
    IMPORT = "import", "Import"


class Qualite(models.TextChoices):
    """Indicateur de qualité d'une donnée reprise (MIG-01, SRC-03)."""

    FIABLE = "fiable", "Fiable"
    A_VERIFIER = "a_verifier", "À vérifier"


class SuppressionInterditeQuerySet(models.QuerySet):
    def delete(self):
        raise RegleMetier("La suppression physique est interdite : archivez ou annulez l'objet (RG-GEN-03).")


class GestionnaireMetier(models.Manager.from_queryset(SuppressionInterditeQuerySet)):
    pass


class ModeleMetier(models.Model):
    """Colonnes communes à toutes les entités métier."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    cree_le = models.DateTimeField(default=timezone.now, editable=False)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    modifie_le = models.DateTimeField(null=True, blank=True)
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    archive = models.BooleanField(default=False)
    archive_le = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    cle_idempotence = models.CharField(max_length=80, null=True, blank=True)
    origine_saisie = models.CharField(max_length=12, choices=OrigineSaisie.choices, default=OrigineSaisie.EN_LIGNE)
    # Identifiant de l'appareil enrôlé (synchronisation.Appareil), sans clé étrangère pour
    # éviter une dépendance circulaire entre modules (voir DECISIONS.md).
    appareil_id = models.UUIDField(null=True, blank=True)
    horodatage_appareil = models.DateTimeField(null=True, blank=True)

    objects = GestionnaireMetier()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise RegleMetier("La suppression physique est interdite : archivez ou annulez l'objet (RG-GEN-03).")

    def marquer_modifie(self, acteur):
        self.modifie_le = timezone.now()
        self.modifie_par = acteur
        self.version = (self.version or 0) + 1


class ModeleAjoutSeul(ModeleMetier):
    """Entité en ajout seul : ni modification ni suppression (mouvements, paiements, journal…)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding and not getattr(self, "_mise_a_jour_autorisee", False):
            raise RegleMetier(
                "Cet enregistrement est en ajout seul : toute correction passe par une contre-écriture."
            )
        super().save(*args, **kwargs)


class Compteur(models.Model):
    """Compteur technique pour les codes lisibles (BEN-CMR-2026-00042, ATT-…, références de paiement).

    Une ligne par clé (ex. « BEN-CMR-2026 ») ; l'incrément se fait sous verrou de ligne.
    """

    cle = models.CharField(max_length=60, primary_key=True)
    valeur = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "compteur_code"
