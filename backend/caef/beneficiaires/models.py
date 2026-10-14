"""Bénéficiaires, candidatures, transferts et doublons (Modèle § 4, SFD § 4)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.commun.champs import TexteChiffre
from caef.commun.models import ModeleMetier, Qualite


class PrecisionNaissance(models.TextChoices):
    EXACTE = "exacte", "Date exacte"
    ANNEE = "annee", "Année"
    TRANCHE = "tranche", "Tranche d'âge"


class Sexe(models.TextChoices):
    F = "F", "Féminin"
    M = "M", "Masculin"


class ModeConsentement(models.TextChoices):
    ECRIT = "ecrit", "Écrit"
    ORAL_TEMOIN = "oral_temoin", "Oral devant témoin"


class StatutBeneficiaire(models.TextChoices):
    ACTIF = "actif", "Actif"
    INACTIF = "inactif", "Inactif"
    CLOTURE = "cloture", "Clôturé"
    ARCHIVE = "archive", "Archivé"
    FUSIONNE = "fusionne", "Fusionné"


class Beneficiaire(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=100)
    autres_noms = models.CharField(max_length=100, blank=True, default="")
    nom_normalise = models.CharField(max_length=220, db_index=True, editable=False)
    cle_phonetique = models.CharField(max_length=220, db_index=True, editable=False)
    date_naissance = models.DateField(null=True, blank=True)
    annee_naissance = models.PositiveSmallIntegerField(null=True, blank=True)
    tranche_age = models.CharField(max_length=20, blank=True, default="")
    precision_naissance = models.CharField(max_length=8, choices=PrecisionNaissance.choices)
    sexe = models.CharField(max_length=1, choices=Sexe.choices, default=Sexe.F)
    telephone = models.CharField(max_length=20, blank=True, default="", db_index=True)
    zone_residence = models.ForeignKey("referentiels.ZoneTerritoriale", on_delete=models.PROTECT, related_name="+")
    niveau_etudes = models.ForeignKey("referentiels.ReferentielValeur", null=True, blank=True,
                                      on_delete=models.PROTECT, related_name="+")
    situation_entree = models.ForeignKey("referentiels.ReferentielValeur", null=True, blank=True,
                                         on_delete=models.PROTECT, related_name="+")
    # Champs restreints (R), chiffrés au niveau applicatif, jamais sur un appareil (OFF-06).
    contact_urgence_nom = TexteChiffre(null=True, blank=True)
    contact_urgence_tel = TexteChiffre(null=True, blank=True)
    piece_identite_type = models.ForeignKey("referentiels.ReferentielValeur", null=True, blank=True,
                                            on_delete=models.PROTECT, related_name="+")
    piece_identite_numero = TexteChiffre(null=True, blank=True)
    centre_rattachement = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT,
                                            related_name="beneficiaires")
    consentement_date = models.DateField()
    consentement_mode = models.CharField(max_length=12, choices=ModeConsentement.choices)
    autorisation_image = models.BooleanField(default=False)
    statut = models.CharField(max_length=10, choices=StatutBeneficiaire.choices, default=StatutBeneficiaire.ACTIF)
    fusionne_dans = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                                      related_name="dossiers_absorbes")
    completude = models.PositiveSmallIntegerField(default=0)
    source_import = models.CharField(max_length=120, blank=True, default="")
    ligne_source = models.CharField(max_length=60, blank=True, default="")
    qualite = models.CharField(max_length=12, choices=Qualite.choices, default=Qualite.FIABLE)

    # Champs visibles hors ligne et par rôle (OFF-06, RG-FOR-04) ; aucun champ R.
    CHAMPS_RESTREINTS = ("contact_urgence_nom", "contact_urgence_tel", "piece_identite_type", "piece_identite_numero")
    CHAMPS_COORDONNEES = ("telephone", "zone_residence")

    class Meta:
        db_table = "beneficiaire"
        ordering = ["nom", "prenoms"]
        constraints = [
            models.CheckConstraint(
                condition=Q(date_naissance__isnull=False) | Q(annee_naissance__isnull=False) | ~Q(tranche_age=""),
                name="beneficiaire_naissance_minimale",
            ),
            models.CheckConstraint(condition=~Q(statut="fusionne") | Q(fusionne_dans__isnull=False),
                                   name="beneficiaire_fusion_coherente"),
        ]

    def __str__(self):
        return f"{self.code} {self.prenoms} {self.nom}"

    @property
    def annee(self):
        if self.date_naissance:
            return self.date_naissance.year
        return self.annee_naissance


class StatutCandidature(models.TextChoices):
    BROUILLON = "brouillon", "Brouillon"
    SOUMISE = "soumise", "Soumise"
    INCOMPLETE = "incomplete", "Incomplète"
    VALIDEE = "validee", "Validée"
    REJETEE = "rejetee", "Rejetée"
    EN_ATTENTE = "en_attente", "En liste d'attente"
    INSCRITE = "inscrite", "Inscrite"
    ANNULEE = "annulee", "Annulée"


class DecisionDoublon(models.TextChoices):
    AUCUN = "aucun", "Aucun doublon"
    DOSSIER_EXISTANT_UTILISE = "dossier_existant_utilise", "Dossier existant utilisé"
    PERSONNE_DIFFERENTE = "personne_differente", "Personne différente"


class Candidature(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    beneficiaire = models.ForeignKey(Beneficiaire, on_delete=models.PROTECT, related_name="candidatures")
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="candidatures")
    formation = models.ForeignKey("formations.Formation", on_delete=models.PROTECT, related_name="candidatures")
    date_reception = models.DateField()
    statut = models.CharField(max_length=12, choices=StatutCandidature.choices, default=StatutCandidature.BROUILLON)
    motif = models.ForeignKey("referentiels.ReferentielValeur", null=True, blank=True, on_delete=models.PROTECT,
                              related_name="+")
    commentaire = models.TextField(blank=True, default="")
    doublon_decision = models.CharField(max_length=26, choices=DecisionDoublon.choices, default=DecisionDoublon.AUCUN)
    doublon_score = models.PositiveSmallIntegerField(default=0)
    # « À vérifier, doublon probable » : candidature créée hors ligne avec un score ≥ 60 (RG-OFF-05).
    doublon_probable = models.BooleanField(default=False)
    date_soumission = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "candidature"
        ordering = ["-date_reception"]


class StatutTransfert(models.TextChoices):
    DEMANDE = "demande", "Demandé"
    ACCEPTE = "accepte", "Accepté"
    REFUSE = "refuse", "Refusé"


class Transfert(ModeleMetier):
    beneficiaire = models.ForeignKey(Beneficiaire, on_delete=models.PROTECT, related_name="transferts")
    centre_origine = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="+")
    centre_accueil = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="+")
    motif = models.TextField()
    statut = models.CharField(max_length=8, choices=StatutTransfert.choices, default=StatutTransfert.DEMANDE)
    demande_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    decide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    decide_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "transfert"
        constraints = [
            models.CheckConstraint(condition=~Q(centre_origine=models.F("centre_accueil")),
                                   name="transfert_centres_distincts"),
        ]


class StatutPaire(models.TextChoices):
    A_TRAITER = "a_traiter", "À traiter"
    DISTINCTES = "distinctes", "Ce n'est pas un doublon"
    FUSIONNEES = "fusionnees", "Fusionnées"


class PaireDoublon(models.Model):
    """Paires suspectes recalculées chaque nuit pour E-BEN-05 (RG-BEN-04) ; table technique."""

    beneficiaire_a = models.ForeignKey(Beneficiaire, on_delete=models.PROTECT, related_name="+")
    beneficiaire_b = models.ForeignKey(Beneficiaire, on_delete=models.PROTECT, related_name="+")
    score = models.PositiveSmallIntegerField()
    champs_concordants = models.JSONField(default=list)
    statut = models.CharField(max_length=10, choices=StatutPaire.choices, default=StatutPaire.A_TRAITER)
    detectee_le = models.DateTimeField(auto_now_add=True)
    traitee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="+")
    traitee_le = models.DateTimeField(null=True, blank=True)
    commentaire = models.TextField(blank=True, default="")

    class Meta:
        db_table = "paire_doublon"
        constraints = [
            models.UniqueConstraint(fields=["beneficiaire_a", "beneficiaire_b"], name="paire_doublon_unique"),
        ]


class Fusion(ModeleMetier):
    """Fusion de deux dossiers, réversible pendant 30 jours (RG-BEN-05, BEN-09).

    Garde tout ce qu'il faut pour l'annuler : valeurs du dossier conservé avant fusion, valeurs
    retenues champ par champ, candidatures et inscriptions rattachées au dossier conservé.
    """

    conserve = models.ForeignKey(Beneficiaire, on_delete=models.PROTECT, related_name="fusions_conservees")
    absorbe = models.ForeignKey(Beneficiaire, on_delete=models.PROTECT, related_name="fusions_absorbees")
    choix = models.JSONField(default=dict)  # {champ: "conserve" | "absorbe"}
    valeurs_avant = models.JSONField(default=dict)  # valeurs du dossier conservé avant fusion
    statut_absorbe_avant = models.CharField(max_length=10)
    candidatures = models.JSONField(default=list)
    inscriptions = models.JSONField(default=list)
    paire = models.ForeignKey(PaireDoublon, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    fusionne_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    fusionne_le = models.DateTimeField()
    annulee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="+")
    annulee_le = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.TextField(blank=True, default="")

    class Meta:
        db_table = "fusion"
        ordering = ["-fusionne_le"]
        constraints = [
            models.CheckConstraint(condition=~Q(conserve=models.F("absorbe")), name="fusion_dossiers_distincts"),
        ]
