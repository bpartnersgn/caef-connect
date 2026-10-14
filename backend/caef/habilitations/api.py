"""Administration : centres, référentiels, périodes, affectations, intérims, modules, journal,
notifications (SFD § 3, E-ADM)."""

from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from caef.commun.api import VueLectureMetier, VueMetier
from caef.commun.exceptions import RegleMetier
from caef.commun.vues import champ, date_, ref, serialiseur_pour
from caef.journal.models import JournalAudit
from caef.notifications.models import Notification
from caef.referentiels.models import Centre, Periode, ReferentielValeur, ZoneTerritoriale

from . import gestion
from .matrice import matrice
from .models import Affectation, InterimResponsable, ModuleCentre
from .services import modules_actifs, verifier


class VueCentres(VueLectureMetier):
    objet = "centre"
    queryset = Centre.objects.select_related("zone_territoriale")
    champ_centre = "pk"
    serializer_class = serialiseur_pour(Centre)

    @action(detail=True, methods=["get"])
    def modules(self, request, pk=None):
        c = self.get_object()
        return Response({"centre": str(c.pk), "modules_actifs": modules_actifs(c.pk)})


class VueReferentiels(VueLectureMetier):
    objet = "referentiel"
    queryset = ReferentielValeur.objects.filter(actif=True)
    champ_centre = None
    serializer_class = serialiseur_pour(ReferentielValeur, ["id", "referentiel", "code", "libelle", "ordre", "actif"])

    def queryset_base(self):
        qs = super().queryset_base()
        if self.request.query_params.get("referentiel"):
            qs = qs.filter(referentiel=self.request.query_params["referentiel"])
        return qs


class VueZones(VueLectureMetier):
    objet = "referentiel"
    queryset = ZoneTerritoriale.objects.all()
    champ_centre = None
    serializer_class = serialiseur_pour(ZoneTerritoriale, ["id", "niveau", "nom", "code", "parent"])


class VuePeriodes(VueLectureMetier):
    objet = "periode"
    queryset = Periode.objects.all()
    champ_centre = None
    serializer_class = serialiseur_pour(Periode, ["id", "type", "libelle", "date_debut", "date_fin", "statut"])


class VueAffectations(VueLectureMetier):
    objet = "utilisateur"
    queryset = Affectation.objects.select_related("role", "centre", "utilisateur")
    serializer_class = serialiseur_pour(Affectation, ["id", "utilisateur", "role", "centre", "national",
                                                      "date_debut", "date_fin", "motif"])

    def create(self, request):
        d = request.data
        aff = gestion.affecter(request.user, utilisateur=ref("identite.Utilisateur", champ(d, "utilisateur")),
                               role=champ(d, "role"), centre=ref("referentiels.Centre", d.get("centre"), False),
                               national=bool(d.get("national")), date_debut=date_(d, "date_debut", False),
                               date_fin=date_(d, "date_fin", False), motif=champ(d, "motif"))
        return Response(self.get_serializer(aff).data, status=201)

    @action(detail=True, methods=["post"])
    def retirer(self, request, pk=None):
        aff = self.get_object()
        gestion.retirer_affectation(request.user, aff, champ(request.data, "motif"))
        return Response(self.get_serializer(aff).data)


class VueInterims(VueLectureMetier):
    objet = "interim"
    queryset = InterimResponsable.objects.all()
    serializer_class = serialiseur_pour(InterimResponsable)

    def create(self, request):
        d = request.data
        i = gestion.declarer_interim(request.user, centre=ref("referentiels.Centre", champ(d, "centre")),
                                     adjoint=ref("identite.Utilisateur", champ(d, "adjoint")),
                                     date_debut=date_(d, "date_debut"), date_fin=date_(d, "date_fin"),
                                     motif=champ(d, "motif"))
        return Response(self.get_serializer(i).data, status=201)

    @action(detail=True, methods=["post"])
    def interrompre(self, request, pk=None):
        i = gestion.interrompre_interim(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(i).data)


class VueModulesCentre(VueLectureMetier):
    """E-ADM-10 : saisi par l'ADM sur décision de la DG, validé par la DG (RG-ADM-17 à 20)."""

    objet = "module_centre"
    queryset = ModuleCentre.objects.all()
    serializer_class = serialiseur_pour(ModuleCentre)

    def create(self, request):
        d = request.data
        ligne = gestion.saisir_changement_module(
            request.user, centre=ref("referentiels.Centre", champ(d, "centre")), module=champ(d, "module"),
            statut=champ(d, "statut"), date_effet=date_(d, "date_effet"),
            decision_reference=champ(d, "decision_reference"), decision_date=date_(d, "decision_date"),
            motif=champ(d, "motif"))
        return Response(self.get_serializer(ligne).data, status=201)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(gestion.valider_changement_module(request.user, self.get_object())).data)

    @action(detail=False, methods=["get"], url_path="operations-en-cours")
    def operations(self, request):
        centre = ref("referentiels.Centre", request.query_params.get("centre"))
        verifier(request.user, "module_centre", "L", centre=centre)
        return Response({"blocages": gestion.operations_en_cours(centre.pk, request.query_params.get("module"))})


class VueMatrice(VueMetier):
    """La Matrice en vigueur, en lecture (E-ADM-04)."""

    objet = "role_permission"
    champ_centre = None

    def list(self, request):
        verifier(request.user, "role_permission", "L")
        m = matrice()
        return Response({"version": m.version, "roles": {c: {"titre": r.titre, "hors_ligne": r.hors_ligne,
                                                             "double_auth": r.double_auth} for c, r in m.roles.items()},
                         "objets": {c: {"libelle": o.libelle, "module": o.module, "droits": {
                             r: {a: {"perimetre": d.perimetre, "condition": d.condition} for a, d in actions.items()}
                             for r, actions in o.droits.items()}}
                                    for c, o in m.objets.items()}})


class VueJournal(VueLectureMetier):
    """Journal d'activité, en lecture seule (SEC-04)."""

    objet = "journal_audit"
    queryset = JournalAudit.objects.all()
    serializer_class = serialiseur_pour(JournalAudit)

    def queryset_base(self):
        qs = super().queryset_base()
        p = self.request.query_params
        for cle in ("action", "objet_type", "objet_id", "utilisateur"):
            if p.get(cle):
                qs = qs.filter(**{cle: p[cle]})
        return qs


class VueNotifications(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serialiseur_pour(Notification, ["id", "type_evenement", "objet_type", "objet_id", "message",
                                                      "cree_le", "lue_le"])

    def get_queryset(self):
        qs = Notification.objects.filter(destinataire=self.request.user).order_by("-cree_le")
        if self.request.query_params.get("non_lues"):
            qs = qs.filter(lue_le__isnull=True)
        return qs

    @action(detail=True, methods=["post"])
    def lue(self, request, pk=None):
        n = self.get_queryset().filter(pk=pk).first()
        if n is None:
            raise RegleMetier("Notification introuvable.")
        n.lue_le = timezone.now()
        n.save(update_fields=["lue_le"])
        return Response(status=204)
