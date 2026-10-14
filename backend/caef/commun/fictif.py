"""Jeu de données fictif commun à la commande de démonstration et aux tests (règle 7)."""

from datetime import timedelta

from django.utils import timezone

from caef.habilitations.models import Affectation, ModuleCentre
from caef.identite.models import Utilisateur
from caef.referentiels.models import Centre, Periode, ReferentielValeur, ZoneTerritoriale

REFERENTIELS = {
    "categorie_formation": ["Couture", "Teinture", "Savonnerie", "Alphabétisation", "Gestion d'activité"],
    "categorie_produit": ["Textile", "Savon", "Artisanat"],
    "unite": ["Pièce", "Mètre", "Kilogramme"],
    "niveau_etudes": ["Aucun", "Primaire", "Secondaire", "Supérieur"],
    "situation_entree": ["Sans activité", "Activité informelle", "Salariée", "Élève"],
    "piece_identite_type": ["Carte d'identité", "Passeport", "Extrait de naissance"],
    "motif_rejet": ["Hors critères", "Dossier incomplet", "Doublon"],
    "motif_complement": ["Pièce manquante", "Information à préciser"],
    "motif_sortie": ["Déménagement", "Raison familiale", "Emploi trouvé", "Autre"],
    "categorie_partenaire": ["Entreprise", "Fondation", "Institution publique", "ONG"],
    "secteur": ["Banque", "Télécommunications", "Mines", "Distribution"],
    "origine_opportunite": ["Prospection", "Recommandation", "Appel à projets"],
    "motif_cloture": ["Budget indisponible", "Hors priorités du partenaire", "Sans réponse"],
}

# Personnes inventées : noms marqués comme fictifs, aucun lien avec des personnes réelles.
PRENOMS = ["Awa", "Fanta", "Mariama", "Kadiatou", "Hawa", "Aminata", "Djénabou", "Oumou", "Saran", "Néné",
           "Fatou", "Binta"]
NOMS = ["Fictive", "Exemple", "Essai", "Démo", "Modèle", "Témoin", "Prototype", "Maquette"]

COMPTES = [
    # identifiant, rôle, centre (None = national)
    ("adm.national", "ADM", None), ("dg.direction", "DG", None), ("rse.national", "RSE", None),
    ("se.national", "SE", None),
    ("rc.cmr", "RC", "CMR"), ("ra.cmr", "RA", "CMR"), ("aa.cmr", "AA", "CMR"), ("rp.cmr", "RP", "CMR"),
    ("fo.cmr", "FO", "CMR"), ("cpt.cmr", "CPT", "CMR"), ("vb.cmr", "VB", "CMR"), ("cmt.cmr", "CMT", "CMR"),
    ("rc.tsb", "RC", "TSB"), ("aa.tsb", "AA", "TSB"),
]


MODULES = ("boutique", "salle_exposition", "scolarite_paiements", "rse_centre")


def creer_socle(mot_de_passe=None, comptes=COMPTES) -> dict:
    """Zones, deux centres (CMR réel de démonstration, TSB fictif), référentiels, période de
    l'année, un compte par rôle et modules activés pour CMR. Sans mot de passe : comptes
    inutilisables pour la connexion (tests)."""
    jour = timezone.localdate()
    conakry = ZoneTerritoriale.objects.create(niveau="region", nom="Conakry", code="GN-C")
    dixinn = ZoneTerritoriale.objects.create(niveau="commune", nom="Dixinn", code="GN-C-DIX", parent=conakry)
    cmr = Centre.objects.create(code="CMR", nom="CAEF Cameroun", zone_territoriale=dixinn,
                                date_ouverture=jour - timedelta(days=900))
    tsb = Centre.objects.create(code="TSB", nom="Centre de test B", zone_territoriale=conakry, fictif=True)
    for referentiel, libelles in REFERENTIELS.items():
        for i, libelle in enumerate(libelles):
            ReferentielValeur.objects.create(referentiel=referentiel, code=f"{referentiel[:10]}-{i + 1}",
                                             libelle=libelle, ordre=i)
    periode = Periode.objects.create(type="annee", libelle=f"Année {jour.year}",
                                     date_debut=jour.replace(month=1, day=1), date_fin=jour.replace(month=12, day=31))
    centres = {"CMR": cmr, "TSB": tsb}
    comptes_crees = {}
    for identifiant, role, centre in comptes:
        u = Utilisateur.objects.create_user(identifiant, mot_de_passe, nom="Compte fictif",
                                            prenom=identifiant.split(".")[0].upper())
        Affectation.objects.create(utilisateur=u, role_id=role, centre=centres.get(centre), national=centre is None,
                                   date_debut=jour - timedelta(days=365), motif="Jeu de données fictif")
        comptes_crees[identifiant] = u
    adm = comptes_crees.get("adm.national")
    dg = comptes_crees.get("dg.direction")
    for module in MODULES:
        for centre in (cmr, tsb):
            ModuleCentre.objects.create(centre=centre, module=module, statut="actif",
                                        date_effet=jour - timedelta(days=365), decision_reference="DEC-FICTIVE-1",
                                        decision_date=jour - timedelta(days=366), motif="Jeu de données fictif",
                                        saisi_par=adm, valide_par=dg, valide_le=timezone.now())
    return {"zone": dixinn, "cmr": cmr, "tsb": tsb, "periode": periode, "u": comptes_crees}


def rv(referentiel, i=0):
    return ReferentielValeur.objects.filter(referentiel=referentiel).order_by("ordre")[i]
