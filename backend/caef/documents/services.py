"""Dépôt et téléchargement des pièces : contrôle des droits sur l'objet rattaché, puis lien signé
de courte durée ; aucun lien public permanent (DAT § 5.3 et § 7)."""

import hashlib
import uuid

from django.apps import apps
from django.core import signing
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from caef.commun.exceptions import AccesRefuse, RegleMetier
from caef.commun.services import origine, parametre
from caef.habilitations.services import verifier
from caef.journal.models import ActionJournal
from caef.journal.services import journaliser

from .models import Confidentialite, Document

# Signatures des formats acceptés : on lit le contenu, pas l'extension annoncée.
FORMATS = {
    "pdf": (b"%PDF-",),
    "jpg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
}

# objet_type (table) → (modèle, objet de la Matrice, chemin vers le centre, nominatif)
RATTACHEMENTS = {
    "beneficiaire": ("beneficiaires.Beneficiaire", "piece_justificative", "centre_rattachement", True),
    "candidature": ("beneficiaires.Candidature", "piece_justificative", "centre", True),
    "presence": ("formations.Presence", "presence", "seance__session__centre", True),
    "attestation": ("formations.Attestation", "attestation", "inscription__session__centre", True),
    "formation": ("formations.Formation", "formation_centre", "centre", False),
    "formateur": ("formations.Formateur", "formateur", None, False),
    "partenaire": ("partenaires.Partenaire", "partenaire", None, False),
    "convention": ("conventions.Convention", "convention", None, False),
    "proposition": ("conventions.Proposition", "proposition", None, False),
    "contribution": ("conventions.Contribution", "contribution", "centre_beneficiaire", False),
    "reversement": ("boutique.Reversement", "reversement_preparation", "point_de_vente__centre", False),
    "session_caisse": ("boutique.SessionCaisse", "caisse", "point_de_vente__centre", False),
    "ligne_rapprochement": ("pilotage.LigneRapprochement", "cloture_mensuelle", "cloture_mensuelle__centre", False),
    "remboursement": ("paiements.Remboursement", "remboursement", "centre", False),
    "centre": ("referentiels.Centre", "centre", "pk", False),
}


def detecter_format(contenu: bytes) -> str | None:
    for fmt, signatures in FORMATS.items():
        if any(contenu.startswith(s) for s in signatures):
            return fmt
    return None


def _objet_rattache(objet_type, objet_id):
    if objet_type not in RATTACHEMENTS:
        raise RegleMetier("Ce type d'objet ne reçoit pas de pièce.")
    modele, objet_matrice, chemin_centre, nominatif = RATTACHEMENTS[objet_type]
    obj = apps.get_model(modele)._default_manager.get(pk=objet_id)
    centre_id = None
    if chemin_centre == "pk":
        centre_id = obj.pk
    elif chemin_centre:
        valeur = obj
        for morceau in chemin_centre.split("__"):
            valeur = getattr(valeur, morceau, None)
            if valeur is None:
                break
        centre_id = getattr(valeur, "pk", valeur)
    return obj, objet_matrice, centre_id, nominatif


def deposer(acteur, *, objet_type, objet_id, type_document, nom_fichier, contenu: bytes,
            confidentialite=Confidentialite.INTERNE, remplace=None) -> Document:
    obj, objet_matrice, centre_id, nominatif = _objet_rattache(objet_type, objet_id)
    action = "C" if objet_matrice == "piece_justificative" else "M"
    if objet_matrice in ("reversement_preparation", "caisse", "cloture_mensuelle", "contribution", "remboursement"):
        action = "C"
    verifier(acteur, objet_matrice, action, centre=centre_id, nominatif=nominatif)
    if len(contenu) > parametre("DOCUMENT_TAILLE_MAX_OCTETS"):
        raise RegleMetier("Fichier trop volumineux (10 Mo au plus).", code="fichier_trop_volumineux")
    fmt = detecter_format(contenu)
    if fmt is None:
        raise RegleMetier("Format refusé : PDF, JPG ou PNG seulement.", code="format_refuse")
    empreinte = hashlib.sha256(contenu).hexdigest()
    chemin = f"{objet_type}/{uuid.uuid4().hex}.{fmt}"
    if nominatif and confidentialite == Confidentialite.INTERNE:
        confidentialite = Confidentialite.NOMINATIF
    with transaction.atomic():
        chemin_reel = default_storage.save(chemin, ContentFile(contenu))
        doc = Document.objects.create(
            objet_type=objet_type, objet_id=obj.pk, centre_id=centre_id, type_document=type_document,
            nom_fichier=nom_fichier[:255], format=fmt, taille_octets=len(contenu), empreinte=empreinte,
            chemin_stockage=chemin_reel, confidentialite=confidentialite,
            version_document=(remplace.version_document + 1) if remplace else 1, remplace=remplace,
            cree_par=acteur, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=doc, centre=centre_id,
                    apres={"objet_type": objet_type, "objet_id": str(obj.pk), "type_document": type_document,
                           "empreinte": empreinte})
    return doc


def verifier_lecture(acteur, doc: Document):
    _, objet_matrice, centre_id, nominatif = _objet_rattache(doc.objet_type, doc.objet_id)
    verifier(acteur, objet_matrice, "L", centre=centre_id, nominatif=nominatif)
    if doc.confidentialite == Confidentialite.RESTREINT:
        verifier(acteur, "beneficiaire_restreint", "L", centre=centre_id, nominatif=True)


SEL_LIEN = "caef.documents.lien"


def lien_telechargement(acteur, doc: Document) -> dict:
    """Lien valable 5 minutes, lié à l'utilisateur, délivré après contrôle des droits."""
    verifier_lecture(acteur, doc)
    duree = parametre("DOCUMENT_LIEN_SECONDES")
    if doc.confidentialite != Confidentialite.INTERNE:
        journaliser(ActionJournal.CONSULTATION_SENSIBLE, utilisateur=acteur, objet=doc, centre=doc.centre_id)
    stockage_s3 = hasattr(default_storage, "bucket_name")
    if stockage_s3:
        url = default_storage.url(doc.chemin_stockage, expire=duree, parameters={
            "ResponseContentDisposition": f'attachment; filename="{doc.nom_fichier}"'})
        return {"url": url, "expire_dans": duree}
    jeton = signing.TimestampSigner(salt=SEL_LIEN).sign_object({"d": str(doc.pk), "u": str(acteur.pk)})
    return {"url": f"/api/v1/documents/telecharger/{jeton}/", "expire_dans": duree}


def lire_jeton(jeton: str, utilisateur) -> Document:
    try:
        donnees = signing.TimestampSigner(salt=SEL_LIEN).unsign_object(
            jeton, max_age=parametre("DOCUMENT_LIEN_SECONDES"))
    except signing.SignatureExpired:
        raise RegleMetier("Lien expiré : redemandez le document.", code="lien_expire")
    except signing.BadSignature:
        raise AccesRefuse("Lien invalide.", objet="document", action="L")
    if donnees["u"] != str(utilisateur.pk):
        raise AccesRefuse("Ce lien a été délivré à une autre personne.", objet="document", action="L")
    doc = Document.objects.get(pk=donnees["d"])
    verifier_lecture(utilisateur, doc)
    return doc
