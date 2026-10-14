"""Lecture de la Matrice des rôles (matrice.yaml), source unique des droits (brief, règle 2)."""

import functools
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FICHIER_MATRICE = Path(__file__).with_name("matrice.yaml")
ACTIONS = ("L", "C", "M", "V", "E", "A")
PERIMETRES = ("s", "c", "n", "ag", "p")
MODULE_SOCLE = "socle"

_JETON = re.compile(r"^([LCMVEA])([*~]?)$")


@dataclass(frozen=True)
class Droit:
    role: str
    objet: str
    action: str
    perimetre: str
    condition: str = ""  # "interim" (V*), "a_defaut_cpt" (V~)


@dataclass
class ObjetMatrice:
    code: str
    libelle: str
    module: str
    centre: bool
    nominatif: bool
    reseau: bool = False
    droits: dict = field(default_factory=dict)  # role -> {action: Droit}


@dataclass
class RoleMatrice:
    code: str
    libelle: str
    titre: str
    double_auth: str
    hors_ligne: bool
    module: str = MODULE_SOCLE


class ErreurMatrice(ValueError):
    pass


def analyser_cellule(role: str, objet: str, cellule: str) -> dict:
    """« L C M A (n) » -> {L: Droit(…, 'n'), C: …}."""
    perimetre = "c"
    trouves = re.findall(r"\(([a-z]+)\)", cellule)
    if trouves:
        perimetre = trouves[-1]
    if perimetre not in PERIMETRES:
        raise ErreurMatrice(f"Périmètre inconnu « {perimetre} » pour {role}/{objet}")
    droits = {}
    for jeton in re.sub(r"\([a-z]+\)", " ", cellule).split():
        m = _JETON.match(jeton)
        if not m:
            raise ErreurMatrice(f"Action inconnue « {jeton} » pour {role}/{objet}")
        action, marque = m.groups()
        condition = {"*": "interim", "~": "a_defaut_cpt", "": ""}[marque]
        droits[action] = Droit(role, objet, action, perimetre, condition)
    return droits


class Matrice:
    def __init__(self, donnees: dict):
        self.version = str(donnees["version"])
        self.roles = {
            code: RoleMatrice(code, r["libelle"], r["titre"], r["double_auth"], bool(r["hors_ligne"]),
                              r.get("module", MODULE_SOCLE))
            for code, r in donnees["roles"].items()
        }
        self.lecture_historique = set(donnees.get("lecture_historique_module_inactif", []))
        self.objets = {}
        for code, o in donnees["objets"].items():
            objet = ObjetMatrice(code, o["libelle"], o.get("module", MODULE_SOCLE), o.get("centre", True),
                                 o.get("nominatif", False), o.get("reseau", False))
            for role, cellule in (o.get("droits") or {}).items():
                if role not in self.roles:
                    raise ErreurMatrice(f"Rôle inconnu « {role} » dans l'objet {code}")
                objet.droits[role] = analyser_cellule(role, code, cellule)
            self.objets[code] = objet

    def objet(self, code) -> ObjetMatrice:
        try:
            return self.objets[code]
        except KeyError as exc:
            raise ErreurMatrice(f"Objet absent de la Matrice : {code}") from exc

    def droit(self, role, objet, action) -> Droit | None:
        return self.objet(objet).droits.get(role, {}).get(action)

    def cellules(self):
        """Toutes les cellules (rôle, objet, action) avec le droit ou None : base des tests de droits."""
        for code, objet in self.objets.items():
            for role in self.roles:
                for action in ACTIONS:
                    yield role, code, action, objet.droits.get(role, {}).get(action)


@functools.cache
def matrice() -> Matrice:
    with FICHIER_MATRICE.open(encoding="utf-8") as fichier:
        return Matrice(yaml.safe_load(fichier))
