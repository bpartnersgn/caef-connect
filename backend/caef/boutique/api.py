"""Boutique : produits et prix, stock, ventes, caisse, inventaires, reversements, tableau de bord
(E-BOU-01 à 10). Le prix et le total sont toujours calculés par le serveur."""

from django.utils.dateparse import parse_datetime
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from caef.commun.api import VueLectureMetier
from caef.commun.services import jour_reel
from caef.commun.vues import Serialiseur, champ, date_, donnees, exporter, ref, serialiseur_pour
from caef.habilitations.services import verifier

from . import services
from .models import (Inventaire, LigneInventaire, LigneVente, MouvementStock, PointDeVente, PrixProduit, Produit,
                     Reglement, Reversement, SessionCaisse, Vente)

PDV = "boutique.PointDeVente"
CENTRE_PDV = "point_de_vente__centre"


class SerialiseurVente(Serialiseur):
    lignes = serialiseur_pour(LigneVente)(many=True, read_only=True)
    reglements = serialiseur_pour(Reglement)(many=True, read_only=True)
    numero_complet = serializers.CharField(read_only=True)

    class Meta:
        model = Vente
        fields = "__all__"


class VuePointsDeVente(VueLectureMetier):
    objet = "produit"
    queryset = PointDeVente.objects.filter(actif=True)
    serializer_class = serialiseur_pour(PointDeVente)

    @action(detail=True, methods=["get"], url_path="tableau-de-bord")
    def tableau_de_bord(self, request, pk=None):
        pdv = ref(PDV, pk)
        verifier(request.user, "tdb_boutique", "L", centre=pdv.centre_id)
        jour = jour_reel()
        debut = date_(request.query_params, "debut", False) or jour.replace(day=1)
        fin = date_(request.query_params, "fin", False) or jour
        return Response(services.volet_boutique(pdv, debut, fin))

    @action(detail=True, methods=["get"], url_path="montant-du")
    def montant_du(self, request, pk=None):
        pdv = self.get_object()
        verifier(request.user, "reversement_preparation", "L", centre=pdv.centre_id)
        p = request.query_params
        beneficiaire = ref("beneficiaires.Beneficiaire", p.get("beneficiaire"), False)
        groupement = p.get("groupement", "")
        return Response({
            "montant_du": services.montant_du(pdv, beneficiaire=beneficiaire, groupement=groupement,
                                              debut=date_(p, "debut", False), fin=date_(p, "fin", False)),
            "solde_restant_du": services.solde_restant_du(pdv, beneficiaire=beneficiaire, groupement=groupement)})


