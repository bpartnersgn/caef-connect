"""Codes lisibles générés par le serveur (RG-GEN-04, RG-OFF-06)."""

import unicodedata

from django.db import transaction

from .models import Compteur


def prochain_numero(cle: str) -> int:
    """Incrémente le compteur `cle` sous verrou de ligne et renvoie la nouvelle valeur."""
    with transaction.atomic():
        compteur, _ = Compteur.objects.select_for_update().get_or_create(cle=cle)
        compteur.valeur += 1
        compteur.save(update_fields=["valeur"])
        return compteur.valeur


def code_annuel(prefixe: str, centre_code: str, annee: int, largeur: int = 5) -> str:
    """Ex. BEN-CMR-2026-00042."""
    cle = f"{prefixe}-{centre_code}-{annee}"
    return f"{cle}-{prochain_numero(cle):0{largeur}d}"


def code_simple(prefixe: str, largeur: int = 5) -> str:
    """Ex. PAR-00012."""
    return f"{prefixe}-{prochain_numero(prefixe):0{largeur}d}"


def normaliser(texte: str | None) -> str:
    """Minuscules, sans accents, espaces simples (RG-BEN-02)."""
    if not texte:
        return ""
    sans_accents = "".join(
        c for c in unicodedata.normalize("NFKD", texte) if not unicodedata.combining(c)
    )
    propre = "".join(c if c.isalnum() else " " for c in sans_accents.lower())
    return " ".join(propre.split())
