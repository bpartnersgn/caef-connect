"""Pagination et gestionnaire d'exceptions de l'API (séparés de api.py pour éviter un import
circulaire avec les réglages de Django REST framework)."""

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as ErreurValidationDjango
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler as gestionnaire_drf

from caef.commun.exceptions import AccesRefuse, ErreurMetier
from caef.journal.services import journaliser_refus


class Pagination(PageNumberPagination):
    """Pagination obligatoire, 25 lignes par défaut (PERF-01)."""

    page_size = 25
    page_size_query_param = "taille"
    max_page_size = 200


def _messages_validation(exc: ErreurValidationDjango):
    if hasattr(exc, "message_dict"):
        return exc.message_dict
    return {"non_field_errors": exc.messages}


def gestionnaire_exceptions(exc, context):
    request = context.get("request")
    if isinstance(exc, AccesRefuse):
        journaliser_refus(getattr(request, "user", None), exc)
        return Response({"code": exc.code, "message": exc.message, "details": exc.details},
                        status=status.HTTP_403_FORBIDDEN)
    if isinstance(exc, ErreurMetier):
        return Response({"code": exc.code, "message": exc.message, "details": exc.details},
                        status=exc.statut_http)
    if isinstance(exc, ErreurValidationDjango):
        return Response({"code": "validation", "message": "Certaines valeurs sont invalides.",
                         "details": _messages_validation(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, ObjectDoesNotExist):
        return Response({"code": "introuvable", "message": "Objet introuvable."}, status=status.HTTP_404_NOT_FOUND)
    reponse = gestionnaire_drf(exc, context)
    if reponse is not None and isinstance(exc, drf_exceptions.ValidationError):
        reponse.data = {"code": "validation", "message": "Certaines valeurs sont invalides.",
                        "details": reponse.data}
    elif reponse is not None and isinstance(exc, (drf_exceptions.NotAuthenticated,
                                                   drf_exceptions.AuthenticationFailed)):
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            reponse.data = {k: (str(v) if not isinstance(v, bool) else v) for k, v in exc.detail.items()}
        else:
            reponse.data = {"code": "non_authentifie", "message": "Connectez-vous pour continuer."}
    return reponse
