"""Services payants, tarifs datés, échéances et exonérations (Modèle § 9, SFD § 12, PAY-01 à PAY-03)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.boutique.models import gnf_entier
from caef.commun.champs import Montant
from caef.commun.models import ModeleMetier


class NatureService(models.TextChoices):
    INSCRIPTION = "inscription", "Frais d'inscription"
    SCOLARITE = "scolarite", "Scolarité"
    EXAMEN = "examen", "Examen"
    ATTESTATION = "attestation", "Attestation"
    SERVICE_ASSOCIE = "service_associe", "Service associé"


class ServicePayant(ModeleMetier):
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="services_payants")
    code = models.CharField(max_length=30)
    libelle = models.CharField(max_length=150)
    nature = models.CharField(max_length=16, choices=NatureService.choices)
    formation = models.ForeignKey("formations.Formation", null=True, blank=True, on_delete=models.PROTECT,
                                  related_name="services_payants")
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = "service_payant"
        constraints = [
            models.UniqueConstraint(fields=["centre", "code"], name="service_code_unique_par_centre"),
            models.CheckConstraint(condition=~Q(nature="scolarite") | Q(formation__isnull=False),
                                   name="service_scolarite_formation"),
        ]

    def __str__(self):
        return self.libelle


class TarifService(ModeleMetier):
    service_payant = models.ForeignKey(ServicePayant, on_delete=models.PROTECT, related_name="tarifs")
    montant = Montant()
    nombre_versements = models.PositiveSmallIntegerField(default=1)
    calendrier = models.JSONField(default=list, blank=True)  # délai en jours de chaque versement après l'inscription
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    decision_reference = models.CharField(max_length=100)

    class Meta:
        db_table = "tarif_service"
        ordering = ["-date_debut"]
        constraints = [
            models.CheckConstraint(condition=Q(montant__gt=0) & gnf_entier("montant"), name="tarif_gnf_entier_positif"),
            models.CheckConstraint(condition=Q(nombre_versements__gte=1), name="tarif_versements_positif"),
            models.UniqueConstraint(fields=["service_payant"], condition=Q(date_fin__isnull=True),
                                    name="un_tarif_en_vigueur"),
        ]


class StatutEcheance(models.TextChoices):
    A_PAYER = "a_payer", "À payer"
    PARTIELLEMENT_PAYEE = "partiellement_payee", "Partiellement payée"
    PAYEE = "payee", "Payée"
    EXONEREE = "exoneree", "Exonérée"
    ANNULEE = "annulee", "Annulée"


class Echeance(ModeleMetier):
    beneficiaire = models.ForeignKey("beneficiaires.Beneficiaire", on_delete=models.PROTECT, related_name="echeances")
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="echeances")
    inscription = models.ForeignKey("formations.Inscription", null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="echeances")
    service_payant = models.ForeignKey(ServicePayant, on_delete=models.PROTECT, related_name="echeances")
    tarif_service = models.ForeignKey(TarifService, on_delete=models.PROTECT, related_name="echeances")
    rang = models.PositiveSmallIntegerField(default=1)
    montant = Montant()
    date_limite = models.DateField()
    reference_paiement = models.CharField(max_length=20, unique=True)
    # Calculés à partir des exonérations validées et des affectations de paiements confirmés ; jamais saisis.
    montant_exonere = Montant(default=0)
    montant_paye = Montant(default=0)
    restant_du = Montant()
    statut = models.CharField(max_length=20, choices=StatutEcheance.choices, default=StatutEcheance.A_PAYER)

    class Meta:
        db_table = "echeance"
        ordering = ["date_limite", "rang"]
        constraints = [
            models.CheckConstraint(condition=Q(montant__gt=0) & gnf_entier("montant"), name="echeance_gnf_entier"),
        ]


class TypeExoneration(models.TextChoices):
    BOURSE = "bourse", "Bourse"
    REDUCTION = "reduction", "Réduction motivée"
    PARTENAIRE = "partenaire", "Prise en charge partenaire"
    PROGRAMME = "programme", "Prise en charge programme"


class StatutExoneration(models.TextChoices):
    PROPOSEE = "proposee", "Proposée"
    VALIDEE = "validee", "Validée"
    REFUSEE = "refusee", "Refusée"


class Exoneration(ModeleMetier):
    echeance = models.ForeignKey(Echeance, on_delete=models.PROTECT, related_name="exonerations")
    type = models.CharField(max_length=12, choices=TypeExoneration.choices)
    montant = Montant()
    motif = models.TextField()
    partenaire = models.ForeignKey("partenaires.Partenaire", null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    programme = models.ForeignKey("conventions.Programme", null=True, blank=True, on_delete=models.PROTECT,
                                  related_name="+")
    piece_justificative = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="+")
    statut = models.CharField(max_length=10, choices=StatutExoneration.choices, default=StatutExoneration.PROPOSEE)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "exoneration"
        constraints = [
            models.CheckConstraint(condition=Q(montant__gt=0) & gnf_entier("montant"), name="exoneration_gnf_entier"),
            models.CheckConstraint(condition=Q(valide_par__isnull=True) | ~Q(valide_par=models.F("cree_par")),
                                   name="exoneration_valideur_distinct"),
        ]
