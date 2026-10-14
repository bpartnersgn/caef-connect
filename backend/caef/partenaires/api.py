"""Partenaires, interlocuteurs, interactions, opportunités et fiches projet (E-PAR-01 à 06)."""

from rest_framework.decorators import action
from rest_framework.response import Response

from caef.commun.api import VueLectureMetier
from caef.commun.vues import champ, date_, donnees, ref, refs, serialiseur_pour

from . import services
from .models import FicheProjet, HistoriqueEtape, Interaction, Interlocuteur, Opportunite, Partenaire

RV = "referentiels.ReferentielValeur"
CHAMPS_PARTENAIRE = ("sigle", "categorie", "secteur", "adresse", "telephone", "courriel", "site_web",
                     "responsable_suivi", "statut", "raison_sociale")
REFS_PARTENAIRE = {"categorie": RV, "secteur": RV, "responsable_suivi": "identite.Utilisateur"}


class VuePartenaires(VueLectureMetier):
    """Annuaire commun au réseau : un centre y cherche avant de créer (RG-PAR-01)."""

    objet = "partenaire"
    champ_centre = None
    queryset = Partenaire.objects.filter(archive=False)
    serializer_class = serialiseur_pour(Partenaire)

    def queryset_base(self):
        qs = super().queryset_base()
        if self.request.query_params.get("q"):
            qs = qs.filter(raison_sociale__icontains=self.request.query_params["q"])
        return qs

    def create(self, request):
        d = request.data
        champs = donnees(d, CHAMPS_PARTENAIRE, references=REFS_PARTENAIRE)
        champs.pop("raison_sociale", None)
        p = services.creer_partenaire(request.user, raison_sociale=champ(d, "raison_sociale"),
                                      confirme_nouveau=bool(d.get("confirme_nouveau")), **champs)
        return Response(self.get_serializer(p).data, status=201)

    def partial_update(self, request, pk=None):
        d = request.data
        p = services.modifier_partenaire(request.user, self.get_object(), version=d.get("version"),
                                         **donnees(d, CHAMPS_PARTENAIRE, references=REFS_PARTENAIRE))
        return Response(self.get_serializer(p).data)

    @action(detail=False, methods=["get"])
    def proches(self, request):
        proches = services.partenaires_proches(champ(request.query_params, "raison_sociale"),
                                               request.query_params.get("sigle", ""))
        self.get_queryset()  # droit de lecture exigé
        return Response([{"id": str(p.pk), "code": p.code, "raison_sociale": p.raison_sociale, "sigle": p.sigle}
                         for p in proches])

    @action(detail=True, methods=["post"])
    def interlocuteurs(self, request, pk=None):
        d = request.data
        i = services.ajouter_interlocuteur(request.user, self.get_object(), principal=bool(d.get("principal")),
                                           **donnees(d, ("nom", "fonction", "telephone_pro", "courriel_pro")))
        return Response(serialiseur_pour(Interlocuteur)(i).data, status=201)

    @action(detail=True, methods=["post"])
    def interactions(self, request, pk=None):
        d = request.data
        i = services.enregistrer_interaction(
            request.user, self.get_object(), participants=refs("identite.Utilisateur", d.get("participants")),
            interlocuteurs=refs("partenaires.Interlocuteur", d.get("interlocuteurs")),
            **donnees(d, ("opportunite", "type", "date", "compte_rendu", "prochaine_action",
                          "date_prochaine_action"),
                      references={"opportunite": "partenaires.Opportunite"},
                      dates=("date", "date_prochaine_action")))
        return Response(serialiseur_pour(Interaction)(i).data, status=201)


class VueInterlocuteurs(VueLectureMetier):
    objet = "interlocuteur"
    champ_centre = None
    queryset = Interlocuteur.objects.filter(archive=False)
    serializer_class = serialiseur_pour(Interlocuteur)

    def queryset_base(self):
        qs = super().queryset_base()
        if self.request.query_params.get("partenaire"):
            qs = qs.filter(partenaire=self.request.query_params["partenaire"])
        return qs


