from caef.commun.contexte import Contexte, definir, restaurer


def adresse_client(request):
    # Derrière Nginx, l'adresse réelle est transmise par X-Real-IP (configuration du proxy).
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or ""


class ContexteRequeteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        jeton = definir(Contexte(adresse_ip=adresse_client(request)))
        try:
            return self.get_response(request)
        finally:
            restaurer(jeton)
