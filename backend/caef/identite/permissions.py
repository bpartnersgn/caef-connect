from rest_framework.permissions import BasePermission

from caef.commun.exceptions import AccesRefuse, DoubleAuthRequise

from .services import CLE_OTP_VERIFIE, double_auth_obligatoire


def double_auth_verifiee(request) -> bool:
    # Un jeton d'appareil n'est délivré qu'après une connexion complète (double authentification comprise).
    if getattr(request, "auth", None) is not None and getattr(request.auth, "est_jeton_appareil", False):
        return True
    session = getattr(request, "session", None)
    return bool(session and session.get(CLE_OTP_VERIFIE))


class UtilisateurAuthentifie(BasePermission):
    """Authentifié, double authentification faite pour les rôles qui l'exigent, mot de passe
    temporaire changé. Les droits métier sont ensuite vérifiés dans chaque service."""

    message = "Connectez-vous pour continuer."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(getattr(request, "auth", None), "est_jeton_appareil", False) \
                and not getattr(view, "accepte_jeton_appareil", False):
            # Le jeton d'appareil ne sert qu'à la synchronisation (DAT § 5.6).
            raise AccesRefuse("Jeton d'appareil réservé à la synchronisation.", code="jeton_appareil_hors_synchro")
        if getattr(view, "sans_double_auth", False):
            return True
        if not double_auth_verifiee(request) and (user.double_auth_active or double_auth_obligatoire(user)):
            raise DoubleAuthRequise("Double authentification requise pour ce compte.")
        if user.mot_de_passe_temporaire:
            raise AccesRefuse("Changez votre mot de passe temporaire avant de continuer.",
                              code="mot_de_passe_temporaire")
        return True
