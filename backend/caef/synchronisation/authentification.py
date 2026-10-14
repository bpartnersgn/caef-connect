"""Jetons à durée limitée, liés à l'utilisateur et à l'appareil enrôlé (DAT § 4.2, § 5.6)."""

from dataclasses import dataclass

from django.conf import settings
from django.core import signing
from django.utils import timezone
from rest_framework import authentication, exceptions

SEL_JETON = "caef.synchronisation.jeton-appareil"


@dataclass
class JetonAppareil:
    appareil: object
    emis_le: float
    est_jeton_appareil: bool = True


def emettre_jeton(utilisateur, appareil) -> str:
    return signing.dumps({"u": str(utilisateur.pk), "a": str(appareil.pk), "t": timezone.now().timestamp()},
                         salt=SEL_JETON, compress=True)


def lire_jeton(jeton: str):
    """Valable 72 heures après la dernière connexion en ligne complète (OFF-06, paramétrable)."""
    duree = settings.CAEF["HORS_LIGNE_VALIDITE_HEURES"] * 3600
    return signing.loads(jeton, salt=SEL_JETON, max_age=duree)


class AuthentificationAppareil(authentication.BaseAuthentication):
    mot_cle = "Appareil"

    def authenticate(self, request):
        entete = authentication.get_authorization_header(request).split()
        if not entete or entete[0].decode().lower() != self.mot_cle.lower():
            return None
        if len(entete) != 2:
            raise exceptions.AuthenticationFailed({"code": "jeton_invalide", "message": "Jeton d'appareil invalide."})
        try:
            donnees = lire_jeton(entete[1].decode())
        except signing.SignatureExpired:
            raise exceptions.AuthenticationFailed(
                {"code": "reconnexion_requise",
                 "message": "Reconnectez-vous en ligne : la validité hors ligne de 72 heures est dépassée."})
        except signing.BadSignature:
            raise exceptions.AuthenticationFailed({"code": "jeton_invalide", "message": "Jeton d'appareil invalide."})

        from caef.identite.models import Utilisateur

        from .models import Appareil, StatutAppareil

        appareil = Appareil.objects.select_related("centre", "point_de_vente").filter(pk=donnees["a"]).first()
        if appareil is None or appareil.statut != StatutAppareil.ACTIF:
            # Un appareil révoqué efface tout au premier contact (OFF-06, CA-OFF-03).
            raise exceptions.AuthenticationFailed(
                {"code": "appareil_revoque", "effacer_donnees_locales": True,
                 "message": "Cet appareil a été révoqué : ses données locales doivent être effacées."})
        utilisateur = Utilisateur.objects.filter(pk=donnees["u"]).first()
        if utilisateur is None or not utilisateur.is_active:
            raise exceptions.AuthenticationFailed({"code": "compte_inactif", "message": "Compte inactif."})
        return utilisateur, JetonAppareil(appareil=appareil, emis_le=donnees["t"])

    def authenticate_header(self, request):
        return self.mot_cle


try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class SchemaAuthentificationAppareil(OpenApiAuthenticationExtension):
        target_class = "caef.synchronisation.authentification.AuthentificationAppareil"
        name = "jetonAppareil"

        def get_security_definition(self, auto_schema):
            return {"type": "apiKey", "in": "header", "name": "Authorization",
                    "description": "« Appareil <jeton> », délivré après une connexion complète."}
except ImportError:  # pragma: no cover
    pass