class VueProduits(VueLectureMetier):
    objet = "produit"
    champ_centre = CENTRE_PDV
    queryset = Produit.objects.select_related("point_de_vente")
    serializer_class = serialiseur_pour(Produit)

    def queryset_base(self):
        qs = super().queryset_base()
        p = self.request.query_params
        if p.get("point_de_vente"):
            qs = qs.filter(point_de_vente=p["point_de_vente"])
        if p.get("actif"):
            qs = qs.filter(actif=p["actif"] in ("1", "true"))
        return qs

    def create(self, request):
        d = request.data
        p = services.creer_produit(
            request.user, ref(PDV, champ(d, "point_de_vente")), nom=champ(d, "nom"),
            categorie=ref("referentiels.ReferentielValeur", champ(d, "categorie")), unite=champ(d, "unite"),
            origine=champ(d, "origine"),
            **donnees(d, ("beneficiaire_deposante", "groupement", "session_origine", "formation_origine",
                          "seuil_alerte", "prix"),
                      references={"beneficiaire_deposante": "beneficiaires.Beneficiaire",
                                  "session_origine": "formations.SessionFormation",
                                  "formation_origine": "formations.Formation"}))
        return Response(self.get_serializer(p).data, status=201)

    @action(detail=True, methods=["get", "post"])
    def prix(self, request, pk=None):
        produit = self.get_object()
        if request.method == "POST":
            services.definir_prix(request.user, produit, champ(request.data, "prix"),
                                  date_(request.data, "date_debut"))
        return Response(serialiseur_pour(PrixProduit)(produit.prix.order_by("-date_debut"), many=True).data)

    @action(detail=True, methods=["post"])
    def entree(self, request, pk=None):
        d = request.data
        m = services.entrer_en_stock(request.user, self.get_object(), type=champ(d, "type"),
                                     quantite=champ(d, "quantite"),
                                     **donnees(d, ("emplacement", "part_centre_pct", "motif")))
        return Response(serialiseur_pour(MouvementStock)(m).data, status=201)

    @action(detail=True, methods=["post"])
    def sortie(self, request, pk=None):
        d = request.data
        m = services.sortir_du_stock(request.user, self.get_object(), type=champ(d, "type"),
                                     quantite=champ(d, "quantite"), motif=champ(d, "motif"),
                                     **donnees(d, ("emplacement",)))
        return Response(serialiseur_pour(MouvementStock)(m).data, status=201)

    @action(detail=True, methods=["post"])
    def transfert(self, request, pk=None):
        d = request.data
        r = services.transferer(request.user, self.get_object(), quantite=champ(d, "quantite"), vers=champ(d, "vers"),
                                motif=d.get("motif", ""))
        return Response(serialiseur_pour(MouvementStock)(r, many=isinstance(r, (list, tuple))).data, status=201)


