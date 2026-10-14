"""Pièces jointes : métadonnées en base, fichiers dans le stockage d'objets (DOC-01, DAT § 5.3)."""

from django.db import models

from caef.commun.models import ModeleMetier


class Confidentialite(models.TextChoices):
    INTERNE = "interne", "Interne"
    NOMINATIF = "nominatif", "Nominatif"
    RESTREINT = "restreint", "Restreint"


class Document(ModeleMetier):
    objet_type = models.CharField(max_length=60)
    objet_id = models.UUIDField()
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="documents")
    type_document = models.CharField(max_length=60)
    nom_fichier = models.CharField(max_length=255)
    format = models.CharField(max_length=10)
    taille_octets = models.PositiveIntegerField()
    empreinte = models.CharField(max_length=64)
    chemin_stockage = models.CharField(max_length=500)  # jamais exposé (R)
    confidentialite = models.CharField(max_length=10, choices=Confidentialite.choices)
    version_document = models.PositiveIntegerField(default=1)
    remplace = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="versions")

    class Meta:
        db_table = "document"
        ordering = ["-cree_le"]
        indexes = [models.Index(fields=["objet_type", "objet_id"])]
