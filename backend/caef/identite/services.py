"""Connexion, verrouillage, double authentification et gestion des comptes (USR, SEC-08, SEC-11)."""

import hashlib
import secrets
from datetime import timedelta

import pyotp
from django.conf import settings
from django.contrib.auth import password_validation
from django.db import transaction
from django.utils import timezone

from caef.commun.exceptions import AccesRefuse, RegleMetier
from caef.habilitations.matrice import matrice
from caef.journal.models import ActionJournal
from caef.journal.services import journaliser

from .models import StatutUtilisateur, Utilisateur

CLE_OTP_VERIFIE = "caef_otp_verifie"
EMETTEUR_TOTP = "CAEF Connect"
MESSAGE_ECHEC = "Identifiant ou mot de passe incorrect."


def _p(nom):
    return settings.CAEF[nom]


def double_auth_obligatoire(utilisateur) -> bool:
    """ADM, DG et CPT (DAT § 5.1, Matrice § 2)."""
    from caef.habilitations.models import Affectation

    roles = matrice().roles
    codes = set(
        Affectation.objects.filter(utilisateur=utilisateur, archive=False).values_list("role_id", flat=True)
    )
    return any(roles[c].double_auth == "obligatoire" for c in codes if c in roles)


def _empreinte_code(code: str) -> str:
    return hashlib.sha256(code.strip().replace(" ", "").encode()).hexdigest()


def verifier_code_double_auth(utilisateur, code: str | None) -> bool:
    if not code or not utilisateur.secret_double_auth:
        return False
    code = code.strip().replace(" ", "")
    if pyotp.TOTP(utilisateur.secret_double_auth).verify(code, valid_window=1):
        return True
    empreinte = _empreinte_code(code)
    if empreinte in (utilisateur.codes_secours or []):
        utilisateur.codes_secours = [c for c in utilisateur.codes_secours if c != empreinte]
        utilisateur.save(update_fields=["codes_secours"])
        return True
    return False


def _enregistrer_echec(utilisateur, motif):
    """Cinq échecs consécutifs bloquent 15 minutes, dix dans l'heure suspendent (RG-ADM-09)."""
    maintenant = timezone.now()
    utilisateur.echecs_consecutifs += 1
    recents = [h for h in (utilisateur.echecs_horodatages or [])
               if maintenant.timestamp() - h < 3600] + [maintenant.timestamp()]
    utilisateur.echecs_horodatages = recents
    if len(recents) >= _p("ECHECS_SUSPENSION_HEURE"):
        utilisateur.statut = StatutUtilisateur.SUSPENDU
    elif utilisateur.echecs_consecutifs >= _p("ECHECS_BLOCAGE"):
        utilisateur.bloque_jusqua = maintenant + timedelta(minutes=_p("BLOCAGE_MINUTES"))
        utilisateur.echecs_consecutifs = 0
    utilisateur.save(update_fields=["echecs_consecutifs", "echecs_horodatages", "bloque_jusqua", "statut"])
    journaliser(ActionJournal.ECHEC_CONNEXION, utilisateur=None, objet=utilisateur, motif=motif)


class ResultatConnexion:
    def __init__(self, utilisateur, double_auth_a_configurer=False):
        self.utilisateur = utilisateur
        self.double_auth_a_configurer = double_auth_a_configurer


def authentifier(identifiant: str, mot_de_passe: str, code: str | None = None) -> ResultatConnexion:
    """Contrôle complet d'une connexion ; lève AccesRefuse avec un message clair."""
    from caef.habilitations.services import affectations_actives

    utilisateur = Utilisateur.objects.filter(identifiant_connexion=identifiant).first()
    if utilisateur is None:
        journaliser(ActionJournal.ECHEC_CONNEXION, objet_type="utilisateur",
                    motif=f"Identifiant inconnu : {identifiant[:60]}")
        raise AccesRefuse(MESSAGE_ECHEC, code="echec_connexion")
    maintenant = timezone.now()
    if utilisateur.bloque_jusqua and utilisateur.bloque_jusqua > maintenant:
        journaliser(ActionJournal.ECHEC_CONNEXION, objet=utilisateur, motif="Compte temporairement bloqué")
        raise AccesRefuse("Trop d'échecs : compte bloqué pendant 15 minutes.", code="compte_bloque")
    if not utilisateur.check_password(mot_de_passe):
        _enregistrer_echec(utilisateur, "Mot de passe incorrect")
        raise AccesRefuse(MESSAGE_ECHEC, code="echec_connexion")
    if utilisateur.statut != StatutUtilisateur.ACTIF:
        journaliser(ActionJournal.ECHEC_CONNEXION, objet=utilisateur, motif=f"Compte {utilisateur.statut}")
        raise AccesRefuse("Ce compte est suspendu ou désactivé : contactez l'administrateur.", code="compte_inactif")
    if not affectations_actives(utilisateur):
        journaliser(ActionJournal.ECHEC_CONNEXION, objet=utilisateur, motif="Aucune affectation active")
        raise AccesRefuse("Aucune affectation active pour ce compte.", code="sans_affectation")

    a_configurer = False
    if utilisateur.double_auth_active:
        if not verifier_code_double_auth(utilisateur, code):
            _enregistrer_echec(utilisateur, "Code de double authentification absent ou invalide")
            raise AccesRefuse("Code de double authentification absent ou invalide.", code="double_auth_invalide")
    elif double_auth_obligatoire(utilisateur):
        a_configurer = True

    utilisateur.echecs_consecutifs = 0
    utilisateur.bloque_jusqua = None
    utilisateur.last_login = maintenant
    utilisateur.save(update_fields=["echecs_consecutifs", "bloque_jusqua", "last_login"])
    journaliser(ActionJournal.CONNEXION, utilisateur=utilisateur, objet=utilisateur)
    return ResultatConnexion(utilisateur, double_auth_a_configurer=a_configurer)


