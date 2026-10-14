"""Données de démonstration, entièrement fictives (règle 7 : aucune donnée réelle hors production).

    python manage.py generer_donnees_fictives

Le mot de passe des comptes de démonstration vient de CAEF_MOT_DE_PASSE_DEMO ; à défaut, il est
tiré au hasard et affiché une seule fois. Refusé en production.
"""

import secrets
from datetime import time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from caef.commun.fictif import NOMS, PRENOMS, creer_socle, rv
from caef.referentiels.models import Centre


class Command(BaseCommand):
    help = "Crée un jeu de données entièrement fictif (développement et recette seulement)."

    def handle(self, *args, **options):
        if settings.ENVIRONNEMENT == "production":
            raise CommandError("Refusé : aucune donnée fictive en production.")
        if Centre.objects.filter(code="CMR").exists():
            raise CommandError("Les données fictives existent déjà (centre CMR présent).")
        mot_de_passe = settings.CAEF.get("MOT_DE_PASSE_DEMO") or secrets.token_urlsafe(12)
        with transaction.atomic():
            self._socle(mot_de_passe)
            self._metier()
        self.stdout.write(self.style.SUCCESS("Données fictives créées."))
        if not settings.CAEF.get("MOT_DE_PASSE_DEMO"):
            self.stdout.write(f"Mot de passe des comptes de démonstration (affiché une seule fois) : {mot_de_passe}")

    def _socle(self, mot_de_passe):
        monde = creer_socle(mot_de_passe)
        self.zone, self.cmr, self.periode, self.u = monde["zone"], monde["cmr"], monde["periode"], monde["u"]

    # ------------------------------------------------------------------ métier, par les services
    def _metier(self):
        from caef.beneficiaires import services as ben
        from caef.boutique import services as bou
        from caef.boutique.models import PointDeVente
        from caef.formations import services as form
        from caef.formations.models import Formateur, Formation
        from caef.partenaires import services as par

        jour = timezone.localdate()
        rc, aa, rp, fo, vb = (self.u[k] for k in ("rc.cmr", "aa.cmr", "rp.cmr", "fo.cmr", "vb.cmr"))

        formation = Formation.objects.create(code="FOR-FICT-1", intitule="Couture de base (fictive)",
                                             portee="nationale", categorie=rv("categorie_formation"),
                                             objectifs="Maîtriser les points de base.", duree_heures=40,
                                             cree_par=self.u["adm.national"])
        formateur = Formateur.objects.create(utilisateur=fo, nom="Compte fictif", prenom="FO",
                                             statut_intervenant="interne", cree_par=rc)
        formateur.centres.add(self.cmr)
        debut = jour - timedelta(days=jour.weekday())
        session = form.creer_session(rp, formation=formation, centre=self.cmr, periode=self.periode,
                                     date_debut=debut, date_fin=debut + timedelta(days=60), lieu="Salle 1",
                                     capacite=20, formateur_principal=formateur)
        seance = form.planifier_seance(rp, session, date=debut, heure_debut=time(9), heure_fin=time(12),
                                       formateur=formateur, theme="Ouverture")
        form.ouvrir_session(rp, session)

        inscriptions = []
        for i in range(8):
            identite = {"nom": NOMS[i % len(NOMS)], "prenoms": PRENOMS[i], "sexe": "F",
                        "annee_naissance": 1990 + i, "precision_naissance": "annee", "zone_residence": self.zone,
                        "consentement_date": jour, "consentement_mode": "ecrit",
                        "niveau_etudes": rv("niveau_etudes", i % 4)}
            cand = ben.creer_candidature(aa, centre=self.cmr, formation=formation, identite=identite)
            ben.soumettre_candidature(aa, cand)
            ben.valider_candidature(rc, cand)
            inscriptions.append(form.inscrire(rp, cand, session))
        if seance.date <= jour:
            form.saisir_presences(fo, seance, {str(ins.pk): ("presente" if k % 4 else "absente")
                                               for k, ins in enumerate(inscriptions)})

        pdv = PointDeVente.objects.create(centre=self.cmr, nom="Boutique CAEF Cameroun", cree_par=rc)
        produit = bou.creer_produit(rc, pdv, nom="Pagne teint (fictif)", categorie=rv("categorie_produit"),
                                    unite=rv("unite"), origine="atelier_centre", prix=150000)
        bou.entrer_en_stock(rc, produit, type="entree_production", quantite=30)
        bou.ouvrir_caisse(vb, pdv, fond_de_caisse=200000)
        bou.vendre(vb, pdv, lignes=[{"produit": produit, "quantite": 2}],
                   reglements=[{"mode": "especes", "montant": 300000}])

        partenaire = par.creer_partenaire(self.u["rse.national"], raison_sociale="Entreprise Fictive SA",
                                          sigle="EFSA", categorie=rv("categorie_partenaire"), secteur=rv("secteur"),
                                          responsable_suivi=self.u["rse.national"])
        par.creer_opportunite(self.u["rse.national"], partenaire=partenaire, intitule="Appui fictif à la couture",
                              origine=rv("origine_opportunite"), centres=[self.cmr],
                              responsable=self.u["rse.national"], prochaine_action="Premier rendez-vous",
                              date_prochaine_action=jour + timedelta(days=7))
