"""Encaissements, Mobile Money, affectations, rapprochement et remboursements (SFD § 12).

Seule la confirmation de l'opérateur fait d'un paiement un encaissement, avec le montant de
l'opérateur (RG-PAY-03). Une transaction de l'opérateur n'est enregistrée qu'une fois (RG-PAY-04).
CAEF Connect ne détient jamais les fonds et ne voit jamais le code secret de la payeuse.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from caef.commun.champs import verifier_gnf_entier
from caef.commun.codes import prochain_numero
from caef.commun.contexte import contexte
from caef.commun.exceptions import AccesRefuse, RegleMetier, SeparationDesTaches
from caef.commun.services import enregistrer, exiger_statut, maintenant, origine, parametre
from caef.habilitations.services import verifier
from caef.journal.models import ActionJournal
from caef.journal.services import instantane, journaliser
from caef.notifications.services import notifier_role
from caef.pilotage.verrou import verifier_mois_ouvert

from .models import (STATUTS_ENCAISSES, AffectationPaiement, CanalPaiement, ExecutionRemboursement,
                     LigneReleveOperateur, Paiement, Remboursement, StatutPaiement, StatutRapprochement,
                     StatutRemboursement, TransactionPasserelle, TypeTransaction)
from .passerelles import passerelle


def _gnf(v, libelle="Le montant"):
    from django.core.exceptions import ValidationError

    try:
        verifier_gnf_entier(v, libelle)
    except ValidationError as e:
        raise RegleMetier(e.messages[0], code="montant_non_entier")
    return Decimal(v)


def _recu(centre, numero_propose=None):
    """Série de l'appareil (RG-PAY-08, RG-BOU-01) ; en ligne sans appareil, série « -P » du centre."""
    from caef.synchronisation.models import Appareil

    ctx = contexte()
    if ctx.appareil_id:
        a = Appareil.objects.select_for_update().get(pk=ctx.appareil_id)
        if a.serie_recu:
            numero = numero_propose or a.dernier_numero_recu + 1
            if numero <= a.dernier_numero_recu:
                raise RegleMetier("Numéro de reçu déjà attribué sur cet appareil.", code="recu_deja_attribue")
            a.dernier_numero_recu = numero
            a.save(update_fields=["dernier_numero_recu"])
            return a.serie_recu, numero
    serie = f"{centre.code}-P"
    return serie, prochain_numero(f"RECU:{centre.pk}:{serie}")


def _echeances_ordonnees(echeances):
    """RG-PAY-08 : de la plus ancienne à la plus récente, sauf choix contraire."""
    return sorted(echeances, key=lambda e: (e.date_limite, e.rang))


def _verifier_echeances(centre, echeances):
    for e in echeances:
        if e.centre_id != centre.pk:
            raise RegleMetier("Une échéance appartient à un autre centre.")
        if e.statut in ("payee", "exoneree", "annulee"):
            raise RegleMetier(f"L'échéance {e.reference_paiement} n'est plus due.")


# --------------------------------------------------------------------------- encaissements

def encaisser_especes(acteur, centre, *, montant, echeances, repartition=None, numero_recu=None):
    """Espèces : confirmé à l'encaissement, reçu émis ; affecté de la plus ancienne échéance à la plus récente."""
    verifier(acteur, "encaissement", "C", centre=centre)
    montant = _gnf(montant)
    if montant <= 0:
        raise RegleMetier("Le montant doit être positif.")
    _verifier_echeances(centre, echeances)
    quand = maintenant()
    verifier_mois_ouvert(centre.pk, quand)
    with transaction.atomic():
        serie, numero = _recu(centre, numero_recu)
        p = Paiement.objects.create(centre=centre, canal=CanalPaiement.ESPECES, montant_attendu=montant,
                                    montant_confirme=montant, montant_net=montant, statut=StatutPaiement.CONFIRME,
                                    serie_recu=serie, numero_recu=numero, encaisse_par=acteur, confirme_le=quand,
                                    affectation_prevue=_prevue(echeances, repartition), cree_par=acteur, **origine())
        _affecter_automatiquement(p)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=p, centre=centre,
                    apres={"canal": p.canal, "montant": str(montant), "recu": f"{serie}-{numero:06d}"})
    return p


def _prevue(echeances, repartition=None):
    repartition = repartition or {}
    return [{"echeance": str(e.pk), "montant": str(repartition[str(e.pk)]) if str(e.pk) in repartition else None}
            for e in _echeances_ordonnees(echeances)]


