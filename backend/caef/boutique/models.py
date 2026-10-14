"""Boutique et salle d'exposition (Modèle § 6, SFD § 9, BOU-01 à BOU-11, BOU-15).

Montants en GNF entiers ; aucune suppression ; le stock est la somme des mouvements ;
aucune donnée sur l'acheteur.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum

from caef.commun.champs import Montant
from caef.commun.models import ModeleAjoutSeul, ModeleMetier


def gnf_entier(champ):
    """Contrôle en base : partie décimale nulle (Modèle § 6)."""
    return Q(**{f"{champ}__isnull": True}) | Q(**{champ: models.functions.Floor(models.F(champ))})


class PointDeVente(ModeleMetier):
    centre = models.ForeignKey("referentiels.Centre", on_delete=models.PROTECT, related_name="points_de_vente")
    nom = models.CharField(max_length=150)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = "point_de_vente"
        constraints = [
            # Un seul point de vente actif par centre au MVP (BOU-13 en P2).
            models.UniqueConstraint(fields=["centre"], condition=Q(actif=True), name="un_point_de_vente_actif_par_centre"),
        ]

    def __str__(self):
        return self.nom


class OrigineProduit(models.TextChoices):
    ATELIER_CENTRE = "atelier_centre", "Atelier du centre"
    SESSION_FORMATION = "session_formation", "Session de formation"
    DEPOT_VENTE = "depot_vente", "Dépôt-vente"
    GROUPEMENT = "groupement", "Groupement"
    ACHAT_REVENTE = "achat_revente", "Achat pour revente"


class Produit(ModeleMetier):
    code = models.CharField(max_length=30, unique=True)
    point_de_vente = models.ForeignKey(PointDeVente, on_delete=models.PROTECT, related_name="produits")
    nom = models.CharField(max_length=150)
    categorie = models.ForeignKey("referentiels.ReferentielValeur", on_delete=models.PROTECT, related_name="+")
    unite = models.ForeignKey("referentiels.ReferentielValeur", on_delete=models.PROTECT, related_name="+")
    origine = models.CharField(max_length=20, choices=OrigineProduit.choices)
    beneficiaire_deposante = models.ForeignKey("beneficiaires.Beneficiaire", null=True, blank=True,
                                               on_delete=models.PROTECT, related_name="produits_deposes")
    groupement = models.CharField(max_length=150, blank=True, default="")
    session_origine = models.ForeignKey("formations.SessionFormation", null=True, blank=True,
                                        on_delete=models.PROTECT, related_name="+")
    formation_origine = models.ForeignKey("formations.Formation", null=True, blank=True, on_delete=models.PROTECT,
                                          related_name="+")
    seuil_alerte = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = "produit"
        ordering = ["nom"]
        constraints = [
            models.UniqueConstraint(fields=["point_de_vente", "nom"], name="produit_nom_unique_par_point_de_vente"),
            models.CheckConstraint(
                condition=~Q(origine="depot_vente") | Q(beneficiaire_deposante__isnull=False) | ~Q(groupement=""),
                name="produit_depot_vente_deposante"),
            models.CheckConstraint(condition=~Q(origine="groupement") | ~Q(groupement=""),
                                   name="produit_groupement_nomme"),
        ]

    def __str__(self):
        return self.nom


class PrixProduit(ModeleAjoutSeul):
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="prix")
    prix = Montant()
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "prix_produit"
        ordering = ["-date_debut"]
        constraints = [
            models.CheckConstraint(condition=Q(prix__gt=0) & gnf_entier("prix"), name="prix_gnf_entier_positif"),
            models.UniqueConstraint(fields=["produit"], condition=Q(date_fin__isnull=True), name="un_prix_en_vigueur"),
        ]


class StatutDepot(models.TextChoices):
    EN_COURS = "en_cours", "En cours"
    SOLDE = "solde", "Soldé"
    RETIRE = "retire", "Retiré"


class Depot(ModeleMetier):
    beneficiaire = models.ForeignKey("beneficiaires.Beneficiaire", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="depots")
    groupement = models.CharField(max_length=150, blank=True, default="")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="depots")
    quantite_deposee = models.DecimalField(max_digits=12, decimal_places=3)
    part_centre_pct = models.DecimalField(max_digits=5, decimal_places=2)
    date_depot = models.DateField()
    statut = models.CharField(max_length=8, choices=StatutDepot.choices, default=StatutDepot.EN_COURS)

    class Meta:
        db_table = "depot"
        constraints = [
            models.CheckConstraint(condition=(Q(beneficiaire__isnull=False) & Q(groupement=""))
                                   | (Q(beneficiaire__isnull=True) & ~Q(groupement="")),
                                   name="depot_deposante_exclusive"),
            models.CheckConstraint(condition=Q(quantite_deposee__gt=0), name="depot_quantite_positive"),
            models.CheckConstraint(condition=Q(part_centre_pct__gte=0) & Q(part_centre_pct__lte=100),
                                   name="depot_part_centre_0_100"),
        ]


class TypeMouvement(models.TextChoices):
    ENTREE_PRODUCTION = "entree_production", "Entrée production"
    ENTREE_DEPOT = "entree_depot", "Entrée dépôt"
    ENTREE_ACHAT = "entree_achat", "Entrée achat"
    VENTE = "vente", "Vente"
    SORTIE_PERTE = "sortie_perte", "Sortie perte"
    SORTIE_DON = "sortie_don", "Sortie don"
    SORTIE_ECHANTILLON = "sortie_echantillon", "Sortie échantillon"
    SORTIE_USAGE_INTERNE = "sortie_usage_interne", "Sortie usage interne"
    AJUSTEMENT_INVENTAIRE = "ajustement_inventaire", "Ajustement inventaire"
    TRANSFERT = "transfert", "Transfert"
    ANNULATION = "annulation", "Annulation"


TYPES_ENTREE = {TypeMouvement.ENTREE_PRODUCTION, TypeMouvement.ENTREE_DEPOT, TypeMouvement.ENTREE_ACHAT}
TYPES_SORTIE = {TypeMouvement.SORTIE_PERTE, TypeMouvement.SORTIE_DON, TypeMouvement.SORTIE_ECHANTILLON,
                TypeMouvement.SORTIE_USAGE_INTERNE}


class Emplacement(models.TextChoices):
    BOUTIQUE = "boutique", "Boutique"
    SALLE_EXPOSITION = "salle_exposition", "Salle d'exposition"


class MouvementStock(ModeleAjoutSeul):
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="mouvements")
    type = models.CharField(max_length=22, choices=TypeMouvement.choices)
    quantite = models.DecimalField(max_digits=12, decimal_places=3)
    date_mouvement = models.DateTimeField()
    motif = models.TextField(blank=True, default="")
    vente = models.ForeignKey("Vente", null=True, blank=True, on_delete=models.PROTECT, related_name="mouvements")
    inventaire = models.ForeignKey("Inventaire", null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="mouvements")
    depot = models.ForeignKey(Depot, null=True, blank=True, on_delete=models.PROTECT, related_name="mouvements")
    mouvement_annule = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                                         related_name="annulations")
    emplacement = models.CharField(max_length=16, choices=Emplacement.choices, default=Emplacement.BOUTIQUE)
    transfert_lie = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT,
                                         related_name="transfert_oppose")
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "mouvement_stock"
        ordering = ["date_mouvement"]
        constraints = [
            models.CheckConstraint(condition=~Q(quantite=0), name="mouvement_quantite_non_nulle"),
            models.CheckConstraint(
                condition=~Q(type__in=["sortie_perte", "sortie_don", "sortie_echantillon", "sortie_usage_interne",
                                       "ajustement_inventaire", "annulation"]) | ~Q(motif=""),
                name="mouvement_motif_obligatoire"),
        ]


class StatutVente(models.TextChoices):
    VALIDEE = "validee", "Validée"
    ANNULEE = "annulee", "Annulée"


class Vente(ModeleAjoutSeul):
    """Une vente validée n'est jamais modifiée : son annulation est une vente d'annulation
    liée (statut « annulée », total négatif) datée du jour de l'annulation (RG-BOU-02).

    Un numéro de reçu attribué à une vente qui a échoué est consigné par une ligne
    « annulée » sans montant ni vente d'origine (BOU-06)."""

    point_de_vente = models.ForeignKey(PointDeVente, on_delete=models.PROTECT, related_name="ventes")
    serie_recu = models.CharField(max_length=12)
    numero_recu = models.PositiveIntegerField()
    numero_recu_papier = models.CharField(max_length=30, null=True, blank=True)
    date_heure_vente = models.DateTimeField()
    vendeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    session_caisse = models.ForeignKey("SessionCaisse", null=True, blank=True, on_delete=models.PROTECT,
                                       related_name="ventes")
    total = Montant()
    statut = models.CharField(max_length=8, choices=StatutVente.choices)
    motif_annulation = models.TextField(blank=True, default="")
    vente_annulation = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="contre_ecriture")
    mois_corrige = models.CharField(max_length=7, blank=True, default="")  # régularisation (RG-SRC-03)
    emplacement = models.CharField(max_length=16, choices=Emplacement.choices, default=Emplacement.BOUTIQUE)

    class Meta:
        db_table = "vente"
        ordering = ["-date_heure_vente"]
        constraints = [
            models.UniqueConstraint(fields=["point_de_vente", "serie_recu", "numero_recu"], name="recu_unique"),
            models.UniqueConstraint(fields=["point_de_vente", "numero_recu_papier"],
                                    condition=Q(numero_recu_papier__isnull=False), name="recu_papier_unique"),
            models.CheckConstraint(condition=gnf_entier("total"), name="vente_total_gnf_entier"),
            models.CheckConstraint(condition=~Q(statut="annulee") | ~Q(motif_annulation=""),
                                   name="vente_annulation_motivee"),
        ]

    @property
    def est_annulee(self):
        return hasattr(self, "contre_ecriture") and self.contre_ecriture is not None

    @property
    def numero_complet(self):
        return f"{self.serie_recu}-{self.numero_recu:06d}"


