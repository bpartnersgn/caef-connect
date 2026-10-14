"""Appareils de terrain et opérations saisies hors ligne (Modèle § 8, OFF-01 à OFF-08)."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from caef.commun.models import ModeleMetier


class StatutAppareil(models.TextChoices):
    ACTIF = "actif", "Actif"
    REVOQUE = "revoque", "Révoqué"


class Appareil(ModeleMetier):
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="appareils")
    libelle = models.CharField(max_length=60)
    utilisateur_principal = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                              on_delete=models.PROTECT, related_name="+")
    point_de_vente = models.ForeignKey("boutique.PointDeVente", null=True, blank=True, on_delete=models.PROTECT,
                                       related_name="appareils")
    serie_recu = models.CharField(max_length=12, null=True, blank=True)
    dernier_numero_recu = models.PositiveIntegerField(default=0)
    enrole_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    enrole_le = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=8, choices=StatutAppareil.choices, default=StatutAppareil.ACTIF)
    revoque_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="+")
    revoque_le = models.DateTimeField(null=True, blank=True)
    motif_revocation = models.TextField(blank=True, default="")
    derniere_synchronisation = models.DateTimeField(null=True, blank=True)
    plus_ancienne_operation_en_attente = models.DateTimeField(null=True, blank=True)
    ecart_horloge_secondes = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "appareil"
        ordering = ["libelle"]
        constraints = [
            models.UniqueConstraint(fields=["point_de_vente", "serie_recu"], condition=Q(serie_recu__isnull=False),
                                    name="appareil_serie_unique_par_point_de_vente"),
            models.CheckConstraint(condition=Q(statut="actif") | (Q(revoque_par__isnull=False) & ~Q(motif_revocation="")),
                                   name="appareil_revocation_motivee"),
        ]

    def __str__(self):
        return self.libelle


class ResultatOperation(models.TextChoices):
    APPLIQUEE = "appliquee", "Appliquée"
    REJETEE = "rejetee", "Rejetée"
    EN_CONFLIT = "en_conflit", "En conflit"
    ECRITURE_TARDIVE = "ecriture_tardive", "Écriture tardive"


class OperationSynchronisation(models.Model):
    """Opération immuable venue d'un appareil ; son UUID, généré sur l'appareil, est la clé
    d'idempotence : une opération reçue deux fois n'est appliquée qu'une fois (OFF-03)."""

    id = models.UUIDField(primary_key=True, editable=False)
    appareil = models.ForeignKey(Appareil, on_delete=models.PROTECT, related_name="operations")
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    type_operation = models.CharField(max_length=60)
    objet_type = models.CharField(max_length=60)
    objet_id = models.UUIDField(null=True, blank=True)
    donnees = models.JSONField()
    version_base = models.PositiveIntegerField(null=True, blank=True)
    horodatage_appareil = models.DateTimeField()
    recu_le = models.DateTimeField(default=timezone.now)
    resultat = models.CharField(max_length=20, choices=ResultatOperation.choices)
    motif_rejet = models.TextField(blank=True, default="")
    horloge_a_verifier = models.BooleanField(default=False)
    reponse = models.JSONField(null=True, blank=True)  # codes définitifs attribués, etc.
    regularisee = models.BooleanField(default=False)

    class Meta:
        db_table = "operation_synchronisation"
        ordering = ["recu_le"]
        indexes = [models.Index(fields=["appareil", "resultat"])]


class NatureChangement(models.TextChoices):
    CREATION = "creation", "Création"
    MODIFICATION = "modification", "Modification"
    ARCHIVAGE = "archivage", "Archivage"
    RETRAIT_DROIT = "retrait_droit", "Retrait de droit"


class JournalChangements(models.Model):
    """Journal des changements par centre, numéroté de façon croissante, en ajout seul ;
    les appareils le lisent par curseur."""

    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="+")
    numero = models.PositiveBigIntegerField()
    objet_type = models.CharField(max_length=60)
    objet_id = models.UUIDField()
    nature = models.CharField(max_length=14, choices=NatureChangement.choices)
    version = models.PositiveIntegerField(default=1)
    survenu_le = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "journal_changements"
        ordering = ["centre", "numero"]
        constraints = [models.UniqueConstraint(fields=["centre", "numero"], name="journal_changements_numero_unique")]


class StatutConflit(models.TextChoices):
    A_RESOUDRE = "a_resoudre", "À résoudre"
    GARDE_SERVEUR = "garde_serveur", "Valeur du serveur gardée"
    REMPLACE = "remplace", "Remplacée par la valeur de l'appareil"
    REGULARISE = "regularise", "Régularisée"


class ConflitSynchronisation(models.Model):
    """File « À résoudre » (E-OFF-02) : conflits de champ (RC ou RA) et écritures tardives (CPT)."""

    id = models.UUIDField(primary_key=True, default=None, editable=False)
    operation = models.ForeignKey(OperationSynchronisation, on_delete=models.PROTECT, related_name="conflits")
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="+")
    objet_type = models.CharField(max_length=60)
    objet_id = models.UUIDField(null=True, blank=True)
    champ = models.CharField(max_length=60, blank=True, default="")  # vide pour une écriture tardive
    valeur_serveur = models.TextField(blank=True, default="")
    valeur_appareil = models.TextField(blank=True, default="")
    statut = models.CharField(max_length=14, choices=StatutConflit.choices, default=StatutConflit.A_RESOUDRE)
    resolu_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    resolu_le = models.DateTimeField(null=True, blank=True)
    motif = models.TextField(blank=True, default="")
    cree_le = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "conflit_synchronisation"
        ordering = ["cree_le"]

    @property
    def ecriture_tardive(self):
        return self.operation.resultat == ResultatOperation.ECRITURE_TARDIVE

    def save(self, *args, **kwargs):
        if self.id is None:
            from caef.commun.models import uuid7

            self.id = uuid7()
        super().save(*args, **kwargs)
