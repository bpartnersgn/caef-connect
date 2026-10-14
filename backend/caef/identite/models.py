"""Comptes nominatifs (USR-01) et double authentification (SEC-11)."""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from caef.commun.champs import TexteChiffre
from caef.commun.exceptions import RegleMetier
from caef.commun.models import uuid7


class StatutUtilisateur(models.TextChoices):
    ACTIF = "actif", "Actif"
    SUSPENDU = "suspendu", "Suspendu"
    DESACTIVE = "desactive", "Désactivé"


class GestionnaireUtilisateurs(BaseUserManager):
    def create_user(self, identifiant_connexion, mot_de_passe=None, **champs):
        if not identifiant_connexion:
            raise ValueError("L'identifiant de connexion est obligatoire.")
        utilisateur = self.model(identifiant_connexion=identifiant_connexion, **champs)
        if mot_de_passe:
            utilisateur.set_password(mot_de_passe)
        else:
            utilisateur.set_unusable_password()
        utilisateur.save(using=self._db)
        return utilisateur

    def get_by_natural_key(self, identifiant):
        return self.get(identifiant_connexion=identifiant)


class Utilisateur(AbstractBaseUser):
    """Table `utilisateur` (Modèle § 3). Aucun compte partagé ; identifiant jamais réattribué."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    identifiant_connexion = models.CharField(max_length=120, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone_pro = models.CharField(max_length=20, blank=True, default="")
    password = models.CharField(max_length=256, db_column="empreinte_mot_de_passe")
    double_auth_active = models.BooleanField(default=False)
    secret_double_auth = TexteChiffre(null=True, blank=True)
    codes_secours = models.JSONField(default=list, blank=True)  # empreintes des codes de secours
    statut = models.CharField(max_length=12, choices=StatutUtilisateur.choices, default=StatutUtilisateur.ACTIF)
    last_login = models.DateTimeField(null=True, blank=True, db_column="derniere_connexion")
    echecs_consecutifs = models.PositiveIntegerField(default=0)
    echecs_horodatages = models.JSONField(default=list, blank=True)
    bloque_jusqua = models.DateTimeField(null=True, blank=True)
    mot_de_passe_temporaire = models.BooleanField(default=False)
    cree_le = models.DateTimeField(default=timezone.now, editable=False)
    modifie_le = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "identifiant_connexion"
    REQUIRED_FIELDS = ["nom", "prenom"]

    objects = GestionnaireUtilisateurs()

    class Meta:
        db_table = "utilisateur"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def is_active(self):
        return self.statut == StatutUtilisateur.ACTIF

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def delete(self, *args, **kwargs):
        raise RegleMetier("Un compte n'est jamais supprimé : désactivez-le (RG-ADM-07).")
