"""Pilotage : clôture mensuelle et rapprochement (SRC-02), indicateurs calculés la nuit dans le
schéma de pilotage (RG-TDB-01), fiches d'indicateurs et rapports."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.commun.champs import DEVISES, Montant
from caef.commun.models import ModeleMetier


class StatutCloture(models.TextChoices):
    A_FAIRE = "a_faire", "À faire"
    VERIFIEE = "verifiee", "Vérifiée"
    VALIDEE = "validee", "Validée"
    VALIDEE_AVEC_ECART = "validee_avec_ecart", "Validée avec écart"


class ClotureMensuelle(ModeleMetier):
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="clotures_mensuelles")
    mois = models.CharField(max_length=7)  # AAAA-MM
    statut = models.CharField(max_length=20, choices=StatutCloture.choices, default=StatutCloture.A_FAIRE)
    totaux = models.JSONField(default=dict)  # {flux: {devise: montant}}, calculés, jamais saisis
    ecart = models.JSONField(default=dict)  # {devise: écart}
    motif_ecart = models.TextField(blank=True, default="")
    verifiee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="+")
    verifiee_le = models.DateTimeField(null=True, blank=True)
    validee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="+")
    validee_le = models.DateTimeField(null=True, blank=True)
    verrouillee = models.BooleanField(default=False)
    motif_renvoi = models.TextField(blank=True, default="")
    derogation_appareils = models.JSONField(default=list, blank=True)  # appareils non synchronisés, décision RC
    cloture_corrigee = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                                         related_name="regularisations")

    class Meta:
        db_table = "cloture_mensuelle"
        ordering = ["-mois"]
        constraints = [
            models.UniqueConstraint(fields=["centre", "mois"], name="cloture_unique_par_mois"),
            models.CheckConstraint(condition=Q(validee_par__isnull=True) | ~Q(validee_par=models.F("verifiee_par")),
                                   name="cloture_separation_des_taches"),
            models.CheckConstraint(condition=Q(mois__regex=r"^\d{4}-(0[1-9]|1[0-2])$"), name="cloture_format_mois"),
        ]


class Flux(models.TextChoices):
    VENTES = "ventes", "Ventes"
    CAISSES = "caisses", "Encaissements des caisses"
    PAIEMENTS_SCOLARITE = "paiements_scolarite", "Paiements de scolarité et services"
    REVERSEMENTS = "reversements", "Reversements"
    CONTRIBUTIONS = "contributions_financieres_recues", "Contributions financières reçues"


class LigneRapprochement(models.Model):
    cloture_mensuelle = models.ForeignKey(ClotureMensuelle, on_delete=models.PROTECT, related_name="lignes")
    flux = models.CharField(max_length=40, choices=Flux.choices)
    devise = models.CharField(max_length=3, choices=DEVISES)
    module_non_active = models.BooleanField(default=False)  # « Module non activé », jamais 0 (RG-ADM-20)
    montant_outil = Montant(null=True, blank=True)
    montant_piece = Montant(null=True, blank=True)
    ecart = Montant(null=True, blank=True)
    motif = models.TextField(blank=True, default="")
    piece_justificative = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="+")

    class Meta:
        db_table = "ligne_rapprochement"
        constraints = [
            models.UniqueConstraint(fields=["cloture_mensuelle", "flux", "devise"], name="ligne_rapprochement_unique"),
        ]


class StatutFiche(models.TextChoices):
    BROUILLON = "brouillon", "Brouillon"
    PROPOSEE = "proposee", "Proposée"
    VALIDEE = "validee", "Validée"
    REVISEE = "revisee", "Révisée"
    RETIREE = "retiree", "Retirée"


class FicheIndicateur(models.Model):
    """Statut de la fiche de chaque indicateur (H10, TDB-01) : seul « validée » s'affiche au national."""

    code = models.CharField(max_length=10, primary_key=True)
    libelle = models.CharField(max_length=200)
    version = models.PositiveSmallIntegerField(default=1)
    statut = models.CharField(max_length=10, choices=StatutFiche.choices, default=StatutFiche.PROPOSEE)
    niveau_validation = models.CharField(max_length=20, default="verifie")
    module = models.CharField(max_length=30, default="socle")

    class Meta:
        db_table = "fiche_indicateur"
        ordering = ["code"]


class ValeurIndicateur(models.Model):
    """Table de synthèse du schéma de pilotage, recalculée chaque nuit, figée à la clôture
    d'une période (RG-TDB-01, RG-TDB-04)."""

    indicateur = models.CharField(max_length=10, db_index=True)
    version_fiche = models.PositiveSmallIntegerField(default=1)
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="+")  # nul = national
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    ventilation = models.CharField(max_length=60, blank=True, default="")  # ex. devise:USD, nature:financiere
    valeur = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)  # nul = non renseigné
    valeur_declarative = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    numerateur = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    denominateur = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    nb_non_renseignes = models.PositiveIntegerField(default=0)
    module_non_active = models.BooleanField(default=False)
    niveau = models.CharField(max_length=12, default="verifie")  # verifie, declaratif
    fiabilite_faible = models.BooleanField(default=False)
    details = models.JSONField(default=dict, blank=True)
    calcule_le = models.DateTimeField()
    fige = models.BooleanField(default=False)

    class Meta:
        db_table = 'pilotage"."valeur_indicateur'
        constraints = [
            models.UniqueConstraint(fields=["indicateur", "centre", "periode_debut", "periode_fin", "ventilation"],
                                    name="valeur_indicateur_unique", nulls_distinct=False),
        ]


class TypeRapport(models.TextChoices):
    SESSION = "R-01", "Rapport de session"
    CENTRE = "R-02", "Rapport périodique de centre"
    NATIONAL = "R-03", "Rapport national"
    PARTENAIRE = "R-04", "Rapport partenaire"


class StatutRapport(models.TextChoices):
    BROUILLON = "brouillon", "Brouillon"
    VALIDE = "valide", "Validé"
    TRANSMIS = "transmis", "Transmis"


class Rapport(ModeleMetier):
    type = models.CharField(max_length=4, choices=TypeRapport.choices)
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="rapports")
    convention = models.ForeignKey("conventions.Convention", null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="rapports")
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    date_limite = models.DateField(null=True, blank=True)
    contenu = models.JSONField(default=dict)
    commentaire = models.TextField(blank=True, default="")
    statut = models.CharField(max_length=10, choices=StatutRapport.choices, default=StatutRapport.BROUILLON)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)
    transmis_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rapport"
        ordering = ["-periode_fin"]