class VueInteractions(VueLectureMetier):
    objet = "interlocuteur"
    champ_centre = None
    queryset = Interaction.objects.filter(archive=False).order_by("-date")
    serializer_class = serialiseur_pour(Interaction)

    def queryset_base(self):
        qs = super().queryset_base()
        for cle in ("partenaire", "opportunite"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs


class VueOpportunites(VueLectureMetier):
    """Pipeline en 15 étapes ; un centre voit les opportunités qui le concernent."""

    objet = "opportunite"
    champ_centre = "centres"
    queryset = Opportunite.objects.filter(archive=False).select_related("partenaire")
    serializer_class = serialiseur_pour(Opportunite)

    def get_queryset(self):
        qs = super().get_queryset().distinct()
        p = self.request.query_params
        for cle in ("statut", "etape", "partenaire", "responsable"):
            if p.get(cle):
                qs = qs.filter(**{cle: p[cle]})
        return qs

    def create(self, request):
        d = request.data
        opp = services.creer_opportunite(
            request.user, partenaire=ref("partenaires.Partenaire", champ(d, "partenaire")),
            intitule=champ(d, "intitule"), origine=ref(RV, champ(d, "origine")),
            centres=refs("referentiels.Centre", d.get("centres")),
            responsable=ref("identite.Utilisateur", d.get("responsable") or request.user.pk),
            prochaine_action=champ(d, "prochaine_action"), date_prochaine_action=date_(d, "date_prochaine_action"),
            fiches_projet=refs("partenaires.FicheProjet", d.get("fiches_projet")),
            **donnees(d, ("apporteur", "montant_estime", "devise", "potentiel")))
        return Response(self.get_serializer(opp).data, status=201)

    @action(detail=True, methods=["post"])
    def etape(self, request, pk=None):
        opp = services.changer_etape(request.user, self.get_object(), int(champ(request.data, "etape")),
                                     request.data.get("commentaire", ""))
        return Response(self.get_serializer(opp).data)

    @action(detail=True, methods=["post"])
    def clore(self, request, pk=None):
        d = request.data
        opp = services.clore_opportunite(request.user, self.get_object(), champ(d, "statut"),
                                         ref(RV, d.get("motif"), False), d.get("commentaire", ""))
        return Response(self.get_serializer(opp).data)

    @action(detail=True, methods=["post"], url_path="fiches-projet")
    def fiches_projet(self, request, pk=None):
        services.rattacher_fiche_projet(request.user, self.get_object(),
                                        ref("partenaires.FicheProjet", champ(request.data, "fiche")))
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=["get"])
    def historique(self, request, pk=None):
        opp = self.get_object()
        return Response({"etapes": serialiseur_pour(HistoriqueEtape)(opp.historique.order_by("date"), many=True).data,
                         "durees_jours": services.durees_par_etape(opp)})


class VueFichesProjet(VueLectureMetier):
    objet = "fiche_projet"
    queryset = FicheProjet.objects.filter(archive=False)
    serializer_class = serialiseur_pour(FicheProjet)

    def create(self, request):
        d = request.data
        f = services.creer_fiche_projet(
            request.user, centre=ref("referentiels.Centre", champ(d, "centre")),
            **donnees(d, ("intitule", "besoin", "beneficiaires_vises", "objectif_impact", "indicateurs",
                          "budget_indicatif", "devise")))
        return Response(self.get_serializer(f).data, status=201)

    @action(detail=True, methods=["post"])
    def qualifier(self, request, pk=None):
        f = services.qualifier_fiche_projet(request.user, self.get_object(),
                                            qualifiee=request.data.get("qualifiee", True) not in (False, "false"),
                                            motif=request.data.get("motif", ""))
        return Response(self.get_serializer(f).data)
