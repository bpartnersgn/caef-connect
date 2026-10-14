"""Partenaires, interlocuteurs, interactions, opportunités, pipeline et fiches projet
(Modèle § 5, SFD § 6)."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.commun.champs import Montant
from caef.commun.models import ModeleMetier


class StatutPartenaire(models.TextChoices):
    PROSPECT = "prospect", "Prospect"
    ACTIF = "actif", "Actif"
    INACTIF = "inactif", "Inactif"


class Partenaire(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    raison_sociale = models.CharField(max_length=200)
    raison_sociale_normalisee = models.CharField(max_length=200, db_index=True, editable=False)
    sigle = models.CharField(max_length=30, blank=True, default="")
    categorie = models.ForeignKey("referentiels.ReferentielValeur", on_delete=models.PROTECT, related_name="+")
    secteur = models.ForeignKey("referentiels.ReferentielValeur", on_delete=models.PROTECT, related_name="+")
    adresse = models.CharField(max_length=255, blank=True, default="")
    telephone = models.CharField(max_length=20, blank=True, default="")
    courriel = models.EmailField(blank=True, default="")
    site_web = models.URLField(blank=True, default="")
    responsable_suivi = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    statut = models.CharField(max_length=10, choices=StatutPartenaire.choices, default=StatutPartenaire.PROSPECT)

    class Meta:
        db_table = "partenaire"
        ordering = ["raison_sociale"]

    def __str__(self):
        return self.raison_sociale


class Interlocuteur(ModeleMetier):
    partenaire = models.ForeignKey(Partenaire, on_delete=models.PROTECT, related_name="interlocuteurs")
    nom = models.CharField(max_length=150)
    fonction = models.CharField(max_length=150)
    telephone_pro = models.CharField(max_length=20, blank=True, default="")
    courriel_pro = models.EmailField(blank=True, default="")
    principal = models.BooleanField(default=False)

    class Meta:
        db_table = "interlocuteur"
        constraints = [
            models.UniqueConstraint(fields=["partenaire"], condition=Q(principal=True),
                                    name="interlocuteur_un_seul_principal"),
        ]


class TypeInteraction(models.TextChoices):
    APPEL = "appel", "Appel"
    COURRIEL = "courriel", "Courriel"
    RENDEZ_VOUS = "rendez_vous", "Rendez-vous"
    VISITE = "visite", "Visite"
    EVENEMENT = "evenement", "Événement"


class Interaction(ModeleMetier):
    partenaire = models.ForeignKey(Partenaire, on_delete=models.PROTECT, related_name="interactions")
    opportunite = models.ForeignKey("Opportunite", null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="interactions")
    type = models.CharField(max_length=12, choices=TypeInteraction.choices)
    date = models.DateField()
    participants_internes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="+",
                                                   db_table="interaction_participant")
    interlocuteurs = models.ManyToManyField(Interlocuteur, blank=True, related_name="interactions",
                                            db_table="interaction_interlocuteur")
    compte_rendu = models.TextField(blank=True, default="")
    prochaine_action = models.CharField(max_length=255, blank=True, default="")
    date_prochaine_action = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "interaction"
        ordering = ["-date"]


class StatutFicheProjet(models.TextChoices):
    BROUILLON = "brouillon", "Brouillon"
    QUALIFIEE = "qualifiee", "Qualifiée"
    RATTACHEE = "rattachee", "Rattachée"
    ABANDONNEE = "abandonnee", "Abandonnée"


class FicheProjet(ModeleMetier):
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="fiches_projet")
    intitule = models.CharField(max_length=200)
    besoin = models.TextField()
    beneficiaires_vises = models.TextField()
    objectif_impact = models.TextField()
    indicateurs = models.TextField()
    budget_indicatif = Montant(null=True, blank=True)
    devise = models.CharField(max_length=3, default="GNF")
    statut = models.CharField(max_length=10, choices=StatutFicheProjet.choices, default=StatutFicheProjet.BROUILLON)

    class Meta:
        db_table = "fiche_projet"


class Potentiel(models.TextChoices):
    FAIBLE = "faible", "Faible"
    MOYEN = "moyen", "Moyen"
    FORT = "fort", "Fort"


class StatutOpportunite(models.TextChoices):
    OUVERTE = "ouverte", "Ouverte"
    GAGNEE = "gagnee", "Gagnée"
    PERDUE = "perdue", "Perdue"
    SUSPENDUE = "suspendue", "Suspendue"


ETAPES_PIPELINE = {
    1: "Prospect identifié", 2: "Prospect qualifié", 3: "Premier contact réalisé", 4: "Rendez-vous planifié",
    5: "Diagnostic des besoins réalisé", 6: "Proposition en préparation", 7: "Proposition soumise",
    8: "Négociation en cours", 9: "Partenariat approuvé", 10: "Convention signée",
    11: "Engagement en cours d'exécution", 12: "Contribution encaissée ou reçue", 13: "Programme exécuté",
    14: "Rapport d'impact transmis", 15: "Partenariat renouvelé ou clôturé",
}
DERNIERE_ETAPE_MANUELLE = 8  # RG-PAR-02 : 9 à 15 dérivées des statuts


class Opportunite(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    intitule = models.CharField(max_length=200)
    partenaire = models.ForeignKey(Partenaire, on_delete=models.PROTECT, related_name="opportunites")
    origine = models.ForeignKey("referentiels.ReferentielValeur", on_delete=models.PROTECT, related_name="+")
    apporteur = models.CharField(max_length=150, blank=True, default="")
    centres = models.ManyToManyField("referentiels.Centre", related_name="opportunites",
                                     db_table="opportunite_centre")
    fiches_projet = models.ManyToManyField(FicheProjet, blank=True, related_name="opportunites",
                                           db_table="opportunite_fiche_projet")
    montant_estime = Montant(null=True, blank=True)
    devise = models.CharField(max_length=3, default="GNF")
    potentiel = models.CharField(max_length=6, choices=Potentiel.choices, blank=True, default="")
    etape = models.PositiveSmallIntegerField(default=1)
    statut = models.CharField(max_length=10, choices=StatutOpportunite.choices, default=StatutOpportunite.OUVERTE)
    motif_cloture = models.ForeignKey("referentiels.ReferentielValeur", null=True, blank=True,
                                      on_delete=models.PROTECT, related_name="+")
    prochaine_action = models.CharField(max_length=255, blank=True, default="")
    date_prochaine_action = models.DateField(null=True, blank=True)
    contributeurs = models.JSONField(default=list, blank=True)  # [{utilisateur, role}], sans commission
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "opportunite"
        constraints = [
            models.CheckConstraint(condition=Q(etape__gte=1) & Q(etape__lte=15), name="opportunite_etape_1_15"),
        ]


class HistoriqueEtape(models.Model):
    opportunite = models.ForeignKey(Opportunite, on_delete=models.PROTECT, related_name="historique")
    etape_avant = models.PositiveSmallIntegerField(null=True, blank=True)
    etape_apres = models.PositiveSmallIntegerField()
    date = models.DateTimeField()
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    commentaire = models.TextField(blank=True, default="")

    class Meta:
        db_table = "historique_etape"
        ordering = ["date"]