def demander_paiement(acteur, centre, *, telephone_payeuse, echeances, montant=None, fournisseur=None):
    """Parcours A, en ligne seulement : le serveur envoie la demande ; la payeuse valide sur son
    téléphone avec son code secret, jamais saisi ici (RG-PAY-05)."""
    verifier(acteur, "encaissement", "C", centre=centre)
    if contexte().hors_ligne:
        raise RegleMetier("La demande de paiement n'est disponible qu'en ligne : déclarez le paiement.",
                          code="demande_hors_ligne")
    if not telephone_payeuse:
        raise RegleMetier("Le numéro de la payeuse est obligatoire.")
    _verifier_echeances(centre, echeances)
    if montant is None:
        from caef.facturation.services import recalculer_echeance

        montant = sum((recalculer_echeance(e).restant_du for e in echeances), Decimal(0))
    montant = _gnf(montant)
    if montant <= 0:
        raise RegleMetier("Le montant doit être positif.")
    gw = passerelle(fournisseur)
    if not gw.accepte_demandes:
        gw.initier(None)  # lève l'erreur explicite de l'adaptateur
    with transaction.atomic():
        p = Paiement.objects.create(centre=centre, canal=CanalPaiement.MOBILE_MONEY_DEMANDE, fournisseur=gw.code,
                                    montant_attendu=montant, telephone_payeuse=telephone_payeuse,
                                    statut=StatutPaiement.INITIE, encaisse_par=acteur,
                                    affectation_prevue=_prevue(echeances), cree_par=acteur, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=p, centre=centre,
                    apres={"canal": p.canal, "montant_attendu": str(montant)})
    etat = gw.initier(p)
    if etat.statut == "en_attente":
        p.statut = StatutPaiement.EN_ATTENTE
        p.save(update_fields=["statut"])
        _programmer_consultations(p)
    return p


def _programmer_consultations(p):
    """Sans notification, le statut est consulté à 1, 5, 15 et 60 minutes (RG-PAY-05)."""
    try:
        from .taches import consulter_paiement

        for minutes in parametre("PAIEMENT_CONSULTATIONS_MINUTES"):
            consulter_paiement.apply_async(args=[str(p.pk), minutes], countdown=minutes * 60)
    except Exception:  # file de tâches indisponible : la tâche périodique de rattrapage prendra le relais
        pass


def declarer_mobile_money(acteur, centre, *, identifiant_transaction, montant_declare, echeances=(),
                          telephone="", numero_recu=None, usage_boutique=False):
    """Parcours C (RG-PAY-07) : identifiant lu sur le SMS, reçu provisoire « Déclaré » ; jamais compté
    comme encaissé avant le rapprochement. Un identifiant déjà confirmé est refusé (RG-PAY-04)."""
    if not usage_boutique:
        verifier(acteur, "encaissement", "C", centre=centre)
    identifiant = (identifiant_transaction or "").strip()
    if not identifiant:
        raise RegleMetier("L'identifiant de transaction est obligatoire.")
    if Paiement.objects.filter(identifiant_transaction=identifiant).exclude(
            statut__in=[StatutPaiement.ECHOUE, StatutPaiement.EXPIRE]).exists() or \
            TransactionPasserelle.objects.filter(identifiant_operateur=identifiant, paiement__isnull=False).exists():
        raise RegleMetier("Cet identifiant de transaction est déjà enregistré.", code="transaction_deja_enregistree")
    montant = _gnf(montant_declare)
    _verifier_echeances(centre, echeances)
    with transaction.atomic():
        serie, numero = _recu(centre, numero_recu) if not usage_boutique else ("", None)
        p = Paiement.objects.create(centre=centre, canal=CanalPaiement.MOBILE_MONEY_DECLARE,
                                    montant_attendu=montant, telephone_payeuse=telephone,
                                    identifiant_transaction=identifiant, statut=StatutPaiement.DECLARE,
                                    serie_recu=serie, numero_recu=numero, encaisse_par=acteur,
                                    affectation_prevue=_prevue(echeances), usage_boutique=usage_boutique,
                                    cree_par=acteur, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=p, centre=centre,
                    apres={"canal": p.canal, "montant_declare": str(montant), "identifiant": identifiant})
        # Une transaction déjà reçue de l'opérateur (notification arrivée avant la déclaration) confirme aussitôt.
        t = TransactionPasserelle.objects.filter(identifiant_operateur=identifiant, paiement__isnull=True,
                                                 statut_operateur="confirme").first()
        if t is not None:
            _confirmer(p, t.montant, t.commission, identifiant)
    return p


