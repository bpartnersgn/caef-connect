"""Paiements en espèces et Mobile Money, affectations, transactions de la passerelle,
remboursements et relevés de l'opérateur (Modèle § 9, SFD § 12, PAY-04 à PAY-11, SEC-14).

CAEF Connect ne détient jamais les fonds : seule la confirmation de l'opérateur fait d'un
paiement un encaissement, avec le montant de l'opérateur.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from caef.boutique.models import gnf_entier
from caef.commun.champs import Montant
from caef.commun.models import ModeleMetier


class CanalPaiement(models.TextChoices):
    ESPECES = "especes", "Espèces"
    MOBILE_MONEY_DEMANDE = "mobile_money_demande", "Mobile Money, demande de paiement"
    MOBILE_MONEY_PAYEUSE = "mobile_money_payeuse", "Mobile Money, à l'initiative de la payeuse"
    MOBILE_MONEY_DECLARE = "mobile_money_declare", "Mobile Money déclaré"


class StatutPaiement(models.TextChoices):
    INITIE = "initie", "Initié"
    EN_ATTENTE = "en_attente", "En attente de la payeuse"
    CONFIRME = "confirme", "Confirmé"
    ECHOUE = "echoue", "Échoué"
    EXPIRE = "expire", "Expiré"
    DECLARE = "declare", "Déclaré"
    NON_RETROUVE = "non_retrouve", "Non retrouvé"
    REMBOURSE_PARTIELLEMENT = "rembourse_partiellement", "Remboursé partiellement"
    REMBOURSE = "rembourse", "Remboursé"


STATUTS_ENCAISSES = (StatutPaiement.CONFIRME, StatutPaiement.REMBOURSE_PARTIELLEMENT, StatutPaiement.REMBOURSE)


class Paiement(ModeleMetier):
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="paiements")
    canal = models.CharField(max_length=22, choices=CanalPaiement.choices)
    fournisseur = models.CharField(max_length=30, blank=True, default="")
    montant_attendu = Montant(null=True, blank=True)
    montant_confirme = Montant(null=True, blank=True)
    commission = Montant(null=True, blank=True)
    montant_net = Montant(null=True, blank=True)
    telephone_payeuse = models.CharField(max_length=20, blank=True, default="")
    identifiant_transaction = models.CharField(max_length=60, blank=True, default="", db_index=True)
    reference_echeance = models.CharField(max_length=20, blank=True, default="")
    statut = models.CharField(max_length=24, choices=StatutPaiement.choices)
    motif_operateur = models.CharField(max_length=255, blank=True, default="")
    serie_recu = models.CharField(max_length=12, blank=True, default="")
    numero_recu = models.PositiveIntegerField(null=True, blank=True)
    encaisse_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="+")
    confirme_le = models.DateTimeField(null=True, blank=True)
    # Échéances visées à l'initiation (parcours A et C), affectées à la confirmation (voir DECISIONS.md).
    affectation_prevue = models.JSONField(default=list, blank=True)
    usage_boutique = models.BooleanField(default=False)

    class Meta:
        db_table = "paiement"
        ordering = ["-cree_le"]
        constraints = [
            models.CheckConstraint(condition=gnf_entier("montant_attendu") & gnf_entier("montant_confirme")
                                   & gnf_entier("commission") & gnf_entier("montant_net"),
                                   name="paiement_gnf_entier"),
            models.CheckConstraint(condition=~Q(canal="mobile_money_declare") | ~Q(identifiant_transaction=""),
                                   name="paiement_declare_identifiant"),
            models.CheckConstraint(condition=~Q(statut="confirme") | Q(montant_confirme__isnull=False),
                                   name="paiement_confirme_montant"),
        ]

    @property
    def montant_affecte(self):
        return sum((a.montant for a in self.affectations.all()), 0)

    @property
    def montant_rembourse(self):
        return sum((r.montant for r in self.remboursements.filter(statut="execute")), 0)


class AffectationPaiement(ModeleMetier):
    paiement = models.ForeignKey(Paiement, on_delete=models.PROTECT, related_name="affectations")
    echeance = models.ForeignKey("facturation.Echeance", on_delete=models.PROTECT, related_name="affectations")
    montant = Montant()
    affecte_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                    related_name="+")
    motif = models.TextField(blank=True, default="")
    automatique = models.BooleanField(default=False)

    class Meta:
        db_table = "affectation_paiement"
        constraints = [
            models.CheckConstraint(condition=Q(montant__gt=0) & gnf_entier("montant"), name="affectation_gnf_entier"),
            models.CheckConstraint(condition=Q(automatique=True) | ~Q(motif="") | Q(affecte_par__isnull=True),
                                   name="affectation_manuelle_motivee"),
        ]


class TypeTransaction(models.TextChoices):
    NOTIFICATION = "notification", "Notification"
    CONSULTATION = "consultation", "Consultation"
    REMBOURSEMENT = "remboursement", "Remboursement"


class TransactionPasserelle(models.Model):
    """Ce que l'opérateur a communiqué ; une transaction de l'opérateur n'est enregistrée
    qu'une fois (PAY-08). Les messages à signature invalide ne sont pas enregistrés ici mais
    au journal d'audit (SEC-14)."""

    id = models.UUIDField(primary_key=True, editable=False)
    paiement = models.ForeignKey(Paiement, null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="transactions")
    fournisseur = models.CharField(max_length=30)
    identifiant_operateur = models.CharField(max_length=60)
    type = models.CharField(max_length=14, choices=TypeTransaction.choices)
    statut_operateur = models.CharField(max_length=40)
    montant = Montant()
    commission = Montant(null=True, blank=True)
    signature_valide = models.BooleanField(default=True)
    recu_le = models.DateTimeField()
    donnees_brutes = models.JSONField()

    class Meta:
        db_table = "transaction_passerelle"
        constraints = [
            models.UniqueConstraint(fields=["fournisseur", "identifiant_operateur"], name="transaction_unique"),
        ]


