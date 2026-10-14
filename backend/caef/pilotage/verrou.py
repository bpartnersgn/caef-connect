"""Verrouillage du mois validé, contrôlé par les services métier (RG-SRC-02) ; la base le
contrôle aussi (migration pilotage 0002)."""

from datetime import date, datetime

from django.utils import timezone

from caef.commun.exceptions import MoisVerrouille


def mois_de(jour) -> str:
    if isinstance(jour, datetime):
        jour = timezone.localtime(jour).date() if timezone.is_aware(jour) else jour.date()
    return f"{jour.year:04d}-{jour.month:02d}"


def mois_verrouille(centre_id, jour) -> bool:
    from .models import ClotureMensuelle

    if jour is None:
        return False
    return ClotureMensuelle.objects.filter(centre_id=getattr(centre_id, "pk", centre_id), mois=mois_de(jour),
                                           verrouillee=True).exists()


def verifier_mois_ouvert(centre_id, jour: date | datetime):
    if mois_verrouille(centre_id, jour):
        raise MoisVerrouille(
            f"Le mois {mois_de(jour)} est verrouillé : passez par une écriture de régularisation "
            "datée du mois courant (RG-SRC-03).",
            details={"mois": mois_de(jour)},
        )