def paiement_pour_vente(acteur, vente, montant, *, paiement=None, identifiant_transaction="", telephone=""):
    """Règlement Mobile Money d'une vente : paiement confirmé par l'opérateur (demande faite avant la
    validation de la vente), ou déclaré avec son identifiant (RG-BOU-10)."""
    centre = vente.point_de_vente.centre
    if paiement is not None:
        if paiement.centre_id != centre.pk or not paiement.usage_boutique:
            raise RegleMetier("Ce paiement ne concerne pas la boutique de ce centre.")
        if paiement.statut != StatutPaiement.CONFIRME:
            raise RegleMetier("Le paiement n'est pas encore confirmé par l'opérateur.")
        if paiement.montant_confirme != montant:
            raise RegleMetier("Le montant confirmé par l'opérateur diffère du règlement.")
        if paiement.reglements.exists():
            raise RegleMetier("Ce paiement règle déjà une autre vente.")
        return paiement
    return declarer_mobile_money(acteur, centre, identifiant_transaction=identifiant_transaction,
                                 montant_declare=montant, telephone=telephone, usage_boutique=True)


# --------------------------------------------------------------------------- notifications et confirmation

def recevoir_notification(fournisseur: str, corps: bytes, entetes: dict):
    """Notification signée de la passerelle. Signature invalide : refusée et journalisée, aucun
    changement (CA-PAY-02). Reçue deux fois : ignorée la seconde fois (CA-PAY-01)."""
    gw = passerelle(fournisseur)
    if not gw.verifier_notification(corps, entetes):
        journaliser(ActionJournal.ACCES_REFUSE, objet_type="notification_passerelle",
                    motif=f"Signature invalide ({fournisseur})")
        raise AccesRefuse("Signature invalide.", objet="notification_passerelle", action="C",
                          code="signature_invalide")
    etat = gw.lire_notification(corps)
    if etat.montant is not None:
        _gnf(etat.montant, "Le montant de l'opérateur")
    with transaction.atomic():
        if TransactionPasserelle.objects.filter(fournisseur=gw.code,
                                                identifiant_operateur=etat.identifiant_operateur).exists():
            return None  # déjà reçue : sans effet
        paiement = _trouver_paiement(etat)
        if paiement is None and etat.statut == "confirme":
            paiement = _paiement_initiative_payeuse(gw.code, etat)
        try:
            with transaction.atomic():
                t = TransactionPasserelle.objects.create(
                    id=uuid.uuid4(), paiement=paiement, fournisseur=gw.code,
                    identifiant_operateur=etat.identifiant_operateur, type=TypeTransaction.NOTIFICATION,
                    statut_operateur=etat.statut, montant=etat.montant or 0, commission=etat.commission,
                    recu_le=timezone.now(), donnees_brutes=etat.brut or {})
        except IntegrityError:
            transaction.set_rollback(True)
            return None  # reçue en parallèle : sans effet
        if paiement is None:
            return t
        if etat.statut == "confirme":
            _confirmer(paiement, etat.montant, etat.commission, etat.identifiant_operateur)
        elif etat.statut == "echoue" and paiement.statut in (StatutPaiement.INITIE, StatutPaiement.EN_ATTENTE):
            _changer_statut(paiement, StatutPaiement.ECHOUE, motif=etat.motif)
    return t


def _trouver_paiement(etat) -> Paiement | None:
    if etat.reference:
        try:
            p = Paiement.objects.filter(pk=uuid.UUID(etat.reference)).first()
            if p:
                return p
        except ValueError:
            pass
    if etat.identifiant_operateur:
        return Paiement.objects.filter(identifiant_transaction=etat.identifiant_operateur).exclude(
            statut__in=[StatutPaiement.ECHOUE, StatutPaiement.EXPIRE]).first()
    return None


