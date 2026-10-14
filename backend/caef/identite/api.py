"""Connexion, double authentification, profil et gestion des comptes (USR-01 à USR-09)."""

from django.contrib.auth import login, logout
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from caef.commun.api import VueLectureMetier
from caef.commun.vues import champ, serialiseur_pour
from caef.habilitations.matrice import matrice
from caef.habilitations.services import affectations_actives, modules_actifs, verifier

from . import services
from .models import Utilisateur


class Connexion(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "connexion"

    def post(self, request):
        d = request.data
        resultat = services.authentifier(champ(d, "identifiant"), champ(d, "mot_de_passe"), d.get("code"))
        login(request, resultat.utilisateur, backend="caef.identite.backends.BackendIdentifiant")
        request.session[services.CLE_OTP_VERIFIE] = bool(resultat.utilisateur.double_auth_active)
        return Response({"double_auth_a_configurer": resultat.double_auth_a_configurer,
                         "mot_de_passe_temporaire": resultat.utilisateur.mot_de_passe_temporaire,
                         "profil": profil(resultat.utilisateur)})


class Deconnexion(APIView):
    sans_double_auth = True

    def post(self, request):
        logout(request)
        return Response(status=204)


def profil(u):
    m = matrice()
    affectations = affectations_actives(u)
    centres = {a.centre_id for a in affectations if a.centre_id}
    return {
        "id": str(u.pk), "identifiant": u.identifiant_connexion, "nom": u.nom, "prenom": u.prenom,
        "double_auth_active": u.double_auth_active,
        "affectations": [{"role": a.role_id, "titre": m.roles[a.role_id].titre, "centre": str(a.centre_id)
                          if a.centre_id else None, "national": a.national} for a in affectations],
        "modules_actifs": {str(c): modules_actifs(c) for c in centres},
    }


class Moi(APIView):
    sans_double_auth = True

    def get(self, request):
        return Response(profil(request.user))


class DoubleAuth(APIView):
    sans_double_auth = True

    def post(self, request, etape):
        u = request.user
        if etape == "initialiser":
            return Response({"uri": services.initialiser_double_auth(u)})
        if etape == "confirmer":
            codes = services.confirmer_double_auth(u, champ(request.data, "code"))
            request.session[services.CLE_OTP_VERIFIE] = True
            return Response({"codes_secours": codes})
        if etape == "verifier":
            if not services.verifier_code_double_auth(u, champ(request.data, "code")):
                return Response({"code": "double_auth_invalide", "message": "Code invalide."}, status=400)
            request.session[services.CLE_OTP_VERIFIE] = True
            return Response({"ok": True})
        return Response(status=404)


class MotDePasse(APIView):
    sans_double_auth = True

    def post(self, request):
        services.changer_mot_de_passe(request.user, champ(request.data, "ancien"), champ(request.data, "nouveau"))
        return Response(status=204)


class VueUtilisateurs(VueLectureMetier):
    """Utilisateurs du périmètre ; création et statut par l'admin. national (E-ADM)."""

    objet = "utilisateur"
    queryset = Utilisateur.objects.all()
    champ_centre = "affectations__centre"
    serializer_class = serialiseur_pour(Utilisateur, ["id", "identifiant_connexion", "nom", "prenom",
                                                      "telephone_pro", "statut", "double_auth_active", "last_login"])

    def get_queryset(self):
        return super().get_queryset().distinct()

    def create(self, request):
        verifier(request.user, "utilisateur", "C")
        d = request.data
        u = Utilisateur.objects.create_user(identifiant_connexion=champ(d, "identifiant_connexion"),
                                            nom=champ(d, "nom"), prenom=champ(d, "prenom"),
                                            telephone_pro=d.get("telephone_pro", ""))
        temporaire = services.mot_de_passe_temporaire(u, request.user)
        return Response({**self.get_serializer(u).data, "mot_de_passe_temporaire": temporaire}, status=201)

    @action(detail=True, methods=["post"])
    def statut(self, request, pk=None):
        u = self.get_object()
        verifier(request.user, "utilisateur", "M")
        services.changer_statut(u, champ(request.data, "statut"), request.user, champ(request.data, "motif"))
        return Response(self.get_serializer(u).data)

    @action(detail=True, methods=["post"], url_path="reinitialiser-mot-de-passe")
    def reinitialiser(self, request, pk=None):
        u = self.get_object()
        verifier(request.user, "utilisateur", "M")
        return Response({"mot_de_passe_temporaire": services.mot_de_passe_temporaire(u, request.user)})
