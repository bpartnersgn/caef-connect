"""Champs communs : montants en GNF entiers, champs chiffrés au niveau applicatif."""

from decimal import Decimal

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

DEVISES = [("GNF", "Franc guinéen"), ("USD", "Dollar américain"), ("EUR", "Euro")]


class Montant(models.DecimalField):
    """Montant décimal (18,2) ; la devise est portée par un champ voisin (Modèle § 1)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_digits", 18)
        kwargs.setdefault("decimal_places", 2)
        super().__init__(*args, **kwargs)


def verifier_gnf_entier(valeur, libelle="Le montant"):
    """Montants en GNF entiers (RG-BOU-11, PAY) : refuse toute partie décimale."""
    if valeur is None:
        return
    valeur = Decimal(valeur)
    if valeur != valeur.to_integral_value():
        raise ValidationError(f"{libelle} doit être un nombre entier de francs guinéens.")


def _fernet():
    return Fernet(settings.CAEF_CLE_CHIFFREMENT_CHAMPS.encode())


def chiffrer(texte: str | None) -> str | None:
    if texte in (None, ""):
        return texte
    return _fernet().encrypt(texte.encode()).decode()


def dechiffrer(jeton: str | None) -> str | None:
    if jeton in (None, ""):
        return jeton
    try:
        return _fernet().decrypt(jeton.encode()).decode()
    except InvalidToken as exc:  # pragma: no cover - clé changée sans migration
        raise ValueError("Champ chiffré illisible : vérifiez la clé de chiffrement.") from exc


class TexteChiffre(models.TextField):
    """Texte chiffré en base avec une clé distincte (DAT § 5.3, champs « R »)."""

    def from_db_value(self, value, expression, connection):
        return dechiffrer(value)

    def to_python(self, value):
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return chiffrer(value)
