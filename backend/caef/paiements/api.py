"""Encaissements, Mobile Money, notifications de la passerelle, affectation, rapprochement et
remboursements (E-PAY-03 à 08). Le montant fait foi depuis l'opérateur, jamais depuis le client ;
aucun code secret de la payeuse n'est demandé ni transmis."""

import csv
import io

from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from caef.commun.api import VueLectureMetier
from caef.commun.exceptions import AccesRefuse, RegleMetier
from caef.commun.services import jour_reel
from caef.commun.vues import champ, date_, exporter, ref, refs, serialiseur_pour
from caef.habilitations.services import verifier
from caef.pilotage.cloture import bornes

from . import services
from .models import AffectationPaiement, LigneReleveOperateur, Paiement, Remboursement

CENTRE = "referentiels.Centre"
SerialiseurPaiement = serialiseur_pour(Paiement)


class VuePaiements(VueLectureMetier):
    objet = "encaissement"
    queryset = Paiement.objects.all().order_by("-cree_le")
    serializer_class = SerialiseurPaiement

    def queryset_base(self):
        qs = super().queryset_base()
        p = self.request.query_params
        for cle in ("statut", "canal", "identifiant_transaction", "reference_echeance"):
            if p.get(cle):
                qs = qs.filter(**{cle: p[cle]})
        return qs

    @action(detail=False, methods=["post"])
    def especes(self, request):
        d = request.data
        p = services.encaisser_especes(request.user, ref(CENTRE, champ(d, "centre")), montant=champ(d, "montant"),
                                       echeances=refs("facturation.Echeance", d.get("echeances")),
                                       repartition=d.get("repartition"))
        return Response(self.get_serializer(p).data, status=201)

    @action(detail=False, methods=["post"])
    def demander(self, request):
        """Parcours A : demande envoyée au téléphone de la payeuse, qui valide chez son opérateur."""
        d = request.data
        p = services.demander_paiement(request.user, ref(CENTRE, champ(d, "centre")),
                                       telephone_payeuse=champ(d, "telephone_payeuse"),
                                       echeances=refs("facturation.Echeance", d.get("echeances")),
                                       montant=d.get("montant"), fournisseur=d.get("fournisseur"))
        return Response(self.get_serializer(p).data, status=201)

    @action(detail=False, methods=["post"])
    def declarer(self, request):
        """Parcours C : identifiant de transaction lu sur le SMS ; « Déclaré » tant que l'opérateur n'a pas confirmé."""
        d = request.data
        p = services.declarer_mobile_money(request.user, ref(CENTRE, champ(d, "centre")),
                                           identifiant_transaction=champ(d, "identifiant_transaction"),
                                           montant_declare=champ(d, "montant_declare"),
                                           echeances=refs("facturation.Echeance", d.get("echeances")),
                                           telephone=d.get("telephone", ""))
        return Response(self.get_serializer(p).data, status=201)

    @action(detail=False, methods=["get"], url_path="a-affecter")
    def a_affecter(self, request):
        centre = ref(CENTRE, champ(request.query_params, "centre"))
        verifier(request.user, "paiement_a_affecter", "L", centre=centre)
        qs = services.paiements_a_affecter(centre.pk)
        return Response([{**self.get_serializer(p).data, "disponible": services.disponible(p)} for p in qs])

    @action(detail=True, methods=["post"])
    def affecter(self, request, pk=None):
        d = request.data
        a = services.affecter(request.user, self.get_object(), ref("facturation.Echeance", champ(d, "echeance")),
                              champ(d, "montant"), champ(d, "motif"))
        return Response(serialiseur_pour(AffectationPaiement)(a).data, status=201)

    @action(detail=True, methods=["post"], url_path="confirmer-manuellement")
    def confirmer_manuellement(self, request, pk=None):
        d = request.data
        p = services.confirmer_manuellement(request.user, self.get_object(),
                                            montant_operateur=champ(d, "montant_operateur"), motif=champ(d, "motif"),
                                            piece_justificative=ref("documents.Document",
                                                                    champ(d, "piece_justificative")))
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["post"])
    def remboursements(self, request, pk=None):
        d = request.data
        r = services.demander_remboursement(request.user, self.get_object(), montant=champ(d, "montant"),
                                            motif=champ(d, "motif"),
                                            echeance=ref("facturation.Echeance", d.get("echeance"), False))
        return Response(serialiseur_pour(Remboursement)(r).data, status=201)

    @action(detail=False, methods=["get"])
    def totaux(self, request):
        p = request.query_params
        centre = ref(CENTRE, champ(p, "centre"))
        verifier(request.user, "encaissement", "L", centre=centre)
        debut, fin = bornes(p.get("mois") or jour_reel().strftime("%Y-%m"))
        return Response(services.totaux_mois(centre.pk, debut, fin))

    @action(detail=False, methods=["get"])
    def export(self, request):
        qs = self.filter_queryset(self.get_queryset())
        return exporter(request.user, objet="export_paiements", centre=request.query_params.get("centre"), lignes=qs,
                        nom="paiements", format_=request.query_params.get("format", "xlsx"), colonnes=[
                            ("Reçu", lambda p: f"{p.serie_recu}-{p.numero_recu}" if p.numero_recu else None),
                            ("Canal", lambda p: p.get_canal_display()), ("Statut", lambda p: p.get_statut_display()),
                            ("Identifiant opérateur", lambda p: p.identifiant_transaction or None),
                            ("Brut", lambda p: p.montant_confirme), ("Commission", lambda p: p.commission),
                            ("Net", lambda p: p.montant_net), ("Confirmé le", lambda p: p.confirme_le)])


