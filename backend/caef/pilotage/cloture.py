"""Clôture mensuelle et rapprochement du centre (SFD § 9.8, SRC-01 à SRC-04, RG-SRC-01 à 03).

Les totaux sont calculés depuis les enregistrements, jamais saisis. Le CPT saisit le montant des
pièces et vérifie ; le RC (ou le RA pendant un intérim déclaré) valide ; le mois est alors verrouillé.
"""

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from caef.commun.exceptions import RegleMetier, SeparationDesTaches
from caef.commun.services import enregistrer, exiger_statut
from caef.habilitations.services import module_actif, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import journaliser
from caef.notifications.services import notifier_role

from .models import ClotureMensuelle, Flux, LigneRapprochement, StatutCloture


def bornes(mois: str) -> tuple[date, date]:
    annee, m = map(int, mois.split("-"))
    return date(annee, m, 1), date(annee, m, calendar.monthrange(annee, m)[1])


def mois_precedent(jour: date) -> str:
    d = jour.replace(day=1) - timedelta(days=1)
    return f"{d.year:04d}-{d.month:02d}"


def calculer_totaux(centre_id, mois) -> dict:
    """{flux: {devise: montant}} ; None pour un flux dont le module est désactivé (RG-ADM-20)."""
    from caef.boutique.models import Reglement, Reversement, StatutReversement, Vente
    from caef.conventions.models import Contribution
    from caef.paiements.services import totaux_mois

    debut, fin = bornes(mois)
    totaux = {}
    boutique = module_actif(centre_id, "boutique", fin)
    if boutique:
        ventes = Vente.objects.filter(point_de_vente__centre_id=centre_id, date_heure_vente__date__gte=debut,
                                      date_heure_vente__date__lte=fin).aggregate(t=Sum("total"))["t"]
        totaux[Flux.VENTES] = {"GNF": ventes or Decimal(0)}
        par_mode = dict(Reglement.objects.filter(vente__session_caisse__point_de_vente__centre_id=centre_id,
                                                 vente__session_caisse__date__gte=debut,
                                                 vente__session_caisse__date__lte=fin)
                        .values_list("mode").annotate(t=Sum("montant")))
        totaux[Flux.CAISSES] = {"GNF": sum(par_mode.values(), Decimal(0)), "par_mode": par_mode}
        rev = Reversement.objects.filter(point_de_vente__centre_id=centre_id, statut=StatutReversement.PAYE,
                                         date_paiement__gte=debut, date_paiement__lte=fin).aggregate(
            t=Sum("montant_reverse"))["t"]
        totaux[Flux.REVERSEMENTS] = {"GNF": rev or Decimal(0)}
    else:
        totaux[Flux.VENTES] = totaux[Flux.CAISSES] = totaux[Flux.REVERSEMENTS] = None
    if module_actif(centre_id, "scolarite_paiements", fin):
        t = totaux_mois(centre_id, debut, fin)
        totaux[Flux.PAIEMENTS_SCOLARITE] = {"GNF": t["brut"] - t["rembourse"], "detail": t}
    else:
        totaux[Flux.PAIEMENTS_SCOLARITE] = None
    contributions = (Contribution.objects.filter(centre_beneficiaire_id=centre_id, financiere=True,
                                                 statut__in=["recue", "validee"], date_reception__gte=debut,
                                                 date_reception__lte=fin)
                     .values_list("devise").annotate(t=Sum("montant_recu")))
    totaux[Flux.CONTRIBUTIONS] = {d: t for d, t in contributions} or {"GNF": Decimal(0)}
    return totaux


def _serialiser(totaux):
    def conv(v):
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        return None if v is None else str(v)
    return {k: conv(v) for k, v in totaux.items()}


