"""Services payants, tarifs, échéances, exonérations et situation d'une apprenante (E-PAY-01 à 03)."""

from rest_framework.decorators import action
from rest_framework.response import Response

from caef.beneficiaires.models import Beneficiaire
from caef.commun.api import VueLectureMetier, q_perimetre
from caef.commun.vues import champ, date_, ref, serialiseur_pour
from caef.habilitations.services import verifier

from . import services
from .models import Echeance, Exoneration, ServicePayant, TarifService


class VueServices(VueLectureMetier):
    objet = "service_tarif"
    queryset = ServicePayant.objects.all()
    serializer_class = serialiseur_pour(ServicePayant)

    def create(self, request):
        d = request.data
        s = services.creer_service(request.user, centre=ref("referentiels.Centre", champ(d, "centre")),
                                   code=champ(d, "code"), libelle=champ(d, "libelle"), nature=champ(d, "nature"),
                                   formation=ref("formations.Formation", d.get("formation"), False))
        return Response(self.get_serializer(s).data, status=201)

    @action(detail=True, methods=["get", "post"])
    def tarifs(self, request, pk=None):
        s = self.get_object()
        if request.method == "POST":
            d = request.data
            services.definir_tarif(request.user, s, montant=champ(d, "montant"), date_debut=date_(d, "date_debut"),
                                   decision_reference=champ(d, "decision_reference"),
                                   nombre_versements=int(d.get("nombre_versements") or 1),
                                   calendrier=d.get("calendrier"))
        return Response(serialiseur_pour(TarifService)(s.tarifs.order_by("-date_debut"), many=True).data)


class VueEcheances(VueLectureMetier):
    objet = "echeance"
    nominatif = True
    queryset = Echeance.objects.select_related("beneficiaire", "service_payant")
    serializer_class = serialiseur_pour(Echeance)

    def queryset_base(self):
        qs = super().queryset_base()
        p = self.request.query_params
        for cle in ("statut", "beneficiaire", "inscription", "reference_paiement"):
            if p.get(cle):
                qs = qs.filter(**{cle: p[cle]})
        return qs

    @action(detail=True, methods=["post"])
    def exonerations(self, request, pk=None):
        d = request.data
        ex = services.proposer_exoneration(
            request.user, self.get_object(), type=champ(d, "type"), montant=d.get("montant"),
            pourcentage=d.get("pourcentage"), motif=champ(d, "motif"),
            piece_justificative=ref("documents.Document", d.get("piece_justificative"), False),
            partenaire=ref("partenaires.Partenaire", d.get("partenaire"), False),
            programme=ref("conventions.Programme", d.get("programme"), False))
        return Response(serialiseur_pour(Exoneration)(ex).data, status=201)


class VueExonerations(VueLectureMetier):
    objet = "exoneration"
    nominatif = True
    champ_centre = "echeance__centre"
    queryset = Exoneration.objects.select_related("echeance")
    serializer_class = serialiseur_pour(Exoneration)

    @action(detail=True, methods=["post"])
    def decider(self, request, pk=None):
        ex = services.decider_exoneration(request.user, self.get_object(),
                                          request.data.get("valider") not in (False, "false", None),
                                          request.data.get("motif", ""))
        return Response(self.get_serializer(ex).data)


class VueSituation(VueLectureMetier):
    """E-PAY-02 : situation financière d'une apprenante, limitée aux centres du périmètre."""

    objet = "echeance"
    nominatif = True
    champ_centre = "centre_rattachement"
    queryset = Beneficiaire.objects.all()

    def get_queryset(self):
        q = q_perimetre(self.request.user, "echeance", champ_centre="echeances__centre", nominatif=True)
        if q is None:
            verifier(self.request.user, "echeance", "L", nominatif=True)
        return Beneficiaire.objects.filter(q).distinct()

    def retrieve(self, request, pk=None):
        from caef.habilitations.services import portee

        b = self.get_object()
        p = portee(request.user, "echeance", "L", nominatif=True)
        return Response(services.situation(b, None if p.national else list(p.centres)))

    def list(self, request):
        return Response(status=405)
