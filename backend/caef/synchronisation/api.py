"""Appareils, envoi des opérations hors ligne, réception des changements et file « À résoudre »
(E-OFF-01 à 03, DAT § 4.4). L'appareil propose, le serveur décide."""

from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from caef.commun.api import VueLectureMetier, q_perimetre
from caef.commun.exceptions import AccesRefuse, RegleMetier
from caef.commun.vues import champ, ref, serialiseur_pour
from caef.habilitations.services import verifier

from . import moteur, services
from .models import Appareil, ConflitSynchronisation, OperationSynchronisation, ResultatOperation


def _appareil_du_jeton(request):
    jeton = getattr(request, "auth", None)
    if not getattr(jeton, "est_jeton_appareil", False):
        raise AccesRefuse("La synchronisation se fait avec le jeton de l'appareil enrôlé.", objet="appareil",
                          action="C", code="jeton_appareil_requis")
    return jeton.appareil


class VueAppareils(VueLectureMetier):
    objet = "appareil"
    queryset = Appareil.objects.select_related("centre", "point_de_vente")
    serializer_class = serialiseur_pour(Appareil)

    def create(self, request):
        d = request.data
        a = services.enroler(request.user, centre=ref("referentiels.Centre", champ(d, "centre")),
                             libelle=champ(d, "libelle"),
                             utilisateur_principal=ref("identite.Utilisateur", d.get("utilisateur_principal"), False),
                             point_de_vente=ref("boutique.PointDeVente", d.get("point_de_vente"), False),
                             serie_recu=d.get("serie_recu") or None)
        return Response(self.get_serializer(a).data, status=201)

    @action(detail=True, methods=["post"])
    def revoquer(self, request, pk=None):
        a = services.revoquer(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(a).data)

    @action(detail=True, methods=["post"])
    def jeton(self, request, pk=None):
        """Délivré après une connexion en ligne complète ; jamais à partir d'un autre jeton d'appareil."""
        a = Appareil.objects.filter(pk=pk).first()
        if a is None:
            raise RegleMetier("Appareil introuvable.")
        return Response(services.delivrer_jeton(request.user, a))


class Operations(APIView):
    accepte_jeton_appareil = True

    def post(self, request):
        appareil = _appareil_du_jeton(request)
        d = request.data
        operations = d.get("operations")
        if not isinstance(operations, list):
            raise RegleMetier("Liste d'opérations attendue.")
        return Response(moteur.appliquer_lot(request.user, appareil, operations,
                                             horloge_appareil=d.get("horloge_appareil"),
                                             plus_ancienne_en_attente=d.get("plus_ancienne_en_attente")))


class Changements(APIView):
    accepte_jeton_appareil = True

    def get(self, request):
        appareil = _appareil_du_jeton(request)
        try:
            curseur = int(request.query_params.get("curseur") or 0)
        except ValueError:
            raise RegleMetier("Curseur invalide.")
        return Response(moteur.changements(request.user, appareil, curseur))


class MesRejets(APIView):
    """Ce qui a été refusé au retour de connexion, avec le motif (OFF-05)."""

    accepte_jeton_appareil = True

    def get(self, request):
        qs = OperationSynchronisation.objects.filter(utilisateur=request.user).exclude(
            resultat=ResultatOperation.APPLIQUEE).order_by("-recu_le")[:200]
        return Response([{"id": str(o.pk), "type": o.type_operation, "resultat": o.resultat,
                          "motif": o.motif_rejet, "horodatage_appareil": o.horodatage_appareil,
                          "recu_le": o.recu_le} for o in qs])


class VueConflits(VueLectureMetier):
    """Conflits de champ (RC, RA) et écritures tardives (CPT), chacun selon ses droits."""

    objet = "conflit_synchronisation"
    queryset = ConflitSynchronisation.objects.select_related("operation")
    serializer_class = serialiseur_pour(ConflitSynchronisation)

    def get_queryset(self):
        u = self.request.user
        q_conflits = q_perimetre(u, "conflit_synchronisation")
        q_tardives = q_perimetre(u, "ecriture_tardive")
        if q_conflits is None and q_tardives is None:
            verifier(u, "conflit_synchronisation", "L")
        tardive = Q(operation__resultat=ResultatOperation.ECRITURE_TARDIVE)
        q = Q(pk__in=[])
        if q_conflits is not None:
            q |= ~tardive & q_conflits
        if q_tardives is not None:
            q |= tardive & q_tardives
        qs = ConflitSynchronisation.objects.select_related("operation").filter(q)
        if self.request.query_params.get("statut"):
            qs = qs.filter(statut=self.request.query_params["statut"])
        return qs

    @action(detail=True, methods=["post"])
    def resoudre(self, request, pk=None):
        c = services.resoudre_conflit(request.user, self.get_object(), champ(request.data, "decision"),
                                      request.data.get("motif", ""))
        return Response(self.get_serializer(c).data)

    @action(detail=True, methods=["post"])
    def regulariser(self, request, pk=None):
        reponse = services.regulariser_ecriture_tardive(request.user, self.get_object(), champ(request.data, "motif"))
        return Response({"conflit": self.get_serializer(self.get_object()).data, "reponse": reponse})