def _paiement_initiative_payeuse(fournisseur, etat) -> Paiement | None:
    """Parcours B : référence d'échéance valide, affectation automatique ; sinon « Paiements à
    affecter », sans aucune affectation (RG-PAY-06, CA-PAY-07)."""
    from caef.facturation.models import Echeance

    echeance = Echeance.objects.filter(reference_paiement=etat.reference).first() if etat.reference else None
    centre_id = echeance.centre_id if echeance else _centre_par_defaut()
    if centre_id is None:
        return None
    return Paiement.objects.create(
        centre_id=centre_id, canal=CanalPaiement.MOBILE_MONEY_PAYEUSE, fournisseur=fournisseur,
        identifiant_transaction=etat.identifiant_operateur, reference_echeance=etat.reference or "",
        statut=StatutPaiement.EN_ATTENTE,
        affectation_prevue=[{"echeance": str(echeance.pk), "montant": None}] if echeance else [])


def _centre_par_defaut():
    """Un paiement sans référence valide va à la file du centre désigné par configuration (compte
    marchand commun ; voir DECISIONS.md)."""
    from django.conf import settings

    from caef.referentiels.models import Centre

    code = settings.CAEF.get("CENTRE_PAIEMENTS_NON_REFERENCES")
    c = Centre.objects.filter(code=code).first() if code else None
    return c.pk if c else None


def _confirmer(paiement, montant_operateur, commission, identifiant):
    """Montant retenu : celui de l'opérateur (RG-PAY-03) ; moindre, il laisse un restant dû ; supérieur,
    un trop-perçu à affecter ou à rembourser."""
    if paiement.statut in STATUTS_ENCAISSES:
        return paiement
    montant = Decimal(montant_operateur)
    paiement.montant_confirme = montant
    paiement.commission = commission
    paiement.montant_net = montant - (commission or 0)
    paiement.identifiant_transaction = paiement.identifiant_transaction or identifiant
    paiement.confirme_le = timezone.now()
    if not paiement.numero_recu and not paiement.usage_boutique:
        paiement.serie_recu, paiement.numero_recu = f"{paiement.centre.code}-P", prochain_numero(
            f"RECU:{paiement.centre_id}:{paiement.centre.code}-P")
    _changer_statut(paiement, StatutPaiement.CONFIRME)
    if not paiement.usage_boutique:
        _affecter_automatiquement(paiement)
    else:
        from caef.boutique.models import Reglement, StatutReglement

        Reglement.objects.filter(paiement=paiement, statut=StatutReglement.DECLARE).update(
            statut=StatutReglement.CONFIRME)
    return paiement


def _changer_statut(paiement, statut, motif=""):
    avant = paiement.statut
    paiement.statut = statut
    if motif:
        paiement.motif_operateur = motif[:255]
    paiement.marquer_modifie(None)
    paiement.save()
    journaliser(ActionJournal.STATUT, objet=paiement, centre=paiement.centre_id, avant={"statut": avant},
                apres={"statut": statut, "montant_confirme": str(paiement.montant_confirme)}, motif=motif)


def disponible(paiement) -> Decimal:
    """Montant confirmé non encore affecté ni remboursé."""
    if paiement.statut not in STATUTS_ENCAISSES or paiement.montant_confirme is None:
        return Decimal(0)
    affecte = paiement.affectations.aggregate(t=Sum("montant"))["t"] or Decimal(0)
    rembourse_hors_echeance = paiement.remboursements.filter(statut=StatutRemboursement.EXECUTE,
                                                             echeance__isnull=True).aggregate(
        t=Sum("montant"))["t"] or Decimal(0)
    return paiement.montant_confirme - affecte - rembourse_hors_echeance


def _affecter_automatiquement(paiement):
    from caef.facturation.models import Echeance
    from caef.facturation.services import recalculer_echeance

    reste = disponible(paiement)
    for ligne in paiement.affectation_prevue or []:
        if reste <= 0:
            break
        e = Echeance.objects.select_for_update().filter(pk=ligne["echeance"]).first()
        if e is None or e.centre_id != paiement.centre_id:
            continue
        recalculer_echeance(e)
        voulu = Decimal(ligne["montant"]) if ligne.get("montant") else e.restant_du
        part = min(reste, voulu, e.restant_du)
        if part <= 0:
            continue
        AffectationPaiement.objects.create(paiement=paiement, echeance=e, montant=part, automatique=True,
                                           cree_par=paiement.encaisse_par)
        recalculer_echeance(e)
        reste -= part
    if reste > 0:
        notifier_role(paiement.centre_id, ("CPT",), "paiement_a_affecter",
                      f"Paiement de {paiement.montant_confirme} GNF : {reste} GNF à affecter.", paiement)


