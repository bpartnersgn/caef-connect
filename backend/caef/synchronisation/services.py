"""Appareils, jetons hors ligne et file « À résoudre » (OFF-06, OFF-05, RG-OFF-07, RG-OFF-08)."""

from django.db import transaction
from django.utils import timezone

from caef.commun.exceptions import AccesRefuse, RegleMetier
from caef.commun.services import enregistrer
from caef.habilitations.matrice import matrice
from caef.habilitations.services import affectations_actives, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import instantane, journaliser

from .authentification import emettre_jeton
from .models import Appareil, ResultatOperation, StatutAppareil, StatutConflit


def roles_hors_ligne(utilisateur, centre_id) -> set[str]:
    """Le mode hors ligne n'existe que pour les rôles de terrain du centre (RG-OFF-08)."""
    m = matrice()
    return {a.role_id for a in affectations_actives(utilisateur)
            if a.centre_id == centre_id and m.roles[a.role_id].hors_ligne}


def enroler(acteur, *, centre, libelle, utilisateur_principal=None, point_de_vente=None, serie_recu=None):
    """E-OFF-01 : par le RC ou l'admin. national ; une série de reçus par appareil du point de vente."""
    verifier(acteur, "appareil", "C", centre=centre)
    if point_de_vente is not None:
        if point_de_vente.centre_id != centre.pk:
            raise RegleMetier("Le point de vente appartient à un autre centre.")
        if not serie_recu:
            raise RegleMetier("Un appareil de point de vente reçoit une série de reçus (RG-BOU-01).")
    with transaction.atomic():
        a = Appareil.objects.create(centre=centre, libelle=libelle, utilisateur_principal=utilisateur_principal,
                                    point_de_vente=point_de_vente, serie_recu=serie_recu, enrole_par=acteur,
                                    cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=a, centre=centre, apres=instantane(a))
    return a


def revoquer(acteur, appareil, motif):
    """Effacement des données locales au premier contact ; les opérations déjà envoyées restent (CA-OFF-03)."""
    verifier(acteur, "appareil", "A", centre=appareil.centre_id)
    if appareil.statut == StatutAppareil.REVOQUE:
        raise RegleMetier("Appareil déjà révoqué.")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        appareil.statut = StatutAppareil.REVOQUE
        appareil.revoque_par = acteur
        appareil.revoque_le = timezone.now()
        appareil.motif_revocation = motif
        enregistrer(appareil, acteur, ["statut", "revoque_par", "revoque_le", "motif_revocation"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=appareil, centre=appareil.centre_id,
                    avant={"statut": "actif"}, apres={"statut": "revoque"}, motif=motif)
    return appareil


def delivrer_jeton(utilisateur, appareil) -> dict:
    """Après une connexion en ligne complète (double authentification comprise) : jeton lié à
    l'utilisateur et à l'appareil, valable 72 heures."""
    if appareil.statut != StatutAppareil.ACTIF:
        raise AccesRefuse("Appareil révoqué.", objet="appareil", action="L", centre_id=appareil.centre_id,
                          code="appareil_revoque")
    if not roles_hors_ligne(utilisateur, appareil.centre_id):
        raise AccesRefuse("Votre rôle travaille en ligne seulement (RG-OFF-08).", objet="appareil", action="L",
                          centre_id=appareil.centre_id)
    journaliser(ActionJournal.CONNEXION, utilisateur=utilisateur, objet=appareil, centre=appareil.centre_id,
                motif="Jeton hors ligne délivré")
    from django.conf import settings

    return {"jeton": emettre_jeton(utilisateur, appareil), "valable_heures": settings.CAEF["HORS_LIGNE_VALIDITE_HEURES"],
            "serie_recu": appareil.serie_recu, "dernier_numero_recu": appareil.dernier_numero_recu}


# --------------------------------------------------------------------------- file « À résoudre »

def resoudre_conflit(acteur, conflit, decision, motif=""):
    """Conflit de champ : garder la valeur du serveur ou la remplacer par celle de l'appareil (RC ou RA)."""
    verifier(acteur, "conflit_synchronisation", "V", centre=conflit.centre_id)
    if conflit.operation.resultat == ResultatOperation.ECRITURE_TARDIVE:
        raise RegleMetier("Une écriture tardive se traite par une régularisation.")
    if conflit.statut != StatutConflit.A_RESOUDRE:
        raise RegleMetier("Conflit déjà traité.")
    if decision not in (StatutConflit.GARDE_SERVEUR, StatutConflit.REMPLACE):
        raise RegleMetier("Décision attendue : garder ou remplacer.")
    with transaction.atomic():
        if decision == StatutConflit.REMPLACE:
            _remplacer_valeur(acteur, conflit)
        conflit.statut = decision
        conflit.resolu_par = acteur
        conflit.resolu_le = timezone.now()
        conflit.motif = motif
        conflit.save(update_fields=["statut", "resolu_par", "resolu_le", "motif"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet_type="conflit_synchronisation",
                    objet_id=conflit.pk, centre=conflit.centre_id,
                    apres={"decision": decision, "champ": conflit.champ}, motif=motif)
    return conflit


def _remplacer_valeur(acteur, conflit):
    from caef.beneficiaires.services import modifier_beneficiaire

    if conflit.objet_type != "beneficiaire":
        raise RegleMetier("Remplacement non pris en charge pour cet objet.")
    from caef.beneficiaires.models import Beneficiaire

    b = Beneficiaire.objects.get(pk=conflit.objet_id)
    modifier_beneficiaire(acteur, b, motif="Résolution d'un conflit de synchronisation",
                          **{conflit.champ: conflit.valeur_appareil})


def regulariser_ecriture_tardive(acteur, conflit, motif):
    """Le CPT rejoue l'opération datée du mois courant, référencée au mois corrigé (RG-OFF-07, RG-SRC-03)."""
    from .moteur import rejouer_en_regularisation

    verifier(acteur, "ecriture_tardive", "V", centre=conflit.centre_id)
    if conflit.operation.resultat != ResultatOperation.ECRITURE_TARDIVE or conflit.statut != StatutConflit.A_RESOUDRE:
        raise RegleMetier("Cette entrée n'est pas une écriture tardive à traiter.")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        reponse = rejouer_en_regularisation(acteur, conflit.operation, motif)
        conflit.statut = StatutConflit.REGULARISE
        conflit.resolu_par = acteur
        conflit.resolu_le = timezone.now()
        conflit.motif = motif
        conflit.save(update_fields=["statut", "resolu_par", "resolu_le", "motif"])
        op = conflit.operation
        type(op).objects.filter(pk=op.pk).update(regularisee=True)
    return reponse
