"""Catalogue, sessions, séances, inscriptions, présences, résultats et attestations (E-FOR-01 à 08)."""

from django.db.models import Q
from django.utils.dateparse import parse_time
from rest_framework.decorators import action
from rest_framework.response import Response

from caef.commun.api import VueLectureMetier, q_perimetre
from caef.commun.exceptions import AccesRefuse
from caef.commun.vues import champ, date_, exporter, ref, serialiseur_pour
from caef.habilitations.services import verifier

from . import services
from .models import Attestation, Evaluation, Formateur, Formation, Inscription, Presence, Seance, SessionFormation


class VueFormations(VueLectureMetier):
    """Catalogue national (tout le réseau) et formations propres aux centres du périmètre."""

    objet = "formation_centre"
    queryset = Formation.objects.filter(archive=False)
    serializer_class = serialiseur_pour(Formation)

    def get_queryset(self):
        u = self.request.user
        q_nat = q_perimetre(u, "formation_nationale", champ_centre=None,
                            champ_session="sessions", champ_propre=None)
        q_cen = q_perimetre(u, "formation_centre", champ_centre="centre", champ_session="sessions")
        if q_nat is None and q_cen is None:
            raise AccesRefuse("Accès refusé.", objet="formation_centre", action="L")
        q = Q(pk__in=[])
        if q_nat is not None:
            q |= Q(portee="nationale") & q_nat
        if q_cen is not None:
            q |= Q(portee="centre") & q_cen
        return Formation.objects.filter(archive=False).filter(q).distinct()

    def create(self, request):
        d = dict(request.data)
        nationale = d.get("portee") == "nationale"
        centre = ref("referentiels.Centre", d.get("centre"), not nationale)
        verifier(request.user, "formation_nationale" if nationale else "formation_centre", "C", centre=centre)
        from caef.commun.codes import code_simple
        from caef.journal.models import ActionJournal
        from caef.journal.services import instantane, journaliser

        f = Formation.objects.create(
            code=code_simple("FOR"), intitule=champ(d, "intitule"), portee="nationale" if nationale else "centre",
            centre=None if nationale else centre, categorie=ref("referentiels.ReferentielValeur", champ(d, "categorie")),
            objectifs=champ(d, "objectifs"), prerequis=d.get("prerequis", ""), contenu=d.get("contenu", ""),
            duree_heures=champ(d, "duree_heures"), seuil_presence_pct=d.get("seuil_presence_pct", 80),
            evaluation_requise=bool(d.get("evaluation_requise")), attestation_prevue=d.get("attestation_prevue", True),
            cree_par=request.user)
        journaliser(ActionJournal.CREATION, utilisateur=request.user, objet=f, centre=centre, apres=instantane(f))
        return Response(self.get_serializer(f).data, status=201)


class VueFormateurs(VueLectureMetier):
    objet = "formateur"
    champ_centre = "centres"
    champ_propre = "utilisateur"
    queryset = Formateur.objects.filter(archive=False)
    serializer_class = serialiseur_pour(Formateur)

    def get_queryset(self):
        return super().get_queryset().distinct()


