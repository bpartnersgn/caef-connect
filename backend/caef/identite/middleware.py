from django.conf import settings
from django.contrib.auth import logout
from django.utils import timezone

CLE_DEBUT_SESSION = "caef_debut_session"


class ExpirationSessionMiddleware:
    """Durée absolue d'une session (8 heures au plus, SEC-02).

    L'expiration après 30 minutes d'inactivité est portée par SESSION_COOKIE_AGE,
    renouvelé à chaque requête.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and hasattr(request, "session"):
            debut = request.session.get(CLE_DEBUT_SESSION)
            maintenant = timezone.now().timestamp()
            if debut is None:
                request.session[CLE_DEBUT_SESSION] = maintenant
            elif maintenant - debut > settings.CAEF_SESSION_DUREE_MAX.total_seconds():
                logout(request)
        return self.get_response(request)
