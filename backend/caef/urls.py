"""Routes de l'API REST /api/v1 (DAT § 4.2)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from caef.beneficiaires import api as beneficiaires
from caef.boutique import api as boutique
from caef.conventions import api as conventions
from caef.documents import api as documents
from caef.facturation import api as facturation
from caef.formations import api as formations
from caef.habilitations import api as habilitations
from caef.identite import api as identite
from caef.paiements import api as paiements
from caef.partenaires import api as partenaires
from caef.pilotage import api as pilotage
from caef.synchronisation import api as synchronisation

r = DefaultRouter(trailing_slash=True)
ROUTES = [
    # administration
    ("utilisateurs", identite.VueUtilisateurs, "utilisateur"),
    ("centres", habilitations.VueCentres, "centre"),
    ("referentiels", habilitations.VueReferentiels, "referentiel"),
    ("zones", habilitations.VueZones, "zone"),
    ("periodes", habilitations.VuePeriodes, "periode"),
    ("affectations", habilitations.VueAffectations, "affectation"),
    ("interims", habilitations.VueInterims, "interim"),
    ("modules-centre", habilitations.VueModulesCentre, "module-centre"),
    ("matrice", habilitations.VueMatrice, "matrice"),
    ("journal", habilitations.VueJournal, "journal"),
    ("notifications", habilitations.VueNotifications, "notification"),
    # bénéficiaires
    ("beneficiaires", beneficiaires.VueBeneficiaires, "beneficiaire"),
    ("candidatures", beneficiaires.VueCandidatures, "candidature"),
    ("transferts", beneficiaires.VueTransferts, "transfert"),
    ("doublons", beneficiaires.VuePairesDoublons, "doublon"),
    ("fusions", beneficiaires.VueFusions, "fusion"),
    # formations
    ("formations", formations.VueFormations, "formation"),
    ("formateurs", formations.VueFormateurs, "formateur"),
    ("sessions", formations.VueSessions, "session"),
    ("seances", formations.VueSeances, "seance"),
    ("inscriptions", formations.VueInscriptions, "inscription"),
    ("presences", formations.VuePresences, "presence"),
    ("evaluations", formations.VueEvaluations, "evaluation"),
    ("attestations", formations.VueAttestations, "attestation"),
    # documents
    ("documents", documents.VueDocuments, "document"),
    # partenariats
    ("partenaires", partenaires.VuePartenaires, "partenaire"),
    ("interlocuteurs", partenaires.VueInterlocuteurs, "interlocuteur"),
    ("interactions", partenaires.VueInteractions, "interaction"),
    ("opportunites", partenaires.VueOpportunites, "opportunite"),
    ("fiches-projet", partenaires.VueFichesProjet, "fiche-projet"),
    ("programmes", conventions.VueProgrammes, "programme"),
    ("propositions", conventions.VuePropositions, "proposition"),
    ("conventions", conventions.VueConventions, "convention"),
    ("engagements", conventions.VueEngagements, "engagement"),
    ("contributions", conventions.VueContributions, "contribution"),
    # boutique
    ("points-de-vente", boutique.VuePointsDeVente, "point-de-vente"),
    ("produits", boutique.VueProduits, "produit"),
    ("mouvements-stock", boutique.VueMouvements, "mouvement-stock"),
    ("ventes", boutique.VueVentes, "vente"),
    ("caisses", boutique.VueCaisses, "caisse"),
    ("inventaires", boutique.VueInventaires, "inventaire"),
    ("reversements", boutique.VueReversements, "reversement"),
    # scolarité et paiements
    ("services-payants", facturation.VueServices, "service-payant"),
    ("echeances", facturation.VueEcheances, "echeance"),
    ("exonerations", facturation.VueExonerations, "exoneration"),
    ("situations", facturation.VueSituation, "situation"),
    ("paiements", paiements.VuePaiements, "paiement"),
    ("releves-operateur", paiements.VueReleves, "releve-operateur"),
    ("remboursements", paiements.VueRemboursements, "remboursement"),
    # pilotage
    ("clotures", pilotage.VueClotures, "cloture"),
    ("indicateurs", pilotage.VueIndicateurs, "indicateur"),
    ("fiches-indicateurs", pilotage.VueFichesIndicateurs, "fiche-indicateur"),
    ("rapports", pilotage.VueRapports, "rapport"),
    # hors ligne
    ("appareils", synchronisation.VueAppareils, "appareil"),
    ("conflits", synchronisation.VueConflits, "conflit"),
]
for prefixe, vue, nom in ROUTES:
    r.register(prefixe, vue, basename=nom)

urlpatterns = [
    path("auth/connexion/", identite.Connexion.as_view(), name="connexion"),
    path("auth/deconnexion/", identite.Deconnexion.as_view(), name="deconnexion"),
    path("auth/moi/", identite.Moi.as_view(), name="moi"),
    path("auth/double-auth/<str:etape>/", identite.DoubleAuth.as_view(), name="double-auth"),
    path("auth/mot-de-passe/", identite.MotDePasse.as_view(), name="mot-de-passe"),
    path("documents/telecharger/<str:jeton>/", documents.Telechargement.as_view(), name="telechargement"),
    path("paiements/notifications/<str:fournisseur>/", paiements.NotificationPasserelle.as_view(),
         name="notification-passerelle"),
    path("synchronisation/operations/", synchronisation.Operations.as_view(), name="sync-operations"),
    path("synchronisation/changements/", synchronisation.Changements.as_view(), name="sync-changements"),
    path("synchronisation/rejets/", synchronisation.MesRejets.as_view(), name="sync-rejets"),
    path("", include(r.urls)),
]