def paiements_a_affecter(centre_id):
    """File « Paiements à affecter » : confirmés (scolarité) dont une part reste non affectée."""
    ids = [p.pk for p in Paiement.objects.filter(centre_id=centre_id, usage_boutique=False,
                                                 statut__in=STATUTS_ENCAISSES)
           if disponible(p) > 0]
    return Paiement.objects.filter(pk__in=ids)


def affecter(acteur, paiement, echeance, montant, motif):
    """Affectation manuelle par le CPT, motivée (RG-PAY-06)."""
    from caef.facturation.services import recalculer_echeance

    verifier(acteur, "paiement_a_affecter", "M", centre=paiement.centre_id)
    if not motif:
        raise RegleMetier("Le motif de l'affectation est obligatoire.")
    montant = _gnf(montant)
    if echeance.centre_id != paiement.centre_id:
        raise RegleMetier("L'échéance appartient à un autre centre.")
    recalculer_echeance(echeance)
    if montant <= 0 or montant > disponible(paiement) or montant > echeance.restant_du:
        raise RegleMetier("Montant supérieur au disponible du paiement ou au restant dû de l'échéance.")
    with transaction.atomic():
        a = AffectationPaiement.objects.create(paiement=paiement, echeance=echeance, montant=montant,
                                               affecte_par=acteur, motif=motif, cree_par=acteur)
        recalculer_echeance(echeance)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=a, centre=paiement.centre_id,
                    apres=instantane(a), motif=motif)
    return a


# --------------------------------------------------------------------------- consultations et délais

def consulter(paiement, derniere=False):
    """Consultation de statut ; à la dernière (60 minutes) sans réponse, « Expiré »."""
    if paiement.statut not in (StatutPaiement.INITIE, StatutPaiement.EN_ATTENTE):
        return paiement
    etat = passerelle(paiement.fournisseur or None).consulter(paiement)
    with transaction.atomic():
        if etat.statut == "confirme":
            try:
                with transaction.atomic():
                    TransactionPasserelle.objects.create(
                        id=uuid.uuid4(), paiement=paiement, fournisseur=paiement.fournisseur,
                        identifiant_operateur=etat.identifiant_operateur, type=TypeTransaction.CONSULTATION,
                        statut_operateur=etat.statut, montant=etat.montant, commission=etat.commission,
                        recu_le=timezone.now(), donnees_brutes=etat.brut or {})
            except IntegrityError:
                pass
            _confirmer(paiement, etat.montant, etat.commission, etat.identifiant_operateur)
        elif etat.statut == "echoue":
            _changer_statut(paiement, StatutPaiement.ECHOUE, motif=etat.motif)
        elif derniere:
            _changer_statut(paiement, StatutPaiement.EXPIRE)
    return paiement


def marquer_non_retrouves(maintenant_=None):
    """Déclaré depuis 24 heures sans transaction correspondante : « Non retrouvé », signalé au CPT."""
    limite = (maintenant_ or timezone.now()) - timedelta(hours=parametre("PAIEMENT_NON_RETROUVE_HEURES"))
    n = 0
    for p in Paiement.objects.filter(statut=StatutPaiement.DECLARE, cree_le__lt=limite):
        _changer_statut(p, StatutPaiement.NON_RETROUVE)
        notifier_role(p.centre_id, ("CPT",), "paiement_non_retrouve",
                      f"Paiement déclaré {p.identifiant_transaction} non retrouvé chez l'opérateur.", p)
        n += 1
    return n


def confirmer_manuellement(acteur, paiement, *, montant_operateur, motif, piece_justificative):
    """Non retrouvé → Confirmé : rapprochement manuel par le CPT, avec pièce et motif."""
    verifier(acteur, "rapprochement_operateur", "M", centre=paiement.centre_id)
    exiger_statut(paiement, (StatutPaiement.NON_RETROUVE, StatutPaiement.DECLARE), "Confirmer manuellement")
    if not motif or piece_justificative is None:
        raise RegleMetier("Pièce et motif obligatoires.")
    with transaction.atomic():
        _confirmer(paiement, _gnf(montant_operateur), None, paiement.identifiant_transaction)
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=paiement, centre=paiement.centre_id,
                    apres={"statut": "confirme", "piece": str(piece_justificative.pk)}, motif=motif)
    return paiement


# --------------------------------------------------------------------------- relevé et rapprochement