class LigneVente(ModeleAjoutSeul):
    vente = models.ForeignKey(Vente, on_delete=models.PROTECT, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="+")
    quantite = models.DecimalField(max_digits=12, decimal_places=3)
    prix_unitaire_applique = Montant()
    remise = Montant(default=0)
    motif_remise = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ligne_vente"
        constraints = [
            models.CheckConstraint(condition=Q(quantite__gt=0), name="ligne_vente_quantite_positive"),
            models.CheckConstraint(condition=Q(remise=0) | ~Q(motif_remise=""), name="ligne_vente_remise_motivee"),
            models.CheckConstraint(condition=gnf_entier("prix_unitaire_applique") & gnf_entier("remise"),
                                   name="ligne_vente_gnf_entier"),
        ]

    @property
    def montant(self):
        return self.quantite * self.prix_unitaire_applique - self.remise


class ModeReglement(models.TextChoices):
    ESPECES = "especes", "Espèces"
    MOBILE_MONEY = "mobile_money", "Mobile Money"
    VIREMENT = "virement", "Virement"
    CHEQUE = "cheque", "Chèque"


class StatutReglement(models.TextChoices):
    CONFIRME = "confirme", "Confirmé"
    DECLARE = "declare", "Déclaré"
    NON_RETROUVE = "non_retrouve", "Non retrouvé"