class VueSessions(VueLectureMetier):
    objet = "session"
    champ_session = ""
    queryset = SessionFormation.objects.select_related("formation", "centre")
    serializer_class = serialiseur_pour(SessionFormation)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("mes_sessions"):
            qs = qs.filter(services.q_sessions_du_formateur(self.request.user, "")).distinct()
        if self.request.query_params.get("statut"):
            qs = qs.filter(statut=self.request.query_params["statut"])
        return qs

    def create(self, request):
        d = request.data
        s = services.creer_session(
            request.user, formation=ref("formations.Formation", champ(d, "formation")),
            centre=ref("referentiels.Centre", champ(d, "centre")), periode=ref("referentiels.Periode", champ(d, "periode")),
            date_debut=date_(d, "date_debut"), date_fin=date_(d, "date_fin"), lieu=d.get("lieu", ""),
            capacite=d.get("capacite"), formateur_principal=ref("formations.Formateur", d.get("formateur_principal"), False),
            programme=ref("conventions.Programme", d.get("programme"), False))
        return Response(self.get_serializer(s).data, status=201)

    def partial_update(self, request, pk=None):
        d = dict(request.data)
        version = d.pop("version", None)
        if "formateur_principal" in d:
            d["formateur_principal"] = ref("formations.Formateur", d["formateur_principal"], False)
        if "programme" in d:
            d["programme"] = ref("conventions.Programme", d["programme"], False)
        for k in ("date_debut", "date_fin"):
            if k in d:
                d[k] = date_(d, k)
        s = services.modifier_session(request.user, self.get_object(), version=version, **d)
        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"])
    def ouvrir(self, request, pk=None):
        return Response(self.get_serializer(services.ouvrir_session(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def cloturer(self, request, pk=None):
        s = services.cloturer_session(request.user, self.get_object(), request.data.get("commentaire", ""))
        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        s = services.annuler_session(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"])
    def rouvrir(self, request, pk=None):
        s = services.rouvrir_session(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(s).data)

    @action(detail=True, methods=["post"])
    def seances(self, request, pk=None):
        d = request.data
        se = services.planifier_seance(request.user, self.get_object(), date=date_(d, "date"),
                                       heure_debut=parse_time(champ(d, "heure_debut")),
                                       heure_fin=parse_time(champ(d, "heure_fin")),
                                       formateur=ref("formations.Formateur", champ(d, "formateur")),
                                       theme=d.get("theme", ""))
        return Response(serialiseur_pour(Seance)(se).data, status=201)

    @action(detail=True, methods=["post"])
    def inscrire(self, request, pk=None):
        ins = services.inscrire(request.user, ref("beneficiaires.Candidature", champ(request.data, "candidature")),
                                self.get_object(), derogation_motif=request.data.get("derogation_motif", ""))
        return Response(serialiseur_pour(Inscription)(ins).data, status=201)

    @action(detail=True, methods=["get"], url_path="propositions-cloture")
    def propositions_cloture(self, request, pk=None):
        s = self.get_object()
        verifier(request.user, "evaluation", "L", centre=s.centre_id, session=s)
        return Response(services.propositions_de_cloture(s))

    @action(detail=True, methods=["get"], url_path="feuille-presence")
    def feuille_presence(self, request, pk=None):
        """E-FOR-07 : une ligne par inscrite, nom, prénom, code et mention de la cheffe de classe."""
        s = self.get_object()
        verifier(request.user, "presence", "L", centre=s.centre_id, session=s)
        return Response([{"inscription": str(i.pk), "code": i.beneficiaire.code, "nom": i.beneficiaire.nom,
                          "prenoms": i.beneficiaire.prenoms, "cheffe_de_classe": i.cheffe_de_classe,
                          "statut_participation": i.statut_participation}
                         for i in s.inscriptions.filter(archive=False).select_related("beneficiaire")])

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        s = self.get_object()
        return exporter(request.user, objet="export_formation", centre=s.centre_id,
                        lignes=s.inscriptions.filter(archive=False).select_related("beneficiaire"),
                        nom=f"session-{s.code}", format_=request.query_params.get("format", "xlsx"), colonnes=[
                            ("Code", lambda i: i.beneficiaire.code), ("Nom", lambda i: i.beneficiaire.nom),
                            ("Prénoms", lambda i: i.beneficiaire.prenoms),
                            ("Participation", lambda i: i.get_statut_participation_display()),
                            ("Taux de présence", lambda i: i.taux_presence)])


class VueSeances(VueLectureMetier):
    objet = "session"
    champ_centre = "session__centre"
    champ_session = "session"
    queryset = Seance.objects.select_related("session")
    serializer_class = serialiseur_pour(Seance)

    @action(detail=True, methods=["post"])
    def presences(self, request, pk=None):
        s = services.saisir_presences(request.user, self.get_object(), champ(request.data, "etats"),
                                      motif_tardif=request.data.get("motif_tardif", ""),
                                      valider=request.data.get("valider", True))
        return Response(self.get_serializer(s).data)


class VueInscriptions(VueLectureMetier):
    objet = "inscription"
    nominatif = True
    champ_centre = "session__centre"
    champ_session = "session"
    queryset = Inscription.objects.select_related("beneficiaire", "session")
    serializer_class = serialiseur_pour(Inscription)

    @action(detail=True, methods=["post"])
    def participation(self, request, pk=None):
        i = services.changer_participation(request.user, self.get_object(), champ(request.data, "statut"),
                                           motif_sortie=ref("referentiels.ReferentielValeur",
                                                            request.data.get("motif_sortie"), False),
                                           motif=request.data.get("motif", ""))
        return Response(self.get_serializer(i).data)

    @action(detail=True, methods=["post"], url_path="cheffe-de-classe")
    def cheffe_de_classe(self, request, pk=None):
        return Response(self.get_serializer(services.designer_cheffe_de_classe(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"], url_path="statut-final")
    def statut_final(self, request, pk=None):
        i = services.confirmer_statut_final(request.user, self.get_object(), champ(request.data, "statut"),
                                            motif_derogation=request.data.get("motif_derogation", ""))
        return Response(self.get_serializer(i).data)

    @action(detail=True, methods=["post"])
    def evaluations(self, request, pk=None):
        d = request.data
        ev = services.saisir_evaluation(request.user, self.get_object(), intitule=champ(d, "intitule"),
                                        date=date_(d, "date"), type_resultat=champ(d, "type_resultat"),
                                        note=d.get("note"), note_max=d.get("note_max"),
                                        appreciation=d.get("appreciation", ""))
        return Response(serialiseur_pour(Evaluation)(ev).data, status=201)

    @action(detail=True, methods=["post"])
    def attestation(self, request, pk=None):
        a = services.delivrer_attestation(request.user, self.get_object())
        return Response(serialiseur_pour(Attestation)(a).data, status=201)


class VuePresences(VueLectureMetier):
    objet = "presence"
    nominatif = True
    champ_centre = "seance__session__centre"
    champ_session = "seance__session"
    queryset = Presence.objects.all()
    serializer_class = serialiseur_pour(Presence)


class VueEvaluations(VueLectureMetier):
    objet = "evaluation"
    nominatif = True
    champ_centre = "inscription__session__centre"
    champ_session = "inscription__session"
    queryset = Evaluation.objects.all()
    serializer_class = serialiseur_pour(Evaluation)

    def partial_update(self, request, pk=None):
        ev = services.modifier_evaluation(request.user, self.get_object(), **request.data)
        return Response(self.get_serializer(ev).data)


class VueAttestations(VueLectureMetier):
    objet = "attestation"
    nominatif = True
    champ_centre = "inscription__session__centre"
    queryset = Attestation.objects.all()
    serializer_class = serialiseur_pour(Attestation)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        a = services.annuler_attestation(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(a).data)