def importer_releve(centre, fournisseur, jour, lignes: list[dict]):
    """RG-PAY-11 : relevé de l'opérateur apparié transaction par transaction. `lignes` :
    [{identifiant, montant, commission}]."""
    resultat = {"apparie": 0, "absent_outil": 0, "ecart_montant": 0, "absent_releve": 0}
    vus = set()
    with transaction.atomic():
        for l in lignes:
            ident = str(l["identifiant"]).strip()
            vus.add(ident)
            if LigneReleveOperateur.objects.filter(fournisseur=fournisseur, identifiant_operateur=ident).exists():
                continue
            montant = _gnf(l["montant"])
            commission = Decimal(l.get("commission") or 0)
            p = Paiement.objects.filter(identifiant_transaction=ident, centre=centre).first()
            if p is None:
                statut = StatutRapprochement.ABSENT_OUTIL
            else:
                if p.statut in (StatutPaiement.DECLARE, StatutPaiement.NON_RETROUVE, StatutPaiement.EN_ATTENTE):
                    _confirmer(p, montant, commission, ident)
                attendu = p.montant_confirme if p.montant_confirme is not None else p.montant_attendu
                statut = StatutRapprochement.APPARIE if attendu == montant else StatutRapprochement.ECART_MONTANT
            t = TransactionPasserelle.objects.filter(fournisseur=fournisseur, identifiant_operateur=ident).first()
            LigneReleveOperateur.objects.create(id=uuid.uuid4(), centre=centre, fournisseur=fournisseur,
                                                date_releve=jour, identifiant_operateur=ident, montant=montant,
                                                commission=commission, transaction_passerelle=t, paiement=p,
                                                statut_rapprochement=statut)
            resultat[statut] += 1
        confirmes = Paiement.objects.filter(centre=centre, statut__in=STATUTS_ENCAISSES, confirme_le__date=jour,
                                            canal__startswith="mobile_money").exclude(identifiant_transaction__in=vus)
        for p in confirmes:
            if LigneReleveOperateur.objects.filter(fournisseur=fournisseur,
                                                   identifiant_operateur=p.identifiant_transaction).exists():
                continue
            LigneReleveOperateur.objects.create(id=uuid.uuid4(), centre=centre, fournisseur=fournisseur,
                                                date_releve=jour, identifiant_operateur=p.identifiant_transaction,
                                                montant=p.montant_confirme or 0, paiement=p,
                                                statut_rapprochement=StatutRapprochement.ABSENT_RELEVE)
            resultat["absent_releve"] += 1
        ecarts = resultat["absent_outil"] + resultat["ecart_montant"] + resultat["absent_releve"]
        if ecarts:
            notifier_role(centre.pk, ("CPT",), "ecart_rapprochement",
                          f"Rapprochement du {jour:%d/%m/%Y} : {ecarts} écart(s) à motiver.", None)
    return resultat


def motiver_ecart(acteur, ligne, motif):
    verifier(acteur, "rapprochement_operateur", "M", centre=ligne.centre_id)
    if ligne.statut_rapprochement == StatutRapprochement.APPARIE:
        raise RegleMetier("Cette ligne est appariée : aucun écart à motiver.")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        ligne.motif = motif
        ligne.motive_par = acteur
        ligne.save(update_fields=["motif", "motive_par"])
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet_type="ligne_releve_operateur",
                    centre=ligne.centre_id, apres={"identifiant": ligne.identifiant_operateur}, motif=motif)
    return ligne


# --------------------------------------------------------------------------- remboursements

def demander_remboursement(acteur, paiement, *, montant, motif, echeance=None):
    """RG-PAY-09 : demandé et motivé par le CPT ; au plus le confirmé non encore remboursé."""
    verifier(acteur, "remboursement", "C", centre=paiement.centre_id)
    if paiement.statut not in (StatutPaiement.CONFIRME, StatutPaiement.REMBOURSE_PARTIELLEMENT):
        raise RegleMetier("Seul un paiement confirmé se rembourse.")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    montant = _gnf(montant)
    deja = paiement.remboursements.exclude(statut=StatutRemboursement.REFUSE).aggregate(
        t=Sum("montant"))["t"] or Decimal(0)
    if montant <= 0 or montant > paiement.montant_confirme - deja:
        raise RegleMetier("Le remboursement dépasse le montant confirmé non encore remboursé.")
    gw = passerelle(paiement.fournisseur or None) if paiement.fournisseur else None
    execution = ExecutionRemboursement.PASSERELLE if gw and gw.accepte_remboursements \
        else ExecutionRemboursement.HORS_OUTIL
    with transaction.atomic():
        r = Remboursement.objects.create(paiement=paiement, echeance=echeance, montant=montant, motif=motif,
                                         demande_par=acteur, execution=execution, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=r, centre=paiement.centre_id,
                    apres=instantane(r), motif=motif)
        notifier_role(paiement.centre_id, ("RC",), "remboursement_a_valider", "Remboursement demandé : à valider.", r)
    return r


