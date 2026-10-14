"""Programmes, propositions et circuit de validation, conventions, engagements et contributions
(E-CNV-01 à 06, E-CTR-01 à 04)."""

from rest_framework.decorators import action
from rest_framework.response import Response

from caef.commun.api import VueLectureMetier
from caef.commun.codes import code_simple
from caef.commun.vues import champ, date_, donnees, ref, refs, serialiseur_pour
from caef.habilitations.services import verifier
from caef.journal.models import ActionJournal
from caef.journal.services import instantane, journaliser

from . import services
from .models import Contribution, Convention, Engagement, Programme, Proposition, Validation

RV = "referentiels.ReferentielValeur"
CHAMPS_CONTRIBUTION = ("nature", "date_prevue", "montant_promis", "devise", "programme", "description_bien",
                       "quantite", "valeur_estimee", "methode_valorisation")


def _apport(d):
    champs = donnees(d, CHAMPS_CONTRIBUTION, references={"programme": "conventions.Programme"},
                     dates=("date_prevue",))
    champs["centre_beneficiaire"] = ref("referentiels.Centre", champ(d, "centre_beneficiaire"))
    return champs


class VueProgrammes(VueLectureMetier):
    objet = "programme"
    champ_centre = "centres"
    queryset = Programme.objects.filter(archive=False)
    serializer_class = serialiseur_pour(Programme)

    def get_queryset(self):
        return super().get_queryset().distinct()

    def create(self, request):
        verifier(request.user, "programme", "C")
        d = request.data
        p = Programme.objects.create(code=code_simple("PRG"), intitule=champ(d, "intitule"),
                                     description=d.get("description", ""),
                                     responsable=ref("identite.Utilisateur", champ(d, "responsable")),
                                     date_debut=date_(d, "date_debut"), date_fin=date_(d, "date_fin"),
                                     cree_par=request.user)
        p.centres.set(refs("referentiels.Centre", d.get("centres")))
        journaliser(ActionJournal.CREATION, utilisateur=request.user, objet=p, apres=instantane(p))
        return Response(self.get_serializer(p).data, status=201)


