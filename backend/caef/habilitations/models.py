"""Rôles, permissions, affectations, intérims et modules activés par centre (module habilitations)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.commun.models import ModeleAjoutSeul, ModeleMetier


class Role(models.Model):
    code = models.CharField(max_length=6, primary_key=True)
    libelle = models.CharField(max_length=120)
    titre_organigramme = models.CharField(max_length=120)
    actif = models.BooleanField(default=True)
    double_auth = models.CharField(max_length=12, default="non")  # obligatoire, recommandee, non
    hors_ligne = models.BooleanField(default=False)

    class Meta:
        db_table = "role"
        ordering = ["code"]

    def __str__(self):
        return self.titre_organigramme


class Permission(models.Model):
    """Une ligne par cellule de la Matrice (rôle, objet, action, périmètre), alimentée depuis
    matrice.yaml à chaque migration ; jamais saisie à la main."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    objet = models.CharField(max_length=60)
    action = models.CharField(max_length=1)
    perimetre = models.CharField(max_length=2)
    condition = models.CharField(max_length=20, blank=True, default="")  # interim, a_defaut_cpt
    module = models.CharField(max_length=30, default="socle")

    class Meta:
        db_table = "permission"
        ordering = ["objet", "role_id", "action"]
        constraints = [models.UniqueConstraint(fields=["role", "objet", "action"], name="permission_unique")]


class Affectation(ModeleMetier):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="affectations")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="affectations")
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="affectations")
    national = models.BooleanField(default=False)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    motif = models.TextField()

    class Meta:
        db_table = "affectation"
        constraints = [
            models.CheckConstraint(condition=Q(national=True) | Q(centre__isnull=False),
                                   name="affectation_centre_sauf_national"),
            models.CheckConstraint(condition=Q(date_fin__isnull=True) | Q(date_fin__gte=models.F("date_debut")),
                                   name="affectation_dates_coherentes"),
        ]


class HabilitationExceptionnelle(ModeleMetier):
    """Habilitation nominative datée sur un objet précis, 30 jours au plus (Matrice § 4 règle 2)."""

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="habilitations")
    objet_type = models.CharField(max_length=60)
    objet_id = models.UUIDField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    demande_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    accorde_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    motif = models.TextField()

    class Meta:
        db_table = "habilitation_exceptionnelle"
        constraints = [
            models.CheckConstraint(condition=Q(date_fin__gte=models.F("date_debut")),
                                   name="habilitation_dates_coherentes"),
        ]


class InterimResponsable(ModeleMetier):
    """Intérim du RC au profit du RA (USR-09, RG-ADM-13 à RG-ADM-16)."""

    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="interims")
    responsable_remplace = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    adjoint = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="interims")
    date_debut = models.DateField()
    date_fin = models.DateField()
    motif = models.TextField()
    declare_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    interrompu_le = models.DateField(null=True, blank=True)
    motif_interruption = models.TextField(blank=True, default="")

    class Meta:
        db_table = "interim_responsable"
        ordering = ["-date_debut"]
        constraints = [
            models.CheckConstraint(condition=Q(date_fin__gte=models.F("date_debut")), name="interim_dates_coherentes"),
        ]

    def fin_effective(self):
        if self.interrompu_le and self.interrompu_le < self.date_fin:
            return self.interrompu_le
        return self.date_fin

    def statut(self, jour):
        if self.interrompu_le and self.interrompu_le <= jour:
            return "interrompu"
        if jour < self.date_debut:
            return "planifie"
        if jour > self.date_fin:
            return "termine"
        return "en_cours"


class ModuleOptionnel(models.TextChoices):
    BOUTIQUE = "boutique", "Boutique et salle d'exposition"
    SALLE_EXPOSITION = "salle_exposition", "Salle d'exposition"
    SCOLARITE_PAIEMENTS = "scolarite_paiements", "Scolarité et paiements"
    RSE_CENTRE = "rse_centre", "Volet RSE du centre"
    CRECHE = "creche", "Crèche (à venir)"
    INSERTION = "insertion", "Insertion (à venir)"
    ENTREPRENEURIAT = "entrepreneuriat", "Entrepreneuriat (à venir)"
    MATERIELS = "materiels", "Matériels et équipements (à venir)"


class StatutModule(models.TextChoices):
    ACTIF = "actif", "Activé"
    INACTIF = "inactif", "Désactivé"


class ModuleCentre(ModeleAjoutSeul):
    """Activation d'un module optionnel pour un centre, en ajout seul (ADM-08, RG-ADM-17 à 20).

    Une ligne ne compte qu'une fois validée par la DG ; le statut en vigueur est la ligne
    validée de date d'effet la plus récente.
    """

    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="modules")
    module = models.CharField(max_length=30, choices=ModuleOptionnel.choices)
    statut = models.CharField(max_length=8, choices=StatutModule.choices)
    date_effet = models.DateField()
    decision_reference = models.CharField(max_length=50)
    decision_date = models.DateField()
    motif = models.TextField()
    saisi_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "module_centre"
        ordering = ["-date_effet", "-cree_le"]
        constraints = [
            models.UniqueConstraint(fields=["centre", "module", "date_effet"], condition=Q(valide_par__isnull=False),
                                    name="module_centre_unique_par_date"),
            models.CheckConstraint(condition=Q(valide_par__isnull=True) | ~Q(valide_par=models.F("saisi_par")),
                                   name="module_centre_valideur_distinct"),
        ]
