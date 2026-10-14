"""Contexte de la requête ou de l'opération synchronisée en cours (adresse IP, appareil).

Renseigné par le middleware HTTP et par le moteur de synchronisation ; lu par le journal d'audit
et par les services qui horodatent une saisie hors ligne.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Contexte:
    adresse_ip: str | None = None
    appareil_id: str | None = None
    horodatage_appareil: datetime | None = None
    hors_ligne: bool = False
    supplements: dict = field(default_factory=dict)


_contexte: ContextVar[Contexte] = ContextVar("caef_contexte", default=Contexte())


def contexte() -> Contexte:
    return _contexte.get()


def definir(ctx: Contexte):
    return _contexte.set(ctx)


def restaurer(jeton):
    _contexte.reset(jeton)
