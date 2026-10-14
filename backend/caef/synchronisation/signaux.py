"""Publication automatique au journal des changements des objets lus par les appareils (DAT § 4.5).

Chaque enregistrement d'un objet synchronisé ajoute une entrée numérotée pour son centre, dans la
même transaction ; les appareils la lisent au curseur.
"""

from django.db.models.signals import post_save

from .journal import publier
from .models import NatureChangement

# modèle → (chemin vers le centre, objet publié : lui-même ou un objet lié)
PUBLIES = {
    "beneficiaires.Beneficiaire": ("centre_rattachement_id", None),
    "beneficiaires.Candidature": ("centre_id", None),
    "formations.SessionFormation": ("centre_id", None),
    "formations.Seance": ("session.centre_id", None),
    "formations.Inscription": ("session.centre_id", None),
    "formations.Presence": ("seance.session.centre_id", None),
    "boutique.Produit": ("point_de_vente.centre_id", None),
    "boutique.PrixProduit": ("produit.point_de_vente.centre_id", "produit"),
    "boutique.MouvementStock": ("produit.point_de_vente.centre_id", "produit"),
    "boutique.SessionCaisse": ("point_de_vente.centre_id", None),
    "facturation.Echeance": ("centre_id", None),
}


def _chemin(o, chemin):
    for morceau in chemin.split("."):
        o = getattr(o, morceau)
        if o is None:
            return None
    return o


def _recepteur(chemin_centre, lien):
    def recevoir(sender, instance, created, raw=False, **kwargs):
        if raw:
            return
        cible = getattr(instance, lien) if lien else instance
        nature = NatureChangement.CREATION if created and not lien else NatureChangement.MODIFICATION
        if getattr(cible, "archive", False):
            nature = NatureChangement.ARCHIVAGE
        publier(_chemin(instance, chemin_centre), cible, nature)
    return recevoir


def connecter():
    from django.apps import apps

    for chemin_modele, (chemin_centre, lien) in PUBLIES.items():
        post_save.connect(_recepteur(chemin_centre, lien), sender=apps.get_model(chemin_modele), weak=False,
                          dispatch_uid=f"caef_publier_{chemin_modele}")
