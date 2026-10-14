"""Aides communes aux services métier : origine de la saisie, verrou optimiste, transitions."""

from django.utils import timezone

from .contexte import contexte
from .exceptions import ConflitVersion, TransitionInterdite
from .models import OrigineSaisie


def origine() -> dict:
    """Colonnes d'origine d'une saisie : en ligne, ou rejouée depuis un appareil (OFF-02)."""
    ctx = contexte()
    if ctx.hors_ligne:
        return {
            "origine_saisie": OrigineSaisie.HORS_LIGNE,
            "appareil_id": ctx.appareil_id,
            "horodatage_appareil": ctx.horodatage_appareil,
        }
    return {"origine_saisie": OrigineSaisie.EN_LIGNE}


def maintenant():
    """Moment réel de l'action : l'horodatage de l'appareil pour une saisie hors ligne (RG-OFF-03)."""
    ctx = contexte()
    if ctx.hors_ligne and ctx.horodatage_appareil:
        return ctx.horodatage_appareil
    return timezone.now()


def jour_reel():
    return timezone.localdate(maintenant())


def verifier_version(obj, version_attendue):
    """Verrou optimiste : refuse l'écriture si la fiche a changé depuis sa lecture (RG-GEN-05)."""
    if version_attendue is not None and int(version_attendue) != obj.version:
        raise ConflitVersion(details={"version_actuelle": obj.version})


def exiger_statut(obj, attendus, action: str, champ: str = "statut"):
    valeur = getattr(obj, champ)
    if valeur not in attendus:
        libelle = getattr(obj, f"get_{champ}_display", lambda: valeur)()
        raise TransitionInterdite(f"« {action} » est impossible au statut « {libelle} ».",
                                  details={"statut": valeur})


def enregistrer(obj, acteur, champs=None):
    """Enregistre une modification en tenant à jour auteur, date et version."""
    obj.marquer_modifie(acteur)
    if champs is not None:
        champs = list(champs) + ["modifie_le", "modifie_par", "version"]
    obj.save(update_fields=champs)
    return obj


def parametre(nom: str):
    """Paramètre métier réglable sans changement de code (settings.CAEF, variables d'environnement)."""
    from django.conf import settings

    return settings.CAEF[nom]
