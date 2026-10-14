"""Droits dérivés de la Matrice : la transcription YAML est fidèle au document 04, puis chaque
cellule (rôle × objet × action) est vérifiée contre le moteur de droits, dans le centre de
l'utilisateur et dans un autre centre. Tout droit absent est refusé."""

from datetime import timedelta
from pathlib import Path

import pytest
from django.utils import timezone

from caef.commun.fictif import COMPTES
from caef.habilitations.matrice import ACTIONS, analyser_cellule, matrice
from caef.habilitations.models import Affectation, InterimResponsable
from caef.habilitations.services import decider, invalider_cache

DOCUMENT = Path(__file__).resolve().parents[4] / "docs" / "04 - Matrice des rôles et permissions CAEF Connect.md"

# Libellés du document qui couvrent plusieurs objets ou s'écrivent autrement dans le fichier.
ALIAS = {
    "File « À résoudre » (conflits de synchronisation et écritures tardives)":
        ["conflit_synchronisation", "ecriture_tardive"],
    "Recherche réseau (anti-doublon)": ["recherche_reseau"],
    "Salle d'exposition (articles exposés, transferts depuis et vers la réserve)": ["salle_exposition"],
}

# Écarts assumés entre le document et le fichier, chacun expliqué dans DECISIONS.md.
ECARTS = {
    ("conflit_synchronisation", "CPT"): "la file est scindée : le CPT ne traite que les écritures tardives",
    ("ecriture_tardive", "RC"): "la file est scindée : RC et RA ne traitent que les conflits de champ",
    ("ecriture_tardive", "RA"): "la file est scindée : RC et RA ne traitent que les conflits de champ",
    ("transfert", "RC"): "« C (accueil), V (origine) » : le côté (accueil, origine) est contrôlé par le service",
    ("transfert", "RA"): "même chose, V pendant l'intérim seulement",
    ("import_beneficiaires", "ADM"): "exécution technique nationale, l'ADM étant affecté au national",
    ("tdb_boutique", "DG"): "volet boutique de la DG prévu au lot 2",
}

# Objets sans ligne dans les tableaux du document, tirés de son texte.
OBJETS_DU_TEXTE = {
    "interim": "déclaration d'intérim, RG-ADM-13",
    "deposante_identite": "identité minimale des déposantes, colonne « accès nominatif » du tableau des rôles",
}


def _normaliser(cellule: str) -> str:
    if cellule in ("—", "-", ""):
        return ""
    principal, _, prose = cellule.partition(", ")
    principal = principal.replace("V (intérim)", "V*").replace("(ag) (n)", "(ag)")
    if "défaut de CPT" in prose:
        principal = principal.replace("V", "V~")
    return principal


def _cellules_du_document():
    libelles = {o.libelle: c for c, o in matrice().objets.items()}
    entete = None
    for ligne in DOCUMENT.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("| Objet"):
            entete = [c.strip() for c in ligne.strip("|").split("|")]
            continue
        if entete and ligne.startswith("| ---"):
            continue
        if entete and ligne.startswith("|"):
            cellules = [c.strip() for c in ligne.strip("|").split("|")]
            for code in ALIAS.get(cellules[0]) or [libelles[cellules[0]]]:
                for role, cellule in zip(entete[1:], cellules[1:], strict=True):
                    yield code, role, cellule
        elif entete:
            entete = None


@pytest.mark.skipif(not DOCUMENT.exists(), reason="document 04 absent")
def test_fichier_conforme_au_document_04():
    m = matrice()
    ecarts = []
    vus = set()
    for code, role, cellule in _cellules_du_document():
        vus.add(code)
        if (code, role) in ECARTS:
            continue
        objet = m.objet(code)
        attendu = analyser_cellule(role, code, _normaliser(cellule)) if _normaliser(cellule) else {}
        reel = objet.droits.get(role, {})
        cle = lambda d: (d.perimetre if objet.centre else "-", d.condition)  # noqa: E731
        if {a: cle(d) for a, d in attendu.items()} != {a: cle(d) for a, d in reel.items()}:
            ecarts.append(f"{code}/{role} : document « {cellule} », fichier {sorted(reel)}")
    assert not ecarts, "\n".join(ecarts)
    manquants = set(m.objets) - vus - set(OBJETS_DU_TEXTE)
    assert not manquants, f"objets sans ligne dans le document : {manquants}"