def initialiser_double_auth(utilisateur) -> str:
    """Nouveau secret TOTP (non actif tant qu'un code n'est pas confirmé). Renvoie l'URI d'enrôlement."""
    secret = pyotp.random_base32()
    utilisateur.secret_double_auth = secret
    utilisateur.double_auth_active = False
    utilisateur.save(update_fields=["secret_double_auth", "double_auth_active"])
    return pyotp.TOTP(secret).provisioning_uri(name=utilisateur.identifiant_connexion, issuer_name=EMETTEUR_TOTP)


def confirmer_double_auth(utilisateur, code: str) -> list[str]:
    if not utilisateur.secret_double_auth or not pyotp.TOTP(utilisateur.secret_double_auth).verify(
            (code or "").strip(), valid_window=1):
        raise RegleMetier("Code invalide : vérifiez l'heure du téléphone et réessayez.")
    codes = [f"{secrets.randbelow(10**8):08d}" for _ in range(8)]
    with transaction.atomic():
        utilisateur.double_auth_active = True
        utilisateur.codes_secours = [_empreinte_code(c) for c in codes]
        utilisateur.save(update_fields=["double_auth_active", "codes_secours"])
        journaliser(ActionJournal.DROITS, utilisateur=utilisateur, objet=utilisateur,
                    apres={"double_auth_active": True}, motif="Activation de la double authentification")
    return codes


def desactiver_double_auth(utilisateur, acteur):
    if double_auth_obligatoire(utilisateur):
        raise RegleMetier("La double authentification est obligatoire pour ce rôle (ADM, DG, CPT).")
    with transaction.atomic():
        utilisateur.double_auth_active = False
        utilisateur.secret_double_auth = None
        utilisateur.codes_secours = []
        utilisateur.save(update_fields=["double_auth_active", "secret_double_auth", "codes_secours"])
        journaliser(ActionJournal.DROITS, utilisateur=acteur, objet=utilisateur,
                    apres={"double_auth_active": False}, motif="Désactivation de la double authentification")


def changer_mot_de_passe(utilisateur, ancien: str, nouveau: str):
    if not utilisateur.check_password(ancien):
        raise RegleMetier("L'ancien mot de passe est incorrect.")
    password_validation.validate_password(nouveau, utilisateur)
    with transaction.atomic():
        utilisateur.set_password(nouveau)
        utilisateur.mot_de_passe_temporaire = False
        utilisateur.save(update_fields=["password", "mot_de_passe_temporaire"])
        journaliser(ActionJournal.MODIFICATION, utilisateur=utilisateur, objet=utilisateur,
                    motif="Changement de mot de passe")


def mot_de_passe_temporaire(utilisateur, acteur) -> str:
    """RG-ADM-10 : à défaut de courriel, l'admin. génère un mot de passe temporaire."""
    temporaire = secrets.token_urlsafe(12)
    with transaction.atomic():
        utilisateur.set_password(temporaire)
        utilisateur.mot_de_passe_temporaire = True
        utilisateur.bloque_jusqua = None
        utilisateur.echecs_consecutifs = 0
        utilisateur.save(update_fields=["password", "mot_de_passe_temporaire", "bloque_jusqua",
                                        "echecs_consecutifs"])
        journaliser(ActionJournal.DROITS, utilisateur=acteur, objet=utilisateur,
                    motif="Mot de passe temporaire généré")
    return temporaire


def changer_statut(utilisateur, statut, acteur, motif):
    """Suspension, désactivation ou réactivation, journalisées ; la désactivation coupe les
    sessions dès la requête suivante (RG-ADM-07)."""
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    avant = utilisateur.statut
    with transaction.atomic():
        utilisateur.statut = statut
        if statut == StatutUtilisateur.ACTIF:
            utilisateur.echecs_horodatages = []
            utilisateur.bloque_jusqua = None
        utilisateur.modifie_le = timezone.now()
        utilisateur.save(update_fields=["statut", "echecs_horodatages", "bloque_jusqua", "modifie_le"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=utilisateur,
                    avant={"statut": avant}, apres={"statut": statut}, motif=motif)
    if statut != StatutUtilisateur.ACTIF:
        _fermer_sessions(utilisateur)


def _fermer_sessions(utilisateur):
    from django.contrib.sessions.models import Session

    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        if str(session.get_decoded().get("_auth_user_id")) == str(utilisateur.pk):
            session.delete()


def suspendre_comptes_inactifs():
    """RG-ADM-08 : compte sans connexion depuis 90 jours → suspendu, RC notifié."""
    limite = timezone.now() - timedelta(days=_p("INACTIVITE_COMPTE_JOURS"))
    suspendus = []
    for u in Utilisateur.objects.filter(statut=StatutUtilisateur.ACTIF, last_login__lt=limite):
        changer_statut(u, StatutUtilisateur.SUSPENDU, None, "Aucune connexion depuis 90 jours (RG-ADM-08)")
        suspendus.append(u)
    if suspendus:
        from caef.notifications.services import notifier_responsables_des_centres_de

        for u in suspendus:
            notifier_responsables_des_centres_de(u, "compte_suspendu", f"Compte suspendu : {u.nom_complet}")
    return suspendus
