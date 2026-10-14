"""Centres, zones, valeurs de référence et périodes (Modèle § 3, module referentiels)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.commun.models import ModeleMetier


class NiveauZone(models.TextChoices):
    REGION = "region", "Région"
    PREFECTURE = "prefecture", "Préfecture"
    COMMUNE = "commune", "Commune"
    QUARTIER = "quartier", "Quartier"


class ZoneTerritoriale(ModeleMetier):
    niveau = models.CharField(max_length=12, choices=NiveauZone.choices)
    nom = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="enfants")

    class Meta:
        db_table = "zone_territoriale"
        constraints = [
            models.CheckConstraint(
                condition=Q(niveau="region") | Q(parent__isnull=False),
                name="zone_parent_obligatoire_sauf_region",
            ),
        ]

    def __str__(self):
        return self.nom


class StatutCentre(models.TextChoices):
    ACTIF = "actif", "Actif"
    INACTIF = "inactif", "Inactif"


class Centre(ModeleMetier):
    code = models.CharField(max_length=3, unique=True)
    nom = models.CharField(max_length=150, unique=True)
    zone_territoriale = models.ForeignKey(ZoneTerritoriale, on_delete=models.PROTECT, related_name="centres")
    adresse = models.CharField(max_length=255, blank=True, default="")
    telephone = models.CharField(max_length=20, blank=True, default="")
    courriel = models.EmailField(blank=True, default="")
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="centres_diriges"
    )
    date_ouverture = models.DateField(null=True, blank=True)
    capacite_indicative = models.PositiveIntegerField(null=True, blank=True)
    statut = models.CharField(max_length=8, choices=StatutCentre.choices, default=StatutCentre.ACTIF)
    # Centre fictif de formation ou de recette : jamais compté dans les indicateurs (Référentiel § 2.2).
    fictif = models.BooleanField(default=False)

    class Meta:
        db_table = "centre"
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(condition=Q(capacite_indicative__isnull=True) | Q(capacite_indicative__gt=0),
                                   name="centre_capacite_positive"),
        ]

    def __str__(self):
        return f"{self.nom} ({self.code})"


class ReferentielValeur(ModeleMetier):
    referentiel = models.CharField(max_length=60)
    code = models.CharField(max_length=60)
    libelle = models.CharField(max_length=200)
    ordre = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)
    date_effet = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "referentiel_valeur"
        ordering = ["referentiel", "ordre", "libelle"]
        constraints = [models.UniqueConstraint(fields=["referentiel", "code"], name="referentiel_code_unique")]

    def __str__(self):
        return self.libelle


class TypePeriode(models.TextChoices):
    MOIS = "mois", "Mois"
    TRIMESTRE = "trimestre", "Trimestre"
    ANNEE = "annee", "Année"
    CAMPAGNE = "campagne", "Campagne"


class StatutPeriode(models.TextChoices):
    OUVERTE = "ouverte", "Ouverte"
    CLOTUREE = "cloturee", "Clôturée"
    ROUVERTE = "rouverte", "Rouverte"


class Periode(ModeleMetier):
    type = models.CharField(max_length=10, choices=TypePeriode.choices)
    libelle = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=10, choices=StatutPeriode.choices, default=StatutPeriode.OUVERTE)

    class Meta:
        db_table = "periode"
        ordering = ["-date_debut"]
        constraints = [
            models.CheckConstraint(condition=Q(date_fin__gte=models.F("date_debut")), name="periode_dates_coherentes"),
        ]

    def __str__(self):
        return self.libelle
