"""Pièces jointes : dépôt contrôlé, liens signés de courte durée après contrôle des droits (SEC-05)."""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.storage import default_storage
from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from caef.commun.exceptions import Introuvable, RegleMetier
from caef.commun.vues import champ, ref, serialiseur_pour
from caef.habilitations.services import verifier

from . import services
from .models import Document

SerialiseurDocument = serialiseur_pour(Document)


class VueDocuments(viewsets.GenericViewSet):
    """Liste des pièces d'un objet, dépôt et lien de téléchargement. Jamais d'URL de stockage directe."""

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = SerialiseurDocument
    lookup_value_regex = "[0-9a-f-]{36}"

    def list(self, request):
        p = request.query_params
        objet_type, objet_id = champ(p, "objet_type"), champ(p, "objet_id")
        try:
            _, objet_matrice, centre_id, nominatif = services._objet_rattache(objet_type, objet_id)
        except (ObjectDoesNotExist, ValueError, ValidationError):
            raise Introuvable("Objet introuvable.")
        verifier(request.user, objet_matrice, "L", centre=centre_id, nominatif=nominatif)
        qs = Document.objects.filter(objet_type=objet_type, objet_id=objet_id, archive=False).order_by("cree_le")
        return Response(SerialiseurDocument(qs, many=True).data)

    def create(self, request):
        fichier = request.FILES.get("fichier")
        if fichier is None:
            raise RegleMetier("Fichier manquant.", code="champ_obligatoire", details={"champ": "fichier"})
        d = request.data
        doc = services.deposer(request.user, objet_type=champ(d, "objet_type"), objet_id=champ(d, "objet_id"),
                               type_document=champ(d, "type_document"), nom_fichier=fichier.name,
                               contenu=fichier.read(), confidentialite=d.get("confidentialite") or "interne",
                               remplace=ref("documents.Document", d.get("remplace"), False))
        return Response(SerialiseurDocument(doc).data, status=201)

    @action(detail=True, methods=["post"])
    def lien(self, request, pk=None):
        return Response(services.lien_telechargement(request.user, ref("documents.Document", pk)))


class Telechargement(APIView):
    """Lien signé lié à la personne, valable quelques minutes (stockage local ; S3 renvoie une URL présignée)."""

    def get(self, request, jeton):
        doc = services.lire_jeton(jeton, request.user)
        return FileResponse(default_storage.open(doc.chemin_stockage, "rb"), as_attachment=True,
                            filename=doc.nom_fichier)
