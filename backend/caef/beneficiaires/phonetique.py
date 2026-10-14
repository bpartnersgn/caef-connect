"""Normalisation et clé phonétique adaptée au français (RG-BEN-02).

Une clé par mot, mots triés : l'inversion nom et prénom donne la même clé. Les règles sont
volontairement simples et déterministes ; elles seront calibrées sur les données du pilote.
"""

import re

from caef.commun.codes import normaliser

# Remplacements appliqués dans l'ordre, sur un mot déjà normalisé (minuscules, sans accents).
_REGLES = [
    (r"ph", "f"), (r"gh", "g"), (r"th", "t"), (r"sch", "ch"), (r"sh", "ch"), (r"kh", "k"),
    (r"qu", "k"), (r"q", "k"), (r"ck", "k"),
    (r"c(?=[eiy])", "s"), (r"c", "k"),
    (r"gu(?=[eiy])", "g"), (r"g(?=[eiy])", "j"), (r"dj", "j"),
    (r"x", "ks"), (r"z", "s"), (r"w", "ou"), (r"y", "i"),
    (r"eau", "o"), (r"au", "o"), (r"ou", "u"),
    (r"ai", "e"), (r"ei", "e"), (r"ee", "i"),
    (r"(?<=[aeiou])s(?=[aeiou])", "z"),
    (r"(?<!^)h", ""), (r"^h", ""),
    (r"(an|am|en|em)(?=[^aeiou]|$)", "an"), (r"(on|om)(?=[^aeiou]|$)", "on"),
    (r"(in|im|ain|ein|un)(?=[^aeiou]|$)", "in"),
]
_REGLES_COMPILEES = [(re.compile(m), r) for m, r in _REGLES]
_FINALES_MUETTES = re.compile(r"(?<=.{2})(e|s|t|d|x|es|ts|ds)$")


def cle_mot(mot: str) -> str:
    mot = normaliser(mot).replace(" ", "")
    if not mot:
        return ""
    for motif, remplacement in _REGLES_COMPILEES:
        mot = motif.sub(remplacement, mot)
    mot = _FINALES_MUETTES.sub("", mot)
    # Lettres doublées réduites (Diallo / Dialo, Camara / Kamara déjà ramené à k).
    mot = re.sub(r"(.)\1+", r"\1", mot)
    return mot


def cle_phonetique(*textes: str) -> str:
    mots = []
    for t in textes:
        mots.extend(normaliser(t).split())
    cles = sorted(c for c in (cle_mot(m) for m in mots) if c)
    return " ".join(cles)


def nom_normalise(nom: str, prenoms: str) -> str:
    return " ".join(sorted(f"{normaliser(nom)} {normaliser(prenoms)}".split()))
