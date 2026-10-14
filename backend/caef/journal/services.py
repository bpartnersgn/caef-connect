"""Écriture du journal d'audit, dans la même transaction que l'action (SEC-04, RG-GEN-02)."""

import datetime
import decimal
import uuid

from django.db import connection
from django.db.models import Model

from caef.commun.contexte import contexte

from .models import ActionJournal, JournalAudit

# Champs jamais recopiés dans le journal (secrets, champs restreints).
CHAMPS_EXCLUS = {"password", "secret_double_auth", "codes_secours", "piece_identite_numero", "chemin_stockage"}


def _serialisable(valeur):
    if isinstance(valeur, (uuid.UUID, decimal.Decimal)):
        return str(valeur)
    if isinstance(valeur, (datetime.date, datetime.datetime, datetime.time)):
        return valeur.isoformat()
    if isinstance(valeur, Model):
        return str(valeur.pk)
    if isinstance(valeur, dict):
        return {k: _serialisable(v) for k, v in valeur.items()}
    if isinstance(valeur, (list, tuple, set)):
        return [_serialisable(v) for v in valeur]
    return valeur


def instantane(obj, champs=None) -> dict:
    """Valeurs des champs simples d'un objet, sans les champs exclus."""
    resultat = {}
    for champ in obj._meta.concrete_fields:
        nom = champ.attname
        if nom in CHAMPS_EXCLUS or champ.name in CHAMPS_EXCLUS:
            continue
        if champs is not None and champ.name not in champs and nom not in champs:
            continue
        resultat[champ.name] = _serialisable(getattr(obj, nom))
    return resultat


def difference(avant: dict, apres: dict) -> tuple[dict, dict]:
    """Valeurs modifiées uniquement (Modèle § 3 : avant, après)."""
    cles = {k for k in set(avant) | set(apres) if avant.get(k) != apres.get(k)}
    cles -= {"modifie_le", "modifie_par", "version"}
    return {k: avant.get(k) for k in cles}, {k: apres.get(k) for k in cles}


def journaliser(action, *, utilisateur=None, objet=None, objet_type=None, objet_id=None, centre=None,
                avant=None, apres=None, motif="", nb_lignes=None, interim=False):
    ctx = contexte()
    if objet is not None:
        objet_type = objet_type or objet._meta.db_table
        objet_id = objet_id or objet.pk
    centre_id = getattr(centre, "pk", centre)
    return JournalAudit.objects.create(
        utilisateur=utilisateur if getattr(utilisateur, "is_authenticated", False) else None,
        adresse_ip=ctx.adresse_ip or "",
        centre_id=centre_id,
        action=action,
        objet_type=objet_type or "",
        objet_id=objet_id,
        avant=_serialisable(avant) if avant else None,
        apres=_serialisable(apres) if apres else None,
        motif=motif or "",
        nb_lignes=nb_lignes,
        appareil_id=ctx.appareil_id,
        interim=interim,
    )


def journaliser_refus(utilisateur, erreur):
    """Journalise un refus d'accès hors de toute transaction annulée.

    Appelé par le gestionnaire d'exceptions de l'API et par le moteur de synchronisation,
    après l'annulation de la transaction de l'action refusée.
    """
    if connection.in_atomic_block and connection.needs_rollback:
        return None
    apres = {"objet": getattr(erreur, "objet", None), "action": getattr(erreur, "action", None),
             "code": getattr(erreur, "code", None)}
    return journaliser(
        ActionJournal.ACCES_REFUSE,
        utilisateur=utilisateur,
        objet_type=getattr(erreur, "objet_type", None) or getattr(erreur, "objet", None) or "",
        objet_id=getattr(erreur, "objet_id", None),
        centre=getattr(erreur, "centre_id", None),
        apres=apres,
        motif=getattr(erreur, "message", str(erreur)),
    )