class VuePropositions(VueLectureMetier):
    objet = "proposition"
    champ_centre = "centres_beneficiaires"
    queryset = Proposition.objects.filter(archive=False)
    serializer_class = serialiseur_pour(Proposition)

    def get_queryset(self):
        qs = super().get_queryset().distinct()
        for cle in ("statut", "opportunite"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs

    def create(self, request):
        d = request.data
        prop = services.creer_proposition(
            request.user, ref("partenaires.Opportunite", champ(d, "opportunite")),
            centres_beneficiaires=refs("referentiels.Centre", d.get("centres_beneficiaires")),
            **donnees(d, services.CHAMPS_PROPOSITION, references={"programme": "conventions.Programme"}))
        return Response(self.get_serializer(prop).data, status=201)

    def partial_update(self, request, pk=None):
        d = request.data
        prop = services.modifier_proposition(
            request.user, self.get_object(), version=d.get("version"),
            **donnees(d, services.CHAMPS_PROPOSITION, references={"programme": "conventions.Programme"}))
        return Response(self.get_serializer(prop).data)

    @action(detail=True, methods=["post"])
    def soumettre(self, request, pk=None):
        return Response(self.get_serializer(services.soumettre_au_circuit(request.user, self.get_object())).data)

    @action(detail=True, methods=["get", "post"])
    def circuit(self, request, pk=None):
        """GET : étapes du circuit ; POST : avis du RC ou décision de la DG."""
        prop = self.get_object()
        if request.method == "POST":
            d = request.data
            prop = services.donner_decision(request.user, prop, champ(d, "decision"), d.get("commentaire", ""),
                                            ref(RV, d.get("motif"), False))
        lignes = Validation.objects.filter(objet_type="proposition", objet_id=prop.pk).order_by("etape", "cree_le")
        return Response({"proposition": self.get_serializer(prop).data,
                         "validations": serialiseur_pour(Validation)(lignes, many=True).data})

    @action(detail=True, methods=["post"], url_path="marquer-soumise")
    def marquer_soumise(self, request, pk=None):
        prop = services.marquer_soumise(request.user, self.get_object(), date_(request.data, "date_envoi"))
        return Response(self.get_serializer(prop).data)

    @action(detail=True, methods=["post"])
    def reponse(self, request, pk=None):
        d = request.data
        prop = services.enregistrer_reponse(request.user, self.get_object(), champ(d, "statut"),
                                            date_(d, "date_reponse"), ref(RV, d.get("motif"), False),
                                            d.get("commentaire", ""))
        return Response(self.get_serializer(prop).data)


class VueConventions(VueLectureMetier):
    objet = "convention"
    champ_centre = "centres"
    queryset = Convention.objects.filter(archive=False).select_related("partenaire")
    serializer_class = serialiseur_pour(Convention)

    def get_queryset(self):
        qs = super().get_queryset().distinct()
        for cle in ("statut", "partenaire", "programme"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs

    def create(self, request):
        d = request.data
        conv = services.creer_convention(
            request.user, partenaire=ref("partenaires.Partenaire", champ(d, "partenaire")),
            centres=refs("referentiels.Centre", d.get("centres")),
            proposition=ref("conventions.Proposition", d.get("proposition"), False),
            **donnees(d, ("programme", "montant_accorde", "devise"), references={"programme": "conventions.Programme"}))
        return Response(self.get_serializer(conv).data, status=201)

    @action(detail=True, methods=["post"])
    def approuver(self, request, pk=None):
        return Response(self.get_serializer(services.approuver_partenariat(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def signer(self, request, pk=None):
        d = request.data
        conv = services.signer_convention(
            request.user, self.get_object(), date_signature=date_(d, "date_signature"),
            signataires=champ(d, "signataires"), document_signe=ref("documents.Document", champ(d, "document_signe")),
            date_debut=date_(d, "date_debut"), date_fin=date_(d, "date_fin"),
            echeancier=[_apport(a) for a in d.get("echeancier") or []])
        return Response(self.get_serializer(conv).data)

    @action(detail=True, methods=["post"])
    def engagements(self, request, pk=None):
        d = request.data
        e = services.ajouter_engagement(request.user, self.get_object(), partie=champ(d, "partie"),
                                        description=champ(d, "description"),
                                        responsable=ref("identite.Utilisateur", champ(d, "responsable")),
                                        echeance=date_(d, "echeance"),
                                        centre=ref("referentiels.Centre", d.get("centre"), False))
        return Response(serialiseur_pour(Engagement)(e).data, status=201)

    @action(detail=True, methods=["post"])
    def contributions(self, request, pk=None):
        c = services.creer_contribution_promise(request.user, self.get_object(), **_apport(request.data))
        return Response(serialiseur_pour(Contribution)(c).data, status=201)

    @action(detail=True, methods=["post"])
    def cloturer(self, request, pk=None):
        conv = services.cloturer_convention(request.user, self.get_object(),
                                            rapport_transmis=bool(request.data.get("rapport_transmis")))
        return Response(self.get_serializer(conv).data)


class VueEngagements(VueLectureMetier):
    objet = "engagement"
    champ_centre = "convention__centres"
    queryset = Engagement.objects.filter(archive=False).select_related("convention")
    serializer_class = serialiseur_pour(Engagement)

    def get_queryset(self):
        qs = super().get_queryset().distinct()
        for cle in ("etat", "convention"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs

    @action(detail=True, methods=["post"])
    def realise(self, request, pk=None):
        e = services.declarer_engagement_realise(request.user, self.get_object(),
                                                 ref("documents.Document", request.data.get("justificatif"), False))
        return Response(self.get_serializer(e).data)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(services.valider_engagement(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def abandonner(self, request, pk=None):
        e = services.abandonner_engagement(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(e).data)


class VueContributions(VueLectureMetier):
    """Promis, reçu et validé restent séparés ; financier et en nature ne s'additionnent pas."""

    objet = "contribution"
    champ_centre = "centre_beneficiaire"
    queryset = Contribution.objects.filter(archive=False).select_related("convention", "partenaire")
    serializer_class = serialiseur_pour(Contribution)

    def queryset_base(self):
        qs = super().queryset_base()
        for cle in ("statut", "convention", "partenaire", "nature", "programme", "centre_beneficiaire"):
            if self.request.query_params.get(cle):
                qs = qs.filter(**{cle: self.request.query_params[cle]})
        return qs

    @action(detail=True, methods=["post"])
    def reception(self, request, pk=None):
        d = request.data
        c = services.enregistrer_reception(
            request.user, self.get_object(), date_reception=date_(d, "date_reception"),
            justificatifs=refs("documents.Document", d.get("justificatifs")),
            **donnees(d, ("montant_recu", "quantite", "devise_origine", "montant_origine", "taux_conversion",
                          "source_taux", "valeur_estimee", "methode_valorisation")))
        return Response(self.get_serializer(c).data)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        return Response(self.get_serializer(services.valider_contribution(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def rapprocher(self, request, pk=None):
        d = request.data
        c = services.rapprocher_contribution(request.user, self.get_object(),
                                             reference_piece_comptable=champ(d, "reference_piece_comptable"),
                                             date_encaissement_constatee=date_(d, "date_encaissement_constatee"))
        return Response(self.get_serializer(c).data)

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        c = services.annuler_contribution(request.user, self.get_object(), champ(request.data, "motif"))
        return Response(self.get_serializer(c).data)

    @action(detail=False, methods=["get"])
    def totaux(self, request):
        return Response(services.totaux_contributions(self.filter_queryset(self.get_queryset())))
