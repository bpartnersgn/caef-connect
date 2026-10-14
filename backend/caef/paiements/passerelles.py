"""Interface interne « passerelle Mobile Money » et ses adaptateurs (DAT § 4.6).

Les modules métier ne parlent qu'à cette interface : initier, consulter, vérifier et lire une
notification, rembourser, lire le relevé. Le choix de l'opérateur ou de l'agrégateur (H16) n'est
pas fait : l'adaptateur se choisit par configuration (CAEF_PASSERELLE_MOBILE_MONEY).

- « declaratif » : repli sans opérateur ; le Mobile Money est déclaré avec sa référence.
- « simulateur » : passerelle fictive signée HMAC, pour le développement et la recette ; refusée
  en production. Aucun appel réel hors production (DAT § 4.6).

Le code secret de la payeuse n'est jamais demandé, transmis ni stocké (RG-PAY-05).
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings

from caef.commun.exceptions import RegleMetier


@dataclass
class EtatOperateur:
    """Ce que l'opérateur dit d'un paiement ; le montant est le sien, jamais celui du client."""

    statut: str  # en_attente, confirme, echoue
    identifiant_operateur: str = ""
    montant: Decimal | None = None
    commission: Decimal | None = None
    motif: str = ""
    reference: str = ""  # référence interne (paiement) ou référence d'échéance (parcours B)
    brut: dict | None = None


class Passerelle:
    code = "abstraite"
    accepte_demandes = False
    accepte_remboursements = False

    def initier(self, paiement) -> EtatOperateur:
        raise NotImplementedError

    def consulter(self, paiement) -> EtatOperateur:
        raise NotImplementedError

    def verifier_notification(self, corps: bytes, entetes: dict) -> bool:
        raise NotImplementedError

    def lire_notification(self, corps: bytes) -> EtatOperateur:
        raise NotImplementedError

    def rembourser(self, paiement, montant) -> EtatOperateur | None:
        return None


class PasserelleDeclarative(Passerelle):
    """Sans contrat marchand : aucune demande possible, aucune notification acceptée."""

    code = "declaratif"

    def initier(self, paiement):
        raise RegleMetier("Aucune passerelle Mobile Money n'est active : déclarez le paiement avec son identifiant "
                          "de transaction.", code="passerelle_inactive")

    def consulter(self, paiement):
        return EtatOperateur(statut="en_attente")

    def verifier_notification(self, corps, entetes):
        return False

    def lire_notification(self, corps):
        raise RegleMetier("Aucune passerelle active.")


class PasserelleSimulateur(Passerelle):
    """Passerelle fictive signée HMAC-SHA256 (en-tête X-Signature), pour les tests et la recette."""

    code = "simulateur"
    accepte_demandes = True
    accepte_remboursements = True

    def __init__(self):
        if settings.ENVIRONNEMENT == "production":
            raise RuntimeError("Le simulateur de passerelle est interdit en production.")
        self.secret = (settings.PASSERELLE_SIMULATEUR_SECRET or "").encode()

    def signer(self, corps: bytes) -> str:
        return hmac.new(self.secret, corps, hashlib.sha256).hexdigest()

    def initier(self, paiement):
        return EtatOperateur(statut="en_attente", reference=str(paiement.pk))

    def consulter(self, paiement):
        from .models import TransactionPasserelle

        t = TransactionPasserelle.objects.filter(paiement=paiement, fournisseur=self.code).order_by("-recu_le").first()
        if t is None:
            return EtatOperateur(statut="en_attente")
        return EtatOperateur(statut=t.statut_operateur, identifiant_operateur=t.identifiant_operateur,
                             montant=t.montant, commission=t.commission)

    def verifier_notification(self, corps, entetes):
        if not self.secret:
            return False
        signature = entetes.get("X-Signature") or entetes.get("x-signature") or ""
        return hmac.compare_digest(self.signer(corps), signature)

    def lire_notification(self, corps):
        d = json.loads(corps)
        return EtatOperateur(
            statut={"SUCCESS": "confirme", "FAILED": "echoue", "PENDING": "en_attente"}.get(d["status"], "echoue"),
            identifiant_operateur=d["transaction_id"], montant=Decimal(str(d["amount"])),
            commission=Decimal(str(d["fee"])) if d.get("fee") is not None else None,
            motif=d.get("reason", ""), reference=d.get("reference", ""), brut=d)

    def rembourser(self, paiement, montant):
        return EtatOperateur(statut="confirme", identifiant_operateur=f"RMB-{paiement.identifiant_transaction}",
                             montant=Decimal(montant))


ADAPTATEURS = {"declaratif": PasserelleDeclarative, "simulateur": PasserelleSimulateur}


def passerelle(code: str | None = None) -> Passerelle:
    code = code or settings.CAEF["PASSERELLE_MOBILE_MONEY"]
    if code not in ADAPTATEURS:
        raise RegleMetier(f"Passerelle inconnue : {code}.")
    return ADAPTATEURS[code]()