class Reglement(ModeleAjoutSeul):
    vente = models.ForeignKey(Vente, on_delete=models.PROTECT, related_name="reglements")
    mode = models.CharField(max_length=14, choices=ModeReglement.choices)
    montant = Montant()
    reference_externe = models.CharField(max_length=60, blank=True, default="")
    paiement = models.ForeignKey("paiements.Paiement", null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="reglements")
    statut = models.CharField(max_length=14, choices=StatutReglement.choices)

    class Meta:
        db_table = "reglement"
        constraints = [
            models.CheckConstraint(condition=~Q(montant=0) & gnf_entier("montant"), name="reglement_gnf_entier"),
            models.CheckConstraint(condition=~Q(mode="mobile_money") | Q(paiement__isnull=False),
                                   name="reglement_mobile_money_paiement"),
            models.CheckConstraint(condition=~Q(mode__in=["virement", "cheque"]) | ~Q(reference_externe=""),
                                   name="reglement_reference_obligatoire"),
        ]


class StatutCaisse(models.TextChoices):
    OUVERTE = "ouverte", "Ouverte"
    COMPTEE = "comptee", "Comptée"
    VALIDEE = "validee", "Validée"
    VALIDEE_AVEC_ECART = "validee_avec_ecart", "Validée avec écart"


class SessionCaisse(ModeleMetier):
    point_de_vente = models.ForeignKey(PointDeVente, on_delete=models.PROTECT, related_name="sessions_caisse")
    date = models.DateField()
    ouverte_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    fond_de_caisse = Montant()
    montants_theoriques = models.JSONField(default=dict, blank=True)  # par mode de règlement
    montants_comptes = models.JSONField(default=dict, blank=True)
    ecart = Montant(null=True, blank=True)
    motif_ecart = models.TextField(blank=True, default="")
    compte_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    compte_le = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)
    motif_recomptage = models.TextField(blank=True, default="")
    statut = models.CharField(max_length=20, choices=StatutCaisse.choices, default=StatutCaisse.OUVERTE)

    class Meta:
        db_table = "session_caisse"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["point_de_vente", "date"], name="une_caisse_par_jour"),
            models.CheckConstraint(condition=gnf_entier("fond_de_caisse") & gnf_entier("ecart"),
                                   name="caisse_gnf_entier"),
            models.CheckConstraint(condition=Q(ecart__isnull=True) | Q(ecart=0) | ~Q(motif_ecart=""),
                                   name="caisse_ecart_motive"),
        ]