class VueMouvements(VueLectureMetier):
    objet = "stock_entree"
    champ_centre = "produit__point_de_vente__centre"
    queryset = MouvementStock.objects.select_related("produit").order_by("-date_mouvement")
    serializer_class = serialiseur_pour(MouvementStock)

    def queryset_base(self):
        qs = super().queryset_base()
        for cle in ("produit", "type", "emplacement"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs


class VueVentes(VueLectureMetier):
    objet = "vente"
    champ_centre = CENTRE_PDV
    champ_propre = "vendeur"
    queryset = Vente.objects.select_related("point_de_vente").prefetch_related("lignes", "reglements")
    serializer_class = SerialiseurVente

    def queryset_base(self):
        qs = super().queryset_base().order_by("-date_heure_vente")
        p = self.request.query_params
        if p.get("date"):
            qs = qs.filter(date_heure_vente__date=p["date"])
        for cle in ("statut", "point_de_vente", "session_caisse"):
            if p.get(cle):
                qs = qs.filter(**{cle: p[cle]})
        return qs

    def create(self, request):
        """En ligne, le reçu prend la série web du centre ; le prix et le total viennent du serveur."""
        d = request.data
        lignes = [{"produit": ref("boutique.Produit", champ(l, "produit")), "quantite": champ(l, "quantite"),
                   "remise": l.get("remise") or 0, "motif_remise": l.get("motif_remise", "")}
                  for l in d.get("lignes") or []]
        reglements = [{**{k: r.get(k) for k in ("mode", "montant", "reference_externe", "identifiant_transaction",
                                                 "telephone") if r.get(k) is not None},
                       "paiement": ref("paiements.Paiement", r.get("paiement"), False)}
                      for r in d.get("reglements") or []]
        v = services.vendre(request.user, ref(PDV, champ(d, "point_de_vente")), lignes=lignes, reglements=reglements,
                            numero_recu_papier=d.get("numero_recu_papier") or None,
                            date_heure_vente=parse_datetime(d["date_heure_vente"]) if d.get("date_heure_vente")
                            else None, emplacement=d.get("emplacement", "boutique"))
        return Response(self.get_serializer(v).data, status=201)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        v = services.annuler_vente(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(v).data, status=201)

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Journal des ventes : reproduction exacte de la liste filtrée, journalisée (CA-BOU-13)."""
        qs = self.filter_queryset(self.get_queryset())
        return exporter(request.user, objet="export_boutique", centre=request.query_params.get("centre"), lignes=qs,
                        nom="journal-ventes", format_=request.query_params.get("format", "xlsx"), colonnes=[
                            ("Reçu", lambda v: v.numero_complet), ("Date", lambda v: v.date_heure_vente),
                            ("Statut", lambda v: v.get_statut_display()), ("Total", lambda v: v.total),
                            ("Vendeur", lambda v: v.vendeur_id), ("Mois corrigé", lambda v: v.mois_corrige or "")])


class VueCaisses(VueLectureMetier):
    objet = "caisse"
    champ_centre = CENTRE_PDV
    queryset = SessionCaisse.objects.select_related("point_de_vente").order_by("-date")
    serializer_class = serialiseur_pour(SessionCaisse)

    def create(self, request):
        d = request.data
        s = services.ouvrir_caisse(request.user, ref(PDV, champ(d, "point_de_vente")),
                                   fond_de_caisse=champ(d, "fond_de_caisse"))
        return Response(self.get_serializer(s).data, status=201)

    @action(detail=True, methods=["get"])
    def theoriques(self, request, pk=None):
        s = self.get_object()
        return Response({"montants_theoriques": services.montants_theoriques(s),
                         "appareils_non_synchronises": services.appareils_non_synchronises(s.point_de_vente, s.date)})

    @action(detail=True, methods=["post"])
    def compter(self, request, pk=None):
        d = request.data
        s = services.compter_caisse(request.user, self.get_object(), montants_comptes=champ(d, "montants_comptes"),
                                    motif_ecart=d.get("motif_ecart", ""),
                                    recus_papier_utilises=d.get("recus_papier_utilises") or (),
                                    derogation_appareils=bool(d.get("derogation_appareils")))
        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(services.valider_caisse(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def renvoyer(self, request, pk=None):
        s = services.renvoyer_caisse(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(s).data)


class SerialiseurInventaire(Serialiseur):
    lignes = serialiseur_pour(LigneInventaire)(many=True, read_only=True)

    class Meta:
        model = Inventaire
        fields = "__all__"


class VueInventaires(VueLectureMetier):
    objet = "inventaire_comptage"
    champ_centre = CENTRE_PDV
    queryset = Inventaire.objects.prefetch_related("lignes").order_by("-date_inventaire")
    serializer_class = SerialiseurInventaire

    def create(self, request):
        inv = services.ouvrir_inventaire(request.user, ref(PDV, champ(request.data, "point_de_vente")))
        return Response(self.get_serializer(inv).data, status=201)

    @action(detail=True, methods=["post"])
    def comptage(self, request, pk=None):
        inv = services.terminer_comptage(request.user, self.get_object(), champ(request.data, "comptages"))
        return Response(self.get_serializer(inv).data)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(services.valider_inventaire(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def recompter(self, request, pk=None):
        inv = services.faire_recompter(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(inv).data)


class VueReversements(VueLectureMetier):
    objet = "reversement_preparation"
    champ_centre = CENTRE_PDV
    queryset = Reversement.objects.select_related("point_de_vente")
    serializer_class = serialiseur_pour(Reversement)

    def create(self, request):
        d = request.data
        r = services.preparer_reversement(
            request.user, ref(PDV, champ(d, "point_de_vente")), periode_debut=date_(d, "periode_debut"),
            periode_fin=date_(d, "periode_fin"), montant_reverse=champ(d, "montant_reverse"),
            beneficiaire=ref("beneficiaires.Beneficiaire", d.get("beneficiaire"), False),
            groupement=d.get("groupement", ""))
        return Response(self.get_serializer(r).data, status=201)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(services.valider_reversement(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def payer(self, request, pk=None):
        d = request.data
        r = services.payer_reversement(request.user, self.get_object(), date_paiement=date_(d, "date_paiement"),
                                       mode=champ(d, "mode"),
                                       piece_justificative=ref("documents.Document", champ(d, "piece_justificative")))
        return Response(self.get_serializer(r).data)