class StatutRemboursement(models.TextChoices):
    DEMANDE = "demande", "Demandé"
    VALIDE = "valide", "Validé"
    REFUSE = "refuse", "Refusé"
    EXECUTE = "execute", "Exécuté"


class ExecutionRemboursement(models.TextChoices):
    PASSERELLE = "passerelle", "Par la passerelle"
    HORS_OUTIL = "hors_outil", "Hors outil, avec pièce"


class Remboursement(ModeleMetier):
    paiement = models.ForeignKey(Paiement, on_delete=models.PROTECT, related_name="remboursements")
    echeance = models.ForeignKey("facturation.Echeance", null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="remboursements")
    montant = Montant()
    motif = models.TextField()
    demande_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)
    execution = models.CharField(max_length=12, choices=ExecutionRemboursement.choices)
    piece_justificative = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="+")
    statut = models.CharField(max_length=8, choices=StatutRemboursement.choices, default=StatutRemboursement.DEMANDE)
    execute_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "remboursement"
        constraints = [
            models.CheckConstraint(condition=Q(montant__gt=0) & gnf_entier("montant"), name="remboursement_gnf_entier"),
            models.CheckConstraint(condition=Q(valide_par__isnull=True) | ~Q(valide_par=models.F("demande_par")),
                                   name="remboursement_valideur_distinct"),
            models.CheckConstraint(
                condition=~(Q(statut="execute") & Q(execution="hors_outil")) | Q(piece_justificative__isnull=False),
                name="remboursement_hors_outil_piece"),
        ]


class StatutRapprochement(models.TextChoices):
    APPARIE = "apparie", "Apparié"
    ABSENT_OUTIL = "absent_outil", "Absent de l'outil"
    ABSENT_RELEVE = "absent_releve", "Absent du relevé"
    ECART_MONTANT = "ecart_montant", "Écart de montant"


class LigneReleveOperateur(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="+")
    fournisseur = models.CharField(max_length=30)
    date_releve = models.DateField()
    identifiant_operateur = models.CharField(max_length=60)
    montant = Montant()
    commission = Montant(default=0)
    transaction_passerelle = models.ForeignKey(TransactionPasserelle, null=True, blank=True,
                                               on_delete=models.PROTECT, related_name="lignes_releve")
    paiement = models.ForeignKey(Paiement, null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="lignes_releve")
    statut_rapprochement = models.CharField(max_length=14, choices=StatutRapprochement.choices)
    motif = models.TextField(blank=True, default="")
    motive_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    importe_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ligne_releve_operateur"
        constraints = [
            models.UniqueConstraint(fields=["fournisseur", "identifiant_operateur"], name="releve_ligne_unique"),
        ]
