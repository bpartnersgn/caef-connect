"""Programmes, propositions, validations, conventions, engagements et contributions
(Modèle § 5, SFD § 7). Promis, signé, reçu et exécuté restent quatre choses distinctes."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.commun.champs import DEVISES, Montant
from caef.commun.models import ModeleMetier


class StatutProgramme(models.TextChoices):
    PREVU = "prevu", "Prévu"
    EN_COURS = "en_cours", "En cours"
    CLOTURE = "cloture", "Clôturé"


class Programme(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    intitule = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    centres = models.ManyToManyField("referentiels.Centre", related_name="programmes", db_table="programme_centre")
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=10, choices=StatutProgramme.choices, default=StatutProgramme.PREVU)

    class Meta:
        db_table = "programme"
        constraints = [
            models.CheckConstraint(condition=Q(date_fin__gte=models.F("date_debut")), name="programme_dates_coherentes"),
        ]

    def __str__(self):
        return self.intitule


class StatutProposition(models.TextChoices):
    BROUILLON = "brouillon", "Brouillon"
    EN_VALIDATION = "en_validation", "En validation"
    VALIDEE = "validee", "Validée"
    REJETEE = "rejetee", "Rejetée"
    SOUMISE = "soumise", "Soumise"
    ACCEPTEE = "acceptee", "Acceptée"
    REFUSEE = "refusee", "Refusée"
    SUSPENDUE = "suspendue", "Suspendue"


class Proposition(ModeleMetier):
    code = models.CharField(max_length=30)
    numero_version = models.PositiveIntegerField(default=1)
    opportunite = models.ForeignKey("partenaires.Opportunite", on_delete=models.PROTECT, related_name="propositions")
    partenaire = models.ForeignKey("partenaires.Partenaire", on_delete=models.PROTECT, related_name="propositions")
    programme = models.ForeignKey(Programme, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    centres_beneficiaires = models.ManyToManyField("referentiels.Centre", related_name="+",
                                                   db_table="proposition_centre")
    montant_sollicite = Montant()
    devise = models.CharField(max_length=3, choices=DEVISES, default="GNF")
    nature = models.JSONField(default=list)
    budget_previsionnel = models.TextField(blank=True, default="")
    resultats_attendus = models.TextField()
    calendrier = models.TextField()
    statut = models.CharField(max_length=14, choices=StatutProposition.choices, default=StatutProposition.BROUILLON)
    date_envoi = models.DateField(null=True, blank=True)
    date_reponse = models.DateField(null=True, blank=True)
    motif = models.ForeignKey("referentiels.ReferentielValeur", null=True, blank=True, on_delete=models.PROTECT,
                              related_name="+")
    commentaire = models.TextField(blank=True, default="")
    version_suivante = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="version_precedente")

    class Meta:
        db_table = "proposition"
        constraints = [
            models.UniqueConstraint(fields=["code", "numero_version"], name="proposition_version_unique"),
            models.CheckConstraint(condition=Q(montant_sollicite__gt=0), name="proposition_montant_positif"),
            models.CheckConstraint(condition=~Q(statut="soumise") | Q(date_envoi__isnull=False),
                                   name="proposition_soumise_date_envoi"),
        ]


class DecisionValidation(models.TextChoices):
    FAVORABLE = "favorable", "Favorable"
    DEFAVORABLE = "defavorable", "Défavorable"
    VALIDE = "valide", "Validé"
    REJETE = "rejete", "Rejeté"


class Validation(ModeleMetier):
    """Circuit de validation paramétrable (H5) : une ligne par étape et par objet."""

    objet_type = models.CharField(max_length=60)
    objet_id = models.UUIDField()
    etape = models.PositiveSmallIntegerField()
    valideur_attendu_role = models.ForeignKey("habilitations.Role", on_delete=models.PROTECT, related_name="+")
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="+")
    decision = models.CharField(max_length=12, choices=DecisionValidation.choices, blank=True, default="")
    decide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    decide_le = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(blank=True, default="")

    class Meta:
        db_table = "validation"
        ordering = ["objet_id", "etape"]


class StatutConvention(models.TextChoices):
    EN_PREPARATION = "en_preparation", "En préparation"
    SIGNEE = "signee", "Signée"
    EN_EXECUTION = "en_execution", "En exécution"
    CLOTUREE = "cloturee", "Clôturée"
    RESILIEE = "resiliee", "Résiliée"


class Convention(ModeleMetier):
    reference = models.CharField(max_length=60, unique=True)
    partenaire = models.ForeignKey("partenaires.Partenaire", on_delete=models.PROTECT, related_name="conventions")
    proposition = models.OneToOneField(Proposition, null=True, blank=True, on_delete=models.PROTECT,
                                       related_name="convention")
    programme = models.ForeignKey(Programme, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    centres = models.ManyToManyField("referentiels.Centre", related_name="conventions", db_table="convention_centre")
    montant_accorde = Montant(null=True, blank=True)
    devise = models.CharField(max_length=3, choices=DEVISES, default="GNF")
    date_signature = models.DateField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    signataires = models.TextField(blank=True, default="")
    document_signe = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                       related_name="+")
    statut = models.CharField(max_length=14, choices=StatutConvention.choices, default=StatutConvention.EN_PREPARATION)

    class Meta:
        db_table = "convention"
        constraints = [
            # RG-CNV-05 : signée seulement avec date, signataires et document signé.
            models.CheckConstraint(
                condition=Q(statut="en_preparation") | (Q(date_signature__isnull=False) & Q(document_signe__isnull=False) & ~Q(signataires="")),
                name="convention_signature_complete"),
        ]


class PartieEngagement(models.TextChoices):
    PARTENAIRE = "partenaire", "Partenaire"
    CAEF = "caef", "CAEF"


class EtatEngagement(models.TextChoices):
    A_REALISER = "a_realiser", "À réaliser"
    EN_COURS = "en_cours", "En cours"
    EN_RETARD = "en_retard", "En retard"
    REALISE = "realise", "Réalisé"
    VALIDE = "valide", "Validé"
    ABANDONNE = "abandonne", "Abandonné"


class Engagement(ModeleMetier):
    convention = models.ForeignKey(Convention, on_delete=models.PROTECT, related_name="engagements")
    partie = models.CharField(max_length=10, choices=PartieEngagement.choices)
    description = models.TextField()
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="+")
    echeance = models.DateField()
    etat = models.CharField(max_length=10, choices=EtatEngagement.choices, default=EtatEngagement.A_REALISER)
    justificatif = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="+")
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    motif_abandon = models.TextField(blank=True, default="")

    class Meta:
        db_table = "engagement"
        ordering = ["echeance"]
        constraints = [
            models.CheckConstraint(condition=~Q(etat__in=["realise", "valide"]) | Q(justificatif__isnull=False),
                                   name="engagement_realise_justifie"),
        ]


NATURES_CONTRIBUTION = [
    ("financiere", "Contribution financière"),
    ("don_nature", "Don en nature"),
    ("equipements", "Mise à disposition d'équipements"),
    ("prestation", "Prestation de service"),
    ("formation_financee", "Formation financée"),
    ("competences", "Mise à disposition de compétences"),
    ("logistique", "Appui logistique"),
    ("autre", "Autre contribution validée"),
]


class StatutContribution(models.TextChoices):
    PROMISE = "promise", "Promise"
    RECUE = "recue", "Reçue"
    VALIDEE = "validee", "Validée"
    ANNULEE = "annulee", "Annulée"


class Contribution(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    convention = models.ForeignKey(Convention, on_delete=models.PROTECT, related_name="contributions")
    partenaire = models.ForeignKey("partenaires.Partenaire", on_delete=models.PROTECT, related_name="contributions")
    programme = models.ForeignKey(Programme, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    centre_beneficiaire = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT,
                                            related_name="contributions")
    nature = models.CharField(max_length=20, choices=NATURES_CONTRIBUTION)
    financiere = models.BooleanField(editable=False)
    devise = models.CharField(max_length=3, choices=DEVISES, default="GNF")
    montant_promis = Montant(null=True, blank=True)
    date_prevue = models.DateField(null=True, blank=True)
    montant_recu = Montant(null=True, blank=True)
    date_reception = models.DateField(null=True, blank=True)
    devise_origine = models.CharField(max_length=3, blank=True, default="")
    montant_origine = Montant(null=True, blank=True)
    taux_conversion = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    source_taux = models.CharField(max_length=120, blank=True, default="")
    description_bien = models.TextField(blank=True, default="")
    quantite = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    valeur_estimee = Montant(null=True, blank=True)
    methode_valorisation = models.CharField(max_length=30, blank=True, default="")
    justificatifs = models.ManyToManyField("documents.Document", blank=True, related_name="+",
                                           db_table="contribution_justificatif")
    reference_comptable = models.CharField(max_length=60, blank=True, default="")
    reference_piece_comptable = models.CharField(max_length=60, blank=True, default="")
    date_encaissement_constatee = models.DateField(null=True, blank=True)
    rapproche_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                      related_name="+")
    rapproche_le = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=8, choices=StatutContribution.choices, default=StatutContribution.PROMISE)
    saisi_reception_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                            on_delete=models.PROTECT, related_name="+")
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.TextField(blank=True, default="")

    class Meta:
        db_table = "contribution"
        constraints = [
            # Modèle § 7.1 : « reçue » impossible sans date de réception ni montant ou quantité.
            models.CheckConstraint(
                condition=~Q(statut__in=["recue", "validee"]) | (Q(date_reception__isnull=False) & (Q(montant_recu__isnull=False) | Q(quantite__isnull=False))),
                name="contribution_recue_complete"),
            # RG-CTR-04 : la personne qui saisit la réception ne la valide pas.
            models.CheckConstraint(condition=Q(valide_par__isnull=True) | ~Q(valide_par=models.F("saisi_reception_par")),
                                   name="contribution_separation_des_taches"),
            models.CheckConstraint(condition=Q(valeur_estimee__isnull=True) | ~Q(methode_valorisation=""),
                                   name="contribution_methode_si_valeur"),
        ]

    def save(self, *args, **kwargs):
        self.financiere = self.nature == "financiere"
        super().save(*args, **kwargs)