class StatutInventaire(models.TextChoices):
    EN_COMPTAGE = "en_comptage", "En comptage"
    COMPTE = "compte", "Compté"
    VALIDE = "valide", "Validé"


class Inventaire(ModeleMetier):
    point_de_vente = models.ForeignKey(PointDeVente, on_delete=models.PROTECT, related_name="inventaires")
    date_inventaire = models.DateField()
    ouvert_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    compte_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)
    motif_recomptage = models.TextField(blank=True, default="")
    statut = models.CharField(max_length=12, choices=StatutInventaire.choices, default=StatutInventaire.EN_COMPTAGE)

    class Meta:
        db_table = "inventaire"
        constraints = [
            models.CheckConstraint(condition=Q(valide_par__isnull=True) | ~Q(valide_par=models.F("compte_par")),
                                   name="inventaire_separation_des_taches"),
        ]


class LigneInventaire(models.Model):
    inventaire = models.ForeignKey(Inventaire, on_delete=models.PROTECT, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name="+")
    emplacement = models.CharField(max_length=16, choices=Emplacement.choices, default=Emplacement.BOUTIQUE)
    quantite_theorique = models.DecimalField(max_digits=12, decimal_places=3)
    quantite_comptee = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    ecart = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    motif = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ligne_inventaire"
        constraints = [
            models.UniqueConstraint(fields=["inventaire", "produit", "emplacement"], name="ligne_inventaire_unique"),
        ]


class StatutReversement(models.TextChoices):
    PREPARE = "prepare", "Préparé"
    VALIDE = "valide", "Validé"
    PAYE = "paye", "Payé"


class Reversement(ModeleMetier):
    point_de_vente = models.ForeignKey(PointDeVente, on_delete=models.PROTECT, related_name="reversements")
    beneficiaire = models.ForeignKey("beneficiaires.Beneficiaire", null=True, blank=True, on_delete=models.PROTECT,
                                     related_name="reversements")
    groupement = models.CharField(max_length=150, blank=True, default="")
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    montant_du = Montant()
    montant_reverse = Montant()
    date_paiement = models.DateField(null=True, blank=True)
    mode = models.CharField(max_length=14, choices=ModeReglement.choices, blank=True, default="")
    piece_justificative = models.ForeignKey("documents.Document", null=True, blank=True, on_delete=models.PROTECT,
                                            related_name="+")
    statut = models.CharField(max_length=8, choices=StatutReversement.choices, default=StatutReversement.PREPARE)
    prepare_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                   related_name="+")
    valide_le = models.DateTimeField(null=True, blank=True)
    paye_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
                                 related_name="+")

    class Meta:
        db_table = "reversement"
        constraints = [
            models.CheckConstraint(condition=(Q(beneficiaire__isnull=False) & Q(groupement=""))
                                   | (Q(beneficiaire__isnull=True) & ~Q(groupement="")),
                                   name="reversement_deposante_exclusive"),
            models.CheckConstraint(condition=Q(montant_reverse__gt=0) & gnf_entier("montant_reverse") & gnf_entier("montant_du"),
                                   name="reversement_gnf_entier"),
            models.CheckConstraint(condition=Q(valide_par__isnull=True) | ~Q(valide_par=models.F("prepare_par")),
                                   name="reversement_valideur_distinct"),
            models.CheckConstraint(condition=Q(paye_par__isnull=True) | ~Q(paye_par=models.F("valide_par")),
                                   name="reversement_payeur_distinct"),
            models.CheckConstraint(
                condition=~Q(statut="paye") | (Q(date_paiement__isnull=False) & ~Q(mode="") & Q(piece_justificative__isnull=False)),
                name="reversement_paye_complet"),
        ]


def stock(produit, emplacement=None):
    """Stock = somme des mouvements (BOU-04) ; jamais un champ modifiable."""
    qs = MouvementStock.objects.filter(produit=produit)
    if emplacement:
        qs = qs.filter(emplacement=emplacement)
    return qs.aggregate(total=Sum("quantite"))["total"] or 0
