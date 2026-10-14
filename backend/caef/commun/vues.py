"""Aides aux vues de l'API : lecture des références, réponses, exports journalisés (RG-EXP-01)."""

import csv
import io
from decimal import Decimal

from django.apps import apps
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.response import Response

from caef.commun.exceptions import Introuvable, RegleMetier
from caef.habilitations.services import verifier
from caef.journal.models import ActionJournal
from caef.journal.services import journaliser


def ref(chemin_modele, valeur, obligatoire=True):
    """Objet désigné par son identifiant dans la requête ; les droits sont vérifiés par le service."""
    if valeur in (None, ""):
        if obligatoire:
            raise RegleMetier(f"Référence manquante ({chemin_modele.split('.')[-1]}).")
        return None
    modele = apps.get_model(chemin_modele)
    try:
        return modele._default_manager.get(pk=valeur)
    except (modele.DoesNotExist, ValueError, TypeError, ValidationError):
        raise Introuvable(f"{modele._meta.verbose_name.capitalize()} introuvable.")


def refs(chemin_modele, valeurs):
    return [ref(chemin_modele, v) for v in (valeurs or [])]


def champ(donnees, nom, obligatoire=True, defaut=None):
    if nom not in donnees or donnees[nom] in (None, ""):
        if obligatoire:
            raise RegleMetier(f"Champ obligatoire : {nom}.", code="champ_obligatoire", details={"champ": nom})
        return defaut
    return donnees[nom]


def date_(donnees, nom, obligatoire=True):
    from django.utils.dateparse import parse_date

    v = champ(donnees, nom, obligatoire)
    if v is None:
        return None
    d = parse_date(str(v))
    if d is None:
        raise RegleMetier(f"Date invalide : {nom} (format AAAA-MM-JJ).")
    return d


def repondre(serialiseur, obj, statut=200, **contexte):
    return Response(serialiseur(obj, context=contexte).data, status=statut)


class Serialiseur(serializers.ModelSerializer):
    """Sérialiseur de lecture : jamais de champ restreint, de secret ni de chemin de stockage."""

    EXCLUS = ("chemin_stockage", "password", "secret_double_auth", "codes_secours", "contact_urgence_nom",
              "contact_urgence_tel", "piece_identite_numero", "piece_identite_type", "cle_idempotence",
              "echecs_horodatages")

    def get_field_names(self, declared_fields, info):
        noms = super().get_field_names(declared_fields, info)
        return [n for n in noms if n not in self.EXCLUS]


def serialiseur_pour(modele, champs="__all__", exclure=()):
    meta = type("Meta", (), {"model": modele, "fields": champs} if not exclure else
                {"model": modele, "exclude": exclure})
    return type(f"Serialiseur{modele.__name__}", (Serialiseur,), {"Meta": meta})


# --------------------------------------------------------------------------- exports

def _valeur(v):
    if v is None:
        return "non renseigné"
    if isinstance(v, Decimal):
        return str(v)
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


def exporter(acteur, *, objet, centre, lignes, colonnes, nom, format_="xlsx", motif=""):
    """Export tableur : droit « E », reproduction exacte de la liste filtrée, journalisé avec le nombre
    de lignes (RG-EXP-01, CA-BOU-13). `colonnes` : [(titre, fonction(ligne))]."""
    verifier(acteur, objet, "E", centre=centre)
    lignes = list(lignes)
    journaliser(ActionJournal.EXPORT, utilisateur=acteur, objet_type=objet, centre=centre, nb_lignes=len(lignes),
                motif=motif or nom)
    entetes = [t for t, _ in colonnes]
    donnees = [[_valeur(f(l)) for _, f in colonnes] for l in lignes]
    if format_ == "csv":
        tampon = io.StringIO()
        tampon.write("﻿")
        ecrivain = csv.writer(tampon, delimiter=";")
        ecrivain.writerow(entetes)
        ecrivain.writerows(donnees)
        reponse = HttpResponse(tampon.getvalue(), content_type="text/csv; charset=utf-8")
        reponse["Content-Disposition"] = f'attachment; filename="{nom}.csv"'
        return reponse
    from openpyxl import Workbook

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = nom[:31]
    feuille.append(entetes)
    for ligne in donnees:
        feuille.append(ligne)
    tampon = io.BytesIO()
    classeur.save(tampon)
    reponse = HttpResponse(tampon.getvalue(),
                           content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    reponse["Content-Disposition"] = f'attachment; filename="{nom}.xlsx"'
    return reponse


def donnees(d, autorises, *, references=None, dates=()):
    """Champs admis seulement (liste blanche) ; références et dates converties."""
    references = references or {}
    resultat = {}
    for k in autorises:
        if k not in d:
            continue
        if k in references:
            resultat[k] = ref(references[k], d[k], False)
        elif k in dates:
            resultat[k] = date_(d, k, False)
        else:
            resultat[k] = d[k]
    return resultat
