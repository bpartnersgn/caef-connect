"""Bénéficiaires, candidatures, doublons, transferts et fusions (E-BEN-01 à 07)."""

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from caef.commun.api import VueLectureMetier
from caef.commun.vues import Serialiseur, champ, date_, exporter, ref, serialiseur_pour
from caef.habilitations.services import decider

from . import services
from .models import Beneficiaire, Candidature, Fusion, PaireDoublon, Transfert

CHAMPS_MINIMAUX = ("id", "code", "nom", "prenoms")


class SerialiseurBeneficiaire(Serialiseur):
    """Le formateur ne voit que nom, prénom et code de ses inscrites (RG-FOR-04)."""

    annee_naissance_calculee = serializers.SerializerMethodField()

    class Meta:
        model = Beneficiaire
        exclude = ("nom_normalise", "cle_phonetique")

    def get_annee_naissance_calculee(self, b):
        return b.annee

    def to_representation(self, b):
        donnees = super().to_representation(b)
        u = self.context["request"].user
        d = decider(u, "beneficiaire", "L", centre=b.centre_rattachement_id, nominatif=True)
        if d.perimetre == "s":
            return {k: donnees[k] for k in CHAMPS_MINIMAUX}
        return donnees


def _identite(d):
    identite = {k: v for k, v in d.items() if k in services.CHAMPS_MODIFIABLES or k in Beneficiaire.CHAMPS_RESTREINTS}
    for k in ("date_naissance", "consentement_date"):
        if identite.get(k):
            identite[k] = date_(identite, k)
    for k, chemin in (("zone_residence", "referentiels.ZoneTerritoriale"), ("niveau_etudes", "referentiels.ReferentielValeur"),
                      ("situation_entree", "referentiels.ReferentielValeur"),
                      ("piece_identite_type", "referentiels.ReferentielValeur")):
        if k in identite:
            identite[k] = ref(chemin, identite[k], False)
    return identite


class VueBeneficiaires(VueLectureMetier):
    objet = "beneficiaire"
    nominatif = True
    champ_centre = "centre_rattachement"
    champ_session = "inscriptions__session"
    queryset = Beneficiaire.objects.exclude(statut="fusionne").select_related("centre_rattachement")
    serializer_class = SerialiseurBeneficiaire

    def queryset_base(self):
        qs = super().queryset_base()
        p = self.request.query_params
        if p.get("statut"):
            qs = qs.filter(statut=p["statut"])
        if p.get("q"):
            from .phonetique import cle_phonetique

            qs = qs.filter(cle_phonetique__contains=cle_phonetique(p["q"]).split(" ")[0]) | qs.filter(code=p["q"])
        return qs

    def partial_update(self, request, pk=None):
        b = self.get_object()
        d = dict(request.data)
        version = d.pop("version", None)
        motif = d.pop("motif", "")
        services.modifier_beneficiaire(request.user, b, version=version, motif=motif, **_identite(d))
        return Response(self.get_serializer(b).data)

    @action(detail=False, methods=["post"], url_path="recherche-reseau")
    def recherche_reseau(self, request):
        d = request.data
        return Response(services.recherche_reseau(
            request.user, nom=champ(d, "nom"), prenoms=champ(d, "prenoms"), date_naissance=date_(d, "date_naissance", False),
            annee_naissance=d.get("annee_naissance"), zone=d.get("zone_residence"), telephone=d.get("telephone", "")))

    @action(detail=True, methods=["get"], url_path="donnees-restreintes")
    def donnees_restreintes(self, request, pk=None):
        return Response(services.lire_donnees_restreintes(request.user, self.get_object()))

    @action(detail=True, methods=["post"])
    def cloturer(self, request, pk=None):
        b = services.cloturer_dossier(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(b).data)

    @action(detail=True, methods=["get"])
    def parcours(self, request, pk=None):
        """E-BEN-04 : candidatures, inscriptions, statuts de participation, attestations."""
        b = self.get_object()
        return Response({
            "candidatures": list(b.candidatures.values("id", "code", "formation__intitule", "statut", "date_reception")),
            "inscriptions": list(b.inscriptions.values("id", "session__code", "session__formation__intitule",
                                                       "statut_participation", "date_inscription", "taux_presence",
                                                       "attestation__numero", "attestation__statut")),
        })

    @action(detail=False, methods=["get"])
    def export(self, request):
        qs = self.filter_queryset(self.get_queryset())
        centre = request.query_params.get("centre")
        return exporter(request.user, objet="export_nominatif", centre=centre, lignes=qs, nom="beneficiaires",
                        format_=request.query_params.get("format", "xlsx"), colonnes=[
                            ("Code", lambda b: b.code), ("Nom", lambda b: b.nom), ("Prénoms", lambda b: b.prenoms),
                            ("Année de naissance", lambda b: b.annee), ("Centre", lambda b: b.centre_rattachement.code),
                            ("Statut", lambda b: b.get_statut_display()), ("Complétude", lambda b: b.completude)])