def valider_remboursement(acteur, r, valider=True, motif=""):
    decision = verifier(acteur, "remboursement", "V", centre=r.paiement.centre_id)
    exiger_statut(r, (StatutRemboursement.DEMANDE,), "Valider")
    if r.demande_par_id == acteur.pk:
        raise SeparationDesTaches("La personne qui a demandé le remboursement ne le valide pas (RG-PAY-09).",
                                  objet="remboursement", action="V", centre_id=r.paiement.centre_id,
                                  objet_type="remboursement", objet_id=r.pk)
    if not valider and not motif:
        raise RegleMetier("Le motif du refus est obligatoire.")
    with transaction.atomic():
        r.statut = StatutRemboursement.VALIDE if valider else StatutRemboursement.REFUSE
        r.valide_par = acteur
        r.valide_le = timezone.now()
        enregistrer(r, acteur, ["statut", "valide_par", "valide_le"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=r, centre=r.paiement.centre_id,
                    avant={"statut": "demande"}, apres={"statut": r.statut}, motif=motif, interim=decision.interim)
    return r


def executer_remboursement(acteur, r, piece_justificative=None):
    """Par la passerelle si elle le permet, sinon hors outil avec pièce ; l'échéance redevient due."""
    from caef.facturation.services import recalculer_echeance

    verifier(acteur, "remboursement", "C", centre=r.paiement.centre_id)
    exiger_statut(r, (StatutRemboursement.VALIDE,), "Exécuter")
    if r.execution == ExecutionRemboursement.HORS_OUTIL and piece_justificative is None:
        raise RegleMetier("Un remboursement hors outil exige une pièce justificative.")
    p = r.paiement
    if r.execution == ExecutionRemboursement.PASSERELLE:
        etat = passerelle(p.fournisseur).rembourser(p, r.montant)
        if etat is None or etat.statut != "confirme":
            raise RegleMetier("La passerelle n'a pas confirmé le remboursement.")
    with transaction.atomic():
        r.statut = StatutRemboursement.EXECUTE
        r.execute_le = timezone.now()
        r.piece_justificative = piece_justificative
        enregistrer(r, acteur, ["statut", "execute_le", "piece_justificative"])
        total = p.remboursements.filter(statut=StatutRemboursement.EXECUTE).aggregate(t=Sum("montant"))["t"] or 0
        _changer_statut(p, StatutPaiement.REMBOURSE if total >= p.montant_confirme
                        else StatutPaiement.REMBOURSE_PARTIELLEMENT)
        if r.echeance_id:
            recalculer_echeance(r.echeance)
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=r, centre=p.centre_id,
                    avant={"statut": "valide"}, apres={"statut": "execute"})
    return r


# --------------------------------------------------------------------------- totaux pour la clôture

def totaux_mois(centre_id, debut, fin) -> dict:
    """Brut, commission et net des encaissements confirmés du mois (RG-PAY-12) ; scolarité seulement."""
    qs = Paiement.objects.filter(centre_id=centre_id, usage_boutique=False, statut__in=STATUTS_ENCAISSES,
                                 confirme_le__date__gte=debut, confirme_le__date__lte=fin)
    agg = qs.aggregate(brut=Sum("montant_confirme"), commission=Sum("commission"), net=Sum("montant_net"))
    rembourse = Remboursement.objects.filter(paiement__centre_id=centre_id, paiement__usage_boutique=False,
                                             statut=StatutRemboursement.EXECUTE, execute_le__date__gte=debut,
                                             execute_le__date__lte=fin).aggregate(t=Sum("montant"))["t"]
    return {"brut": agg["brut"] or Decimal(0), "commission": agg["commission"] or Decimal(0),
            "net": agg["net"] or Decimal(0), "rembourse": rembourse or Decimal(0)}