def generer(centre, mois: str) -> ClotureMensuelle:
    """Le 1er de chaque mois, état du mois écoulé (RG-SRC-02) ; régénéré tant qu'il est « À faire »."""
    totaux = calculer_totaux(centre.pk, mois)
    with transaction.atomic():
        cloture, _ = ClotureMensuelle.objects.get_or_create(centre=centre, mois=mois)
        if cloture.statut != StatutCloture.A_FAIRE:
            return cloture
        cloture.totaux = _serialiser(totaux)
        cloture.save(update_fields=["totaux"])
        for flux, par_devise in totaux.items():
            if par_devise is None:
                LigneRapprochement.objects.update_or_create(
                    cloture_mensuelle=cloture, flux=flux, devise="GNF",
                    defaults={"module_non_active": True, "montant_outil": None, "ecart": None})
                continue
            for devise, montant in par_devise.items():
                if devise in ("par_mode", "detail"):
                    continue
                ligne, cree = LigneRapprochement.objects.get_or_create(
                    cloture_mensuelle=cloture, flux=flux, devise=devise, defaults={"montant_outil": montant})
                if not cree:
                    ligne.montant_outil = montant
                    ligne.module_non_active = False
                    ligne.ecart = (ligne.montant_piece - montant) if ligne.montant_piece is not None else None
                    ligne.save(update_fields=["montant_outil", "module_non_active", "ecart"])
        cloture.ecart = _ecart_total(cloture)
        cloture.save(update_fields=["ecart"])
    return cloture


def _ecart_total(cloture) -> dict:
    ecarts = {}
    for l in cloture.lignes.filter(module_non_active=False, ecart__isnull=False):
        ecarts[l.devise] = str(Decimal(ecarts.get(l.devise, 0)) + l.ecart)
    return ecarts


def saisir_pieces(acteur, cloture, montants: dict):
    """`montants` : {ligne_id: {"montant_piece": m, "motif": "...", "piece_justificative": doc}}."""
    verifier(acteur, "cloture_mensuelle", "C", centre=cloture.centre_id)
    exiger_statut(cloture, (StatutCloture.A_FAIRE,), "Saisir les pièces")
    generer(cloture.centre, cloture.mois)
    lignes = {str(l.pk): l for l in cloture.lignes.all()}
    with transaction.atomic():
        for lid, v in montants.items():
            l = lignes.get(str(lid))
            if l is None or l.module_non_active:
                raise RegleMetier("Ligne de rapprochement inconnue ou module non activé.")
            montant = Decimal(v["montant_piece"])
            if l.devise == "GNF" and montant != montant.to_integral_value():
                raise RegleMetier("Montants entiers en GNF.")
            l.montant_piece = montant
            l.ecart = montant - (l.montant_outil or 0)
            l.motif = v.get("motif", l.motif)
            if v.get("piece_justificative") is not None:
                l.piece_justificative = v["piece_justificative"]
            l.save()
        cloture.ecart = _ecart_total(cloture)
        enregistrer(cloture, acteur, ["ecart"])
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=cloture, centre=cloture.centre_id,
                    apres={"lignes": len(montants), "ecart": cloture.ecart})
    return cloture


def blocages_verification(cloture) -> list[str]:
    """Conditions de « Vérifiée » (SFD 9.8, CA-SRC-02)."""
    from caef.boutique.models import SessionCaisse, StatutCaisse
    from caef.paiements.models import LigneReleveOperateur
    from caef.synchronisation.models import Appareil, StatutAppareil

    debut, fin = bornes(cloture.mois)
    blocages = []
    for l in cloture.lignes.filter(module_non_active=False):
        if l.montant_piece is None:
            blocages.append(f"Montant des pièces manquant : {l.get_flux_display()} ({l.devise}).")
        elif l.ecart and not l.motif:
            blocages.append(f"Écart non motivé : {l.get_flux_display()} ({l.devise}).")
    if SessionCaisse.objects.filter(point_de_vente__centre_id=cloture.centre_id, date__gte=debut, date__lte=fin).exclude(
            statut__in=[StatutCaisse.VALIDEE, StatutCaisse.VALIDEE_AVEC_ECART]).exists():
        blocages.append("Des sessions de caisse du mois ne sont pas validées.")
    fin_mois = timezone.make_aware(datetime.combine(fin + timedelta(days=1), time.min))
    derogation = set(map(str, cloture.derogation_appareils or []))
    for a in Appareil.objects.filter(centre_id=cloture.centre_id, statut=StatutAppareil.ACTIF):
        if str(a.pk) in derogation:
            continue
        if a.derniere_synchronisation is None or a.derniere_synchronisation < fin_mois or \
                (a.plus_ancienne_operation_en_attente and a.plus_ancienne_operation_en_attente < fin_mois):
            blocages.append(f"Appareil non synchronisé après la fin du mois : {a.libelle}.")
    if LigneReleveOperateur.objects.filter(centre_id=cloture.centre_id, date_releve__gte=debut, date_releve__lte=fin,
                                           motif="").exclude(statut_rapprochement="apparie").exists():
        blocages.append("Des écarts de rapprochement Mobile Money du mois ne sont pas motivés.")
    return blocages


