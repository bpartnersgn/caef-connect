"""Clôture mensuelle, tableaux de bord, fiches d'indicateurs et rapports (E-TDB, E-SRC, E-RAP)."""

from rest_framework.decorators import action
from rest_framework.response import Response

from caef.commun.api import VueLectureMetier
from caef.commun.services import jour_reel
from caef.commun.vues import champ, date_, ref, refs, serialiseur_pour
from caef.habilitations.services import verifier

from . import cloture, rapports
from .models import ClotureMensuelle, FicheIndicateur, LigneRapprochement, Rapport, StatutFiche, ValeurIndicateur


class VueClotures(VueLectureMetier):
    objet = "cloture_mensuelle"
    queryset = ClotureMensuelle.objects.select_related("centre")
    serializer_class = serialiseur_pour(ClotureMensuelle)

    def queryset_base(self):
        qs = super().queryset_base()
        for cle in ("mois", "statut", "centre"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs

    def create(self, request):
        """Génère (ou recalcule tant qu'elle est à faire) la clôture d'un mois révolu."""
        d = request.data
        centre = ref("referentiels.Centre", champ(d, "centre"))
        verifier(request.user, "cloture_mensuelle", "C", centre=centre)
        c = cloture.generer(centre, champ(d, "mois"))
        return Response(self.get_serializer(c).data, status=201)

    @action(detail=True, methods=["get"])
    def lignes(self, request, pk=None):
        c = self.get_object()
        return Response({"lignes": serialiseur_pour(LigneRapprochement)(c.lignes.all(), many=True).data,
                         "blocages": cloture.blocages_verification(c)})

    @action(detail=True, methods=["post"])
    def pieces(self, request, pk=None):
        montants = {}
        for cle, v in (champ(request.data, "montants") or {}).items():
            montants[cle] = {**v, "piece_justificative": ref("documents.Document", v.get("piece_justificative"),
                                                               False)}
        return Response(self.get_serializer(cloture.saisir_pieces(request.user, self.get_object(), montants)).data)

    @action(detail=True, methods=["post"], url_path="deroger-appareils")
    def deroger(self, request, pk=None):
        c = cloture.deroger_appareils(request.user, self.get_object(),
                                      refs("synchronisation.Appareil", request.data.get("appareils")),
                                      champ(request.data, "motif"))
        return Response(self.get_serializer(c).data)

    @action(detail=True, methods=["post"], url_path="verifier")
    def verifier_(self, request, pk=None):
        return Response(self.get_serializer(cloture.verifier_cloture(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(cloture.valider_cloture(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def renvoyer(self, request, pk=None):
        c = cloture.renvoyer_cloture(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(c).data)


class VueIndicateurs(VueLectureMetier):
    """Valeurs de la table de synthèse. Sans centre : tableau national (fiches validées seulement) ;
    avec centre : tableau de bord du centre. Un indicateur absent s'affiche « non renseigné »."""

    objet = "tdb_centre"
    queryset = ValeurIndicateur.objects.all()

    def list(self, request):
        p = request.query_params
        jour = jour_reel()
        debut = date_(p, "debut", False) or jour.replace(day=1)
        fin = date_(p, "fin", False) or jour
        centre = ref("referentiels.Centre", p.get("centre"), False)
        if centre is None:
            verifier(request.user, "tdb_national", "L")
            valides = set(FicheIndicateur.objects.filter(statut=StatutFiche.VALIDEE).values_list("code", flat=True))
            qs = ValeurIndicateur.objects.filter(centre__isnull=True, indicateur__in=valides)
        else:
            verifier(request.user, "tdb_centre", "L", centre=centre)
            qs = ValeurIndicateur.objects.filter(centre=centre)
        qs = qs.filter(periode_debut=debut, periode_fin=fin).order_by("indicateur", "ventilation")
        fiches = {f.code: f for f in FicheIndicateur.objects.all()}
        return Response({"debut": debut, "fin": fin, "centre": str(centre.pk) if centre else None,
                         "valeurs": [{**rapports.valeur_publique(v),
                                      "libelle": fiches[v.indicateur].libelle if v.indicateur in fiches else "",
                                      "statut_fiche": fiches[v.indicateur].statut if v.indicateur in fiches else ""}
                                     for v in qs]})

    def retrieve(self, request, pk=None):
        return Response(status=405)


class VueFichesIndicateurs(VueLectureMetier):
    objet = "fiche_indicateur"
    champ_centre = None
    lookup_value_regex = "IND-[0-9]+"
    queryset = FicheIndicateur.objects.all()
    serializer_class = serialiseur_pour(FicheIndicateur)

    @action(detail=True, methods=["post"])
    def statut(self, request, pk=None):
        """Proposée par le SE, validée (ou retirée) par la DG (H10)."""
        f = self.get_object()
        statut = champ(request.data, "statut")
        if statut not in StatutFiche.values:
            from caef.commun.exceptions import RegleMetier

            raise RegleMetier("Statut de fiche inconnu.")
        verifier(request.user, "fiche_indicateur", "V" if statut in ("validee", "retiree") else "M")
        from django.db import transaction

        from caef.journal.models import ActionJournal
        from caef.journal.services import journaliser

        avant = f.statut
        f.statut = statut
        if statut == StatutFiche.REVISEE:
            f.version += 1
        with transaction.atomic():
            f.save()
            journaliser(ActionJournal.STATUT, utilisateur=request.user, objet_type="fiche_indicateur", objet_id=None,
                        avant={"code": f.code, "statut": avant}, apres={"statut": statut, "version": f.version},
                        motif=request.data.get("motif", ""))
        return Response(self.get_serializer(f).data)


class VueRapports(VueLectureMetier):
    objet = "rapport_centre"
    queryset = Rapport.objects.all()
    serializer_class = serialiseur_pour(Rapport)

    def get_queryset(self):
        from django.db.models import Q

        from caef.commun.api import q_perimetre

        q = Q(pk__in=[])
        trouve = False
        for type_, objet in rapports.OBJETS.items():
            qo = q_perimetre(self.request.user, objet, champ_centre="centre" if type_ == "R-02" else None)
            if qo is not None:
                trouve = True
                q |= Q(type=type_) & qo
        if not trouve:
            verifier(self.request.user, "rapport_centre", "L")
        return Rapport.objects.filter(q)

    def create(self, request):
        d = request.data
        r = rapports.generer_rapport(request.user, type=champ(d, "type"), debut=date_(d, "debut"), fin=date_(d, "fin"),
                                     centre=ref("referentiels.Centre", d.get("centre"), False),
                                     convention=ref("conventions.Convention", d.get("convention"), False),
                                     commentaire=d.get("commentaire", ""))
        return Response(self.get_serializer(r).data, status=201)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(rapports.valider_rapport(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def transmettre(self, request, pk=None):
        return Response(self.get_serializer(rapports.transmettre_rapport(request.user, self.get_object())).data)