class NotificationPasserelle(APIView):
    """Point d'entrée des notifications de l'opérateur : sans session, authentifié par la signature.
    Signature invalide : 401, journalisée, aucun changement. Doublon : 200 sans effet."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = []

    def post(self, request, fournisseur):
        entetes = {k: v for k, v in request.headers.items()}
        try:
            services.recevoir_notification(fournisseur, request.body, entetes)
        except AccesRefuse:
            return Response({"code": "signature_invalide"}, status=401)
        except RegleMetier as e:
            return Response({"code": e.code, "message": e.message}, status=400)
        return Response({"ok": True})


class VueReleves(VueLectureMetier):
    """Rapprochement opérateur : import d'un relevé (CSV ou JSON) et motifs des écarts (RG-PAY-11)."""

    objet = "rapprochement_operateur"
    queryset = LigneReleveOperateur.objects.all().order_by("-date_releve")
    serializer_class = serialiseur_pour(LigneReleveOperateur)
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def queryset_base(self):
        qs = super().queryset_base()
        for cle in ("statut_rapprochement", "date_releve", "fournisseur"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs

    def create(self, request):
        d = request.data
        centre = ref(CENTRE, champ(d, "centre"))
        verifier(request.user, "rapprochement_operateur", "M", centre=centre)
        fichier = request.FILES.get("fichier")
        if fichier is not None:
            texte = fichier.read().decode("utf-8-sig")
            separateur = ";" if texte.count(";") >= texte.count(",") else ","
            lignes = [{"identifiant": l["identifiant"], "montant": l["montant"], "commission": l.get("commission") or 0}
                      for l in csv.DictReader(io.StringIO(texte), delimiter=separateur)]
        else:
            lignes = d.get("lignes") or []
        if not lignes:
            raise RegleMetier("Le relevé est vide.")
        return Response(services.importer_releve(centre, champ(d, "fournisseur"), date_(d, "jour"), lignes),
                        status=201)

    @action(detail=True, methods=["post"])
    def motiver(self, request, pk=None):
        l = services.motiver_ecart(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(l).data)


class VueRemboursements(VueLectureMetier):
    objet = "remboursement"
    champ_centre = "paiement__centre"
    queryset = Remboursement.objects.select_related("paiement")
    serializer_class = serialiseur_pour(Remboursement)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        r = services.valider_remboursement(request.user, self.get_object(),
                                           request.data.get("valider") not in (False, "false"),
                                           request.data.get("motif", ""))
        return Response(self.get_serializer(r).data)

    @action(detail=True, methods=["post"])
    def executer(self, request, pk=None):
        r = services.executer_remboursement(request.user, self.get_object(),
                                            ref("documents.Document", request.data.get("piece_justificative"), False))
        return Response(self.get_serializer(r).data)
