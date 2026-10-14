"""Petites aides de construction pour les tests de scénarios (données fictives seulement)."""

from datetime import time, timedelta

from django.utils import timezone

from caef.commun.fictif import rv


def dossier_complet(i=0, zone=None):
    noms = ["Fictive", "Exemple", "Essai", "Démo", "Modèle", "Témoin"]
    return {"nom": noms[i], "prenoms": f"Prénom{i}", "sexe": "F", "annee_naissance": 1995 + i,
            "precision_naissance": "annee", "zone_residence": zone, "consentement_date": timezone.localdate(),
            "consentement_mode": "ecrit"}


def boutique(monde, prix=10000, stock=20):
    from caef.boutique import services as bou
    from caef.boutique.models import PointDeVente

    rc = monde["u"]["rc.cmr"]
    pdv = PointDeVente.objects.create(centre=monde["cmr"], nom="Boutique fictive", cree_par=rc)
    produit = bou.creer_produit(rc, pdv, nom="Savon fictif", categorie=rv("categorie_produit"), unite=rv("unite"),
                                origine="atelier_centre", prix=prix)
    bou.entrer_en_stock(rc, produit, type="entree_production", quantite=stock)
    return pdv, produit


def session_ouverte(monde, decalage_seance=0):
    from caef.formations import services as form
    from caef.formations.models import Formateur, Formation

    rp, rc = monde["u"]["rp.cmr"], monde["u"]["rc.cmr"]
    formation = Formation.objects.create(code="FOR-T-1", intitule="Formation fictive", portee="nationale",
                                         categorie=rv("categorie_formation"), objectifs="Objectifs fictifs",
                                         duree_heures=20)
    formateur = Formateur.objects.create(utilisateur=monde["u"]["fo.cmr"], nom="Fictif", prenom="FO",
                                         statut_intervenant="interne", cree_par=rc)
    formateur.centres.add(monde["cmr"])
    jour = timezone.localdate()
    s = form.creer_session(rp, formation=formation, centre=monde["cmr"], periode=monde["periode"],
                           date_debut=jour, date_fin=jour + timedelta(days=30), lieu="Salle fictive", capacite=10,
                           formateur_principal=formateur)
    seance = form.planifier_seance(rp, s, date=jour + timedelta(days=decalage_seance), heure_debut=time(9), heure_fin=time(11), formateur=formateur)
    form.ouvrir_session(rp, s)
    return formation, s, seance


def verrouiller_mois(monde, centre=None, jour=None):
    from caef.pilotage.models import ClotureMensuelle

    jour = jour or timezone.localdate()
    return ClotureMensuelle.objects.create(centre=centre or monde["cmr"], mois=f"{jour.year:04d}-{jour.month:02d}",
                                           statut="validee", verrouillee=True,
                                           verifiee_par=monde["u"]["cpt.cmr"], verifiee_le=timezone.now(),
                                           validee_par=monde["u"]["rc.cmr"], validee_le=timezone.now())
