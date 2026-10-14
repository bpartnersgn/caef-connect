"""Catalogue, sessions, séances, formateurs, inscriptions, présences, évaluations, attestations
(Modèle § 4, SFD § 5)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.commun.models import ModeleMetier


class PorteeFormation(models.TextChoices):
    NATIONALE = "nationale", "Nationale"
    CENTRE = "centre", "Propre à un centre"


class StatutFormation(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class Formation(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    intitule = models.CharField(max_length=200)
    portee = models.CharField(max_length=10, choices=PorteeFormation.choices)
    centre = models.ForeignKey("referentiels.Centre", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="formations")
    categorie = models.ForeignKey("referentiels.ReferentielValeur", on_delete=models.PROTECT, related_name="+")
    objectifs = models.TextField()
    prerequis = models.TextField(blank=True, default="")
    contenu = models.TextField(blank=True, default="")
    duree_heures = models.DecimalField(max_digits=7, decimal_places=2)
    seuil_presence_pct = models.PositiveSmallIntegerField(default=80)
    evaluation_requise = models.BooleanField(default=False)
    attestation_prevue = models.BooleanField(default=True)
    absence_justifiee_exclue = models.BooleanField(default=True)
    statut = models.CharField(max_length=8, choices=StatutFormation.choices, default=StatutFormation.ACTIVE)

    class Meta:
        db_table = "formation"
        ordering = ["intitule"]
        constraints = [
            models.UniqueConstraint(fields=["categorie", "intitule"], name="formation_intitule_unique_par_categorie"),
            models.CheckConstraint(condition=Q(portee="nationale", centre__isnull=True) | Q(portee="centre", centre__isnull=False),
                                   name="formation_portee_coherente"),
            models.CheckConstraint(condition=Q(duree_heures__gt=0), name="formation_duree_positive"),
            models.CheckConstraint(condition=Q(seuil_presence_pct__lte=100), name="formation_seuil_pct"),
        ]

    def __str__(self):
        return self.intitule


class StatutIntervenant(models.TextChoices):
    INTERNE = "interne", "Interne"
    EXTERNE = "externe", "Externe"
    BENEVOLE = "benevole", "Bénévole"


class Formateur(ModeleMetier):
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                       related_name="formateur")
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone_pro = models.CharField(max_length=20, blank=True, default="")
    statut_intervenant = models.CharField(max_length=10, choices=StatutIntervenant.choices)
    competences = models.JSONField(default=list, blank=True)
    domaines = models.JSONField(default=list, blank=True)
    centres = models.ManyToManyField("referentiels.Centre", related_name="formateurs", db_table="formateur_centre")

    class Meta:
        db_table = "formateur"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class StatutSession(models.TextChoices):
    BROUILLON = "brouillon", "Brouillon"
    OUVERTE = "ouverte", "Ouverte"
    EN_COURS = "en_cours", "En cours"
    CLOTUREE = "cloturee", "Clôturée"
    ANNULEE = "annulee", "Annulée"


class SessionFormation(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    formation = models.ForeignKey(Formation, on_delete=models.PROTECT, related_name="sessions")
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="sessions")
    periode = models.ForeignKey("referentiels.Periode", on_delete=models.PROTECT, related_name="sessions")
    date_debut = models.DateField()
    date_fin = models.DateField()
    lieu = models.CharField(max_length=200, blank=True, default="")
    capacite = models.PositiveIntegerField(null=True, blank=True)
    formateur_principal = models.ForeignKey(Formateur, null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="sessions_principales")
    formateurs_associes = models.ManyToManyField(Formateur, blank=True, related_name="sessions_associees",
                                                 db_table="session_formateur_associe")
    programme = models.ForeignKey("conventions.Programme", null=True, blank=True, on_delete=models.PROTECT,
                                  related_name="sessions")
    statut = models.CharField(max_length=10, choices=StatutSession.choices, default=StatutSession.BROUILLON)
    rapport_cloture = models.JSONField(null=True, blank=True)
    commentaire_cloture = models.TextField(blank=True, default="")
    date_ouverture = models.DateTimeField(null=True, blank=True)
    date_cloture = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.TextField(blank=True, default="")

    class Meta:
        db_table = "session_formation"
        ordering = ["-date_debut"]
        constraints = [
            models.CheckConstraint(condition=Q(date_fin__gte=models.F("date_debut")), name="session_dates_coherentes"),
            models.CheckConstraint(condition=Q(capacite__isnull=True) | Q(capacite__gt=0), name="session_capacite_positive"),
        ]

    def __str__(self):
        return self.code


class Seance(ModeleMetier):
    session = models.ForeignKey(SessionFormation, on_delete=models.PROTECT, related_name="seances")
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    formateur = models.ForeignKey(Formateur, on_delete=models.PROTECT, related_name="seances")
    theme = models.CharField(max_length=200, blank=True, default="")
    presences_validees = models.BooleanField(default=False)
    presences_validees_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "seance"
        ordering = ["date", "heure_debut"]
        constraints = [
            models.CheckConstraint(condition=Q(heure_fin__gt=models.F("heure_debut")), name="seance_heures_coherentes"),
        ]


class StatutParticipation(models.TextChoices):
    INSCRITE = "inscrite", "Inscrite"
    COMMENCEE = "commencee", "Commencée"
    SUSPENDUE = "suspendue", "Suspendue"
    ABANDONNEE = "abandonnee", "Abandonnée"
    ACHEVEE = "achevee", "Achevée"
    NON_ACHEVEE = "non_achevee", "Non achevée"


STATUTS_FINAUX = (StatutParticipation.ACHEVEE, StatutParticipation.NON_ACHEVEE, StatutParticipation.ABANDONNEE)


class Inscription(ModeleMetier):
    beneficiaire = models.ForeignKey("beneficiaires.Beneficiaire", on_delete=models.PROTECT,
                                     related_name="inscriptions")
    session = models.ForeignKey(SessionFormation, on_delete=models.PROTECT, related_name="inscriptions")
    candidature = models.ForeignKey("beneficiaires.Candidature", on_delete=models.PROTECT,
                                    related_name="inscriptions")
    date_inscription = models.DateField()
    statut_participation = models.CharField(max_length=12, choices=StatutParticipation.choices,
                                            default=StatutParticipation.INSCRITE)
    motif_sortie = models.ForeignKey("referentiels.ReferentielValeur", null=True, blank=True,
                                     on_delete=models.PROTECT, related_name="+")
    taux_presence = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    derogation_motif = models.TextField(blank=True, default="")
    derogation_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                       related_name="+")
    cheffe_de_classe = models.BooleanField(default=False)
    date_statut_final = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "inscription"
        constraints = [
            models.UniqueConstraint(fields=["beneficiaire", "session"], name="inscription_unique"),
            # Au plus une cheffe de classe par session (Matrice § 2.1, TF-ORG-01).
            models.UniqueConstraint(fields=["session"], condition=Q(cheffe_de_classe=True),
                                    name="inscription_une_cheffe_de_classe"),
        ]


class EtatPresence(models.TextChoices):
    PRESENTE = "presente", "Présente"
    ABSENTE = "absente", "Absente"
    RETARD = "retard", "Retard"
    ABSENCE_JUSTIFIEE = "absence_justifiee", "Absence justifiée"


class Presence(ModeleMetier):
    seance = models.ForeignKey(Seance, on_delete=models.PROTECT, related_name="presences")
    inscription = models.ForeignKey(Inscription, on_delete=models.PROTECT, related_name="presences")
    etat = models.CharField(max_length=18, choices=EtatPresence.choices)
    justificatif = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="+")
    saisi_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    saisi_le = models.DateTimeField()
    saisie_tardive_motif = models.TextField(blank=True, default="")

    class Meta:
        db_table = "presence"
        constraints = [models.UniqueConstraint(fields=["seance", "inscription"], name="presence_unique")]


class TypeResultat(models.TextChoices):
    NOTE = "note", "Note"
    APPRECIATION = "appreciation", "Appréciation"
    ACQUIS = "acquis", "Acquis"


class Evaluation(ModeleMetier):
    inscription = models.ForeignKey(Inscription, on_delete=models.PROTECT, related_name="evaluations")
    intitule = models.CharField(max_length=200)
    date = models.DateField()
    type_resultat = models.CharField(max_length=14, choices=TypeResultat.choices)
    note = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    note_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    appreciation = models.CharField(max_length=60, blank=True, default="")

    class Meta:
        db_table = "evaluation"
        constraints = [
            models.CheckConstraint(
                condition=~Q(type_resultat="note") | (Q(note__isnull=False) & Q(note_max__gt=0) & Q(note__lte=models.F("note_max"))),
                name="evaluation_note_coherente"),
        ]


class StatutAttestation(models.TextChoices):
    DELIVREE = "delivree", "Délivrée"
    ANNULEE = "annulee", "Annulée"


class Attestation(ModeleMetier):
    inscription = models.OneToOneField(Inscription, on_delete=models.PROTECT, related_name="attestation")
    numero = models.CharField(max_length=30, unique=True)
    date_delivrance = models.DateField()
    delivre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    statut = models.CharField(max_length=8, choices=StatutAttestation.choices, default=StatutAttestation.DELIVREE)
    motif_annulation = models.TextField(blank=True, default="")
    document = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="+")

    class Meta:
        db_table = "attestation"