class VueCandidatures(VueLectureMetier):
    objet = "candidature"
    nominatif = True
    queryset = Candidature.objects.select_related("beneficiaire", "formation")
    serializer_class = serialiseur_pour(Candidature)

    def queryset_base(self):
        qs = super().queryset_base()
        for cle in ("statut", "formation", "beneficiaire"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs

    def create(self, request):
        d = request.data
        cand = services.creer_candidature(
            request.user, centre=ref("referentiels.Centre", champ(d, "centre")),
            formation=ref("formations.Formation", champ(d, "formation")), date_reception=date_(d, "date_reception", False),
            dossier_existant=ref("beneficiaires.Beneficiaire", d.get("beneficiaire"), False),
            identite=_identite(d["identite"]) if d.get("identite") else None,
            decision_doublon=d.get("decision_doublon"), commentaire_doublon=d.get("commentaire_doublon", ""))
        return Response(self.get_serializer(cand).data, status=201)

    def _transition(self, fonction, *args, **kwargs):
        cand = fonction(self.request.user, self.get_object(), *args, **kwargs)
        return Response(self.get_serializer(cand).data)

    @action(detail=True, methods=["post"])
    def soumettre(self, request, pk=None):
        return self._transition(services.soumettre_candidature)

    @action(detail=True, methods=["post"], url_path="demander-complement")
    def demander_complement(self, request, pk=None):
        return self._transition(services.demander_complement, ref("referentiels.ReferentielValeur", request.data.get("motif")),
                                request.data.get("commentaire", ""))

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return self._transition(services.valider_candidature)

    @action(detail=True, methods=["post"])
    def rejeter(self, request, pk=None):
        return self._transition(services.rejeter_candidature, ref("referentiels.ReferentielValeur", request.data.get("motif")),
                                champ(request.data, "commentaire"))

    @action(detail=True, methods=["post"], url_path="mettre-en-attente")
    def mettre_en_attente(self, request, pk=None):
        return self._transition(services.placer_en_attente,
                                ref("formations.SessionFormation", request.data.get("session"), False))

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        return self._transition(services.annuler_candidature, champ(request.data, "commentaire"),
                                ref("referentiels.ReferentielValeur", request.data.get("motif"), False))

    @action(detail=True, methods=["post"], url_path="lever-doute-doublon")
    def lever_doute(self, request, pk=None):
        return self._transition(services.lever_doute_doublon,
                                dossier_existant=ref("beneficiaires.Beneficiaire", request.data.get("dossier_existant"), False),
                                commentaire=champ(request.data, "commentaire"))


class VueTransferts(VueLectureMetier):
    objet = "transfert"
    nominatif = True
    champ_centre = "centre_origine"
    queryset = Transfert.objects.all()
    serializer_class = serialiseur_pour(Transfert)

    def get_queryset(self):
        from caef.commun.api import q_perimetre

        q1 = q_perimetre(self.request.user, "transfert", champ_centre="centre_origine", nominatif=True)
        q2 = q_perimetre(self.request.user, "transfert", champ_centre="centre_accueil", nominatif=True)
        if q1 is None:
            return super().get_queryset()
        return Transfert.objects.filter(q1 | q2)

    def create(self, request):
        d = request.data
        t = services.demander_transfert(request.user, ref("beneficiaires.Beneficiaire", champ(d, "beneficiaire")),
                                        ref("referentiels.Centre", champ(d, "centre_accueil")), champ(d, "motif"))
        return Response(self.get_serializer(t).data, status=201)

    @action(detail=True, methods=["post"])
    def decider(self, request, pk=None):
        t = services.decider_transfert(request.user, self.get_object(), bool(request.data.get("accepte")),
                                       request.data.get("motif", ""))
        return Response(self.get_serializer(t).data)


class VuePairesDoublons(VueLectureMetier):
    """E-BEN-05 : paires suspectes, score, champs concordants."""

    objet = "beneficiaire"  # la Matrice ne donne que « V » sur la fusion : la liste suit le dossier
    nominatif = True
    champ_centre = "beneficiaire_a__centre_rattachement"
    queryset = PaireDoublon.objects.filter(statut="a_traiter").select_related("beneficiaire_a", "beneficiaire_b")
    serializer_class = serialiseur_pour(PaireDoublon)

    def get_queryset(self):
        from caef.commun.api import q_perimetre

        qs = super().get_queryset()
        q = q_perimetre(self.request.user, "beneficiaire", champ_centre="beneficiaire_b__centre_rattachement",
                        nominatif=True)
        return qs | self.queryset.filter(q) if q is not None else qs

    @action(detail=True, methods=["post"])
    def distinctes(self, request, pk=None):
        p = services.declarer_paire_distincte(request.user, self.get_object(), champ(request.data, "commentaire"))
        return Response(self.get_serializer(p).data)

    @action(detail=True, methods=["post"])
    def fusionner(self, request, pk=None):
        p = self.get_object()
        conserve = ref("beneficiaires.Beneficiaire", champ(request.data, "conserve"))
        absorbe = p.beneficiaire_b if conserve.pk == p.beneficiaire_a_id else p.beneficiaire_a
        f = services.fusionner(request.user, conserve, absorbe, request.data.get("choix") or {}, paire=p)
        return Response(serialiseur_pour(Fusion)(f).data, status=201)


class VueFusions(VueLectureMetier):
    objet = "beneficiaire"
    nominatif = True
    champ_centre = "conserve__centre_rattachement"
    queryset = Fusion.objects.all()
    serializer_class = serialiseur_pour(Fusion)

    def create(self, request):
        d = request.data
        f = services.fusionner(request.user, ref("beneficiaires.Beneficiaire", champ(d, "conserve")),
                               ref("beneficiaires.Beneficiaire", champ(d, "absorbe")), d.get("choix") or {})
        return Response(self.get_serializer(f).data, status=201)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        f = services.annuler_fusion(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(f).data)