COMPTE_DU_ROLE = {role: identifiant for identifiant, role, centre in COMPTES if centre in (None, "CMR")}
CELLULES = [(role, code) for code in matrice().objets for role in matrice().roles]


def _attendu_dans_son_centre(droit):
    if droit is None:
        return False
    # V* : intérim non déclaré ; V~ : le centre a un comptable. Testés à part ci-dessous.
    return droit.condition == ""


def _attendu_autre_centre(droit, objet, national):
    if not _attendu_dans_son_centre(droit):
        return False
    return national or not objet.centre or (droit.perimetre in ("n", "ag") and objet.reseau)


@pytest.mark.parametrize("role,code", CELLULES, ids=[f"{r}-{c}" for r, c in CELLULES])
def test_cellule(monde, role, code):
    u = monde["u"][COMPTE_DU_ROLE[role]]
    national = Affectation.objects.get(utilisateur=u).national
    objet = matrice().objet(code)
    erreurs = []
    for action in ACTIONS:
        droit = matrice().droit(role, code, action)
        ici = decider(u, code, action, centre=monde["cmr"]).autorise
        ailleurs = decider(u, code, action, centre=monde["tsb"]).autorise
        if ici != _attendu_dans_son_centre(droit):
            erreurs.append(f"{action} dans son centre : {ici}")
        if ailleurs != _attendu_autre_centre(droit, objet, national):
            erreurs.append(f"{action} dans un autre centre : {ailleurs}")
    assert not erreurs, f"{role}/{code} : " + " ; ".join(erreurs)


def test_le_ra_ne_valide_que_pendant_un_interim_declare(monde):
    ra, rc = monde["u"]["ra.cmr"], monde["u"]["rc.cmr"]
    assert not decider(ra, "candidature", "V", centre=monde["cmr"]).autorise
    jour = timezone.localdate()
    InterimResponsable.objects.create(centre=monde["cmr"], responsable_remplace=rc, adjoint=ra,
                                      date_debut=jour, date_fin=jour + timedelta(days=5), motif="Congé fictif",
                                      declare_par=rc)
    d = decider(ra, "candidature", "V", centre=monde["cmr"])
    assert d.autorise and d.interim
    assert not decider(ra, "candidature", "V", centre=monde["tsb"]).autorise


def test_validation_de_caisse_a_defaut_de_comptable(monde):
    rc = monde["u"]["rc.cmr"]
    assert not decider(rc, "caisse_validation", "V", centre=monde["cmr"]).autorise
    Affectation.objects.filter(role_id="CPT", centre=monde["cmr"]).update(date_fin=timezone.localdate()
                                                                            - timedelta(days=1))
    invalider_cache(rc)
    assert decider(rc, "caisse_validation", "V", centre=monde["cmr"]).autorise


def test_un_role_de_module_est_suspendu_quand_le_module_est_desactive(monde):
    from caef.habilitations.models import ModuleCentre

    vb = monde["u"]["vb.cmr"]
    assert decider(vb, "vente", "C", centre=monde["cmr"]).autorise
    ModuleCentre.objects.create(centre=monde["cmr"], module="boutique", statut="inactif",
                                date_effet=timezone.localdate(), decision_reference="DEC-FICTIVE-2",
                                decision_date=timezone.localdate(), motif="Fermeture fictive",
                                saisi_par=monde["u"]["adm.national"], valide_par=monde["u"]["dg.direction"],
                                valide_le=timezone.now())
    invalider_cache(vb)
    assert not decider(vb, "vente", "C", centre=monde["cmr"]).autorise