def deroger_appareils(acteur, cloture, appareils, motif):
    """Décision motivée du RC pour un appareil non synchronisé (OFF-08)."""
    verifier(acteur, "cloture_mensuelle", "V", centre=cloture.centre_id)
    exiger_statut(cloture, (StatutCloture.A_FAIRE,), "Déroger")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        cloture.derogation_appareils = sorted(set(cloture.derogation_appareils or []) | {str(a.pk) for a in appareils})
        enregistrer(cloture, acteur, ["derogation_appareils"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=cloture, centre=cloture.centre_id,
                    apres={"derogation_appareils": cloture.derogation_appareils}, motif=motif)
    return cloture


def verifier_cloture(acteur, cloture):
    verifier(acteur, "cloture_mensuelle", "C", centre=cloture.centre_id)
    exiger_statut(cloture, (StatutCloture.A_FAIRE,), "Vérifier")
    blocages = blocages_verification(cloture)
    if blocages:
        raise RegleMetier("Vérification impossible.", code="verification_bloquee", details={"blocages": blocages})
    with transaction.atomic():
        cloture.statut = StatutCloture.VERIFIEE
        cloture.verifiee_par = acteur
        cloture.verifiee_le = timezone.now()
        enregistrer(cloture, acteur, ["statut", "verifiee_par", "verifiee_le"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=cloture, centre=cloture.centre_id,
                    avant={"statut": "a_faire"}, apres={"statut": "verifiee"})
        notifier_role(cloture.centre_id, ("RC",), "cloture_a_valider", f"Clôture {cloture.mois} vérifiée : à valider.",
                      cloture)
    return cloture


def valider_cloture(acteur, cloture):
    """Par le RC, ou le RA en intérim ; jamais par le vérificateur ; verrouille le mois."""
    decision = verifier(acteur, "cloture_mensuelle", "V", centre=cloture.centre_id)
    exiger_statut(cloture, (StatutCloture.VERIFIEE,), "Valider")
    if cloture.verifiee_par_id == acteur.pk:
        raise SeparationDesTaches("Le vérificateur ne valide jamais sa propre clôture (RG-SRC-02).",
                                  objet="cloture_mensuelle", action="V", centre_id=cloture.centre_id,
                                  objet_type="cloture_mensuelle", objet_id=cloture.pk)
    avec_ecart = any(Decimal(v) != 0 for v in (cloture.ecart or {}).values())
    statut = StatutCloture.VALIDEE_AVEC_ECART if avec_ecart else StatutCloture.VALIDEE
    with transaction.atomic():
        cloture.statut = statut
        cloture.validee_par = acteur
        cloture.validee_le = timezone.now()
        cloture.verrouillee = True
        enregistrer(cloture, acteur, ["statut", "validee_par", "validee_le", "verrouillee"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=cloture, centre=cloture.centre_id,
                    avant={"statut": "verifiee"}, apres={"statut": statut, "verrouillee": True},
                    interim=decision.interim)
    return cloture


def renvoyer_cloture(acteur, cloture, motif):
    verifier(acteur, "cloture_mensuelle", "V", centre=cloture.centre_id)
    exiger_statut(cloture, (StatutCloture.VERIFIEE,), "Renvoyer")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        cloture.statut = StatutCloture.A_FAIRE
        cloture.motif_renvoi = motif
        cloture.verifiee_par = None
        cloture.verifiee_le = None
        enregistrer(cloture, acteur, ["statut", "motif_renvoi", "verifiee_par", "verifiee_le"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=cloture, centre=cloture.centre_id,
                    avant={"statut": "verifiee"}, apres={"statut": "a_faire"}, motif=motif)
    return cloture


def generer_clotures_du_mois(jour=None):
    from caef.referentiels.models import Centre

    jour = jour or timezone.localdate()
    mois = mois_precedent(jour)
    return [generer(c, mois) for c in Centre.objects.filter(statut="actif")]
