"""Dossiers, recherche anti-doublon, candidatures, transferts et fusions (SFD § 4, RG-BEN-01 à 09)."""

from dataclasses import dataclass, field
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from caef.commun.codes import code_annuel
from caef.commun.contexte import contexte
from caef.commun.exceptions import AccesRefuse, RegleMetier
from caef.commun.services import enregistrer, exiger_statut, jour_reel, origine, parametre, verifier_version
from caef.habilitations.services import decider, portee, roles_de, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import difference, instantane, journaliser
from caef.notifications.services import notifier_role

from .models import (
    Beneficiaire,
    Candidature,
    DecisionDoublon,
    Fusion,
    PaireDoublon,
    PrecisionNaissance,
    StatutBeneficiaire,
    StatutCandidature,
    StatutPaire,
    StatutTransfert,
    Transfert,
)
from .phonetique import cle_phonetique, nom_normalise

CHAMPS_MODIFIABLES = {"nom", "prenoms", "autres_noms", "date_naissance", "annee_naissance", "tranche_age",
                      "precision_naissance", "sexe", "telephone", "zone_residence", "niveau_etudes",
                      "situation_entree", "autorisation_image", "consentement_date", "consentement_mode"}


# --------------------------------------------------------------------------- doublons

@dataclass
class Correspondance:
    beneficiaire: Beneficiaire
    score: int
    champs: list = field(default_factory=list)


def _naissance_identique(a, b) -> bool:
    """Date identique ; à défaut de date complète des deux côtés, même année au même niveau de précision."""
    if a.get("date_naissance") and b.get("date_naissance"):
        return a["date_naissance"] == b["date_naissance"]
    if a.get("precision") == b.get("precision") == PrecisionNaissance.ANNEE:
        return bool(a.get("annee")) and a.get("annee") == b.get("annee")
    return False


def score_doublon(a: dict, b: dict) -> tuple[int, list]:
    """RG-BEN-02 : noms 50, naissance 30, localité 10, téléphone 10. Le téléphone ne suffit jamais seul."""
    score, champs = 0, []
    if a["cle"] and (a["cle"] == b["cle"] or a["nom_normalise"] == b["nom_normalise"]):
        score += 50
        champs.append("nom_prenoms")
    if _naissance_identique(a, b):
        score += 30
        champs.append("naissance")
    if a.get("zone") and a.get("zone") == b.get("zone"):
        score += 10
        champs.append("localite")
    if a.get("telephone") and a.get("telephone") == b.get("telephone"):
        score += 10
        champs.append("telephone")
    if champs == ["telephone"]:
        return 0, []
    return score, champs


def _signature(nom, prenoms, date_naissance=None, annee_naissance=None, zone=None, telephone="", autres_noms="",
               precision=None):
    if precision is None:
        precision = PrecisionNaissance.EXACTE if date_naissance else PrecisionNaissance.ANNEE
    return {
        "cle": cle_phonetique(nom, prenoms),
        "cle_autres": cle_phonetique(autres_noms, prenoms) if autres_noms else "",
        "nom_normalise": nom_normalise(nom, prenoms),
        "date_naissance": date_naissance,
        "annee": date_naissance.year if date_naissance else annee_naissance,
        "precision": precision,
        "zone": str(getattr(zone, "pk", zone)) if zone else None,
        "telephone": (telephone or "").replace(" ", ""),
    }


def _signature_dossier(b: Beneficiaire):
    return _signature(b.nom, b.prenoms, b.date_naissance, b.annee_naissance, b.zone_residence_id, b.telephone,
                      b.autres_noms, b.precision_naissance)


def chercher_doublons(signature: dict, exclure=None, limite=20) -> list[Correspondance]:
    """Recherche dans tout le réseau (RG-BEN-01) ; candidats triés par score décroissant."""
    cles = [signature["cle"]] + ([signature["cle_autres"]] if signature.get("cle_autres") else [])
    q = Q(cle_phonetique__in=cles) | Q(nom_normalise=signature["nom_normalise"])
    mots = sorted(signature["cle"].split(), key=len, reverse=True)
    if mots:
        q |= Q(cle_phonetique__contains=mots[0])
    if signature.get("date_naissance"):
        q |= Q(date_naissance=signature["date_naissance"])
    qs = Beneficiaire.objects.filter(q).exclude(statut=StatutBeneficiaire.FUSIONNE).select_related(
        "centre_rattachement")
    if exclure is not None:
        qs = qs.exclude(pk=getattr(exclure, "pk", exclure))
    resultats = []
    seuil = parametre("SEUIL_DOUBLON_INFORMATIF")
    for b in qs[:500]:
        sb = _signature_dossier(b)
        score, champs = score_doublon(signature, sb)
        if sb["cle"] != signature["cle"] and signature.get("cle_autres") and sb["cle"] == signature["cle_autres"]:
            score, champs = max((score, champs), (score + 50, champs + ["autres_noms"]))
        if score >= seuil:
            resultats.append(Correspondance(b, score, champs))
    resultats.sort(key=lambda c: -c.score)
    return resultats[:limite]


def recherche_reseau(acteur, *, nom, prenoms, date_naissance=None, annee_naissance=None, zone=None,
                     telephone="") -> list[dict]:
    """Étape 1 obligatoire de E-BEN-02. Pour un dossier d'un autre centre, seulement le code, le nom,
    l'année de naissance et le centre (BEN-05, USR-04)."""
    verifier(acteur, "recherche_reseau", "L")
    sig = _signature(nom, prenoms, date_naissance, annee_naissance, zone, telephone)
    p = portee(acteur, "beneficiaire", "L", nominatif=True)
    sortie = []
    for c in chercher_doublons(sig):
        b = c.beneficiaire
        ligne = {"id": str(b.pk), "code": b.code, "nom": b.nom, "prenoms": b.prenoms, "annee_naissance": b.annee,
                 "centre": b.centre_rattachement.nom, "score": c.score, "champs_concordants": c.champs,
                 "niveau": _niveau_alerte(c.score)}
        if not (p.national or b.centre_rattachement_id in p.centres):
            ligne = {k: ligne[k] for k in ("code", "nom", "prenoms", "annee_naissance", "centre", "score", "niveau")}
        sortie.append(ligne)
    journaliser(ActionJournal.CONSULTATION_SENSIBLE, utilisateur=acteur, objet_type="recherche_reseau",
                nb_lignes=len(sortie))
    return sortie


def _niveau_alerte(score):
    if score >= parametre("SEUIL_DOUBLON_BLOQUANT"):
        return "bloquant"
    if score >= parametre("SEUIL_DOUBLON_INFORMATIF"):
        return "informatif"
    return "aucun"


# --------------------------------------------------------------------------- dossier

def calculer_completude(b: Beneficiaire, requis=None) -> int:
    requis = requis or parametre("CHAMPS_REQUIS_DOSSIER")
    remplis = 0
    for champ in requis:
        if champ == "naissance":
            ok = bool(b.date_naissance or b.annee_naissance or b.tranche_age)
        else:
            valeur = getattr(b, b._meta.get_field(champ).attname, None)
            ok = valeur not in (None, "")
        remplis += ok
    return round(100 * remplis / len(requis)) if requis else 100


def _remplir_cles(b: Beneficiaire):
    b.nom_normalise = nom_normalise(b.nom, b.prenoms)
    b.cle_phonetique = cle_phonetique(b.nom, b.prenoms)
    b.telephone = (b.telephone or "").replace(" ", "")
    if b.date_naissance:
        b.precision_naissance = PrecisionNaissance.EXACTE
    elif b.annee_naissance:
        b.precision_naissance = PrecisionNaissance.ANNEE
    elif b.tranche_age:
        b.precision_naissance = PrecisionNaissance.TRANCHE
    b.completude = calculer_completude(b)


def _verifier_restreints(acteur, centre, champs: dict, action):
    restreints = {k for k in champs if k in Beneficiaire.CHAMPS_RESTREINTS and champs[k] not in (None, "")}
    if restreints:
        verifier(acteur, "beneficiaire_restreint", action, centre=centre, nominatif=True)


def creer_candidature(acteur, *, centre, formation, date_reception=None, beneficiaire=None, identite=None,
                      decision_doublon=None, commentaire_doublon="", dossier_existant=None):
    """E-BEN-02 : crée la candidature, et le dossier s'il n'existe pas.

    Si un dossier proche existe (score ≥ 60), l'agent ouvre le dossier existant ou déclare
    « personne différente » avec un commentaire (RG-BEN-03). Hors ligne, l'alerte ne bloque pas :
    la candidature est marquée « à vérifier, doublon probable » (RG-OFF-05).
    """
    verifier(acteur, "candidature", "C", centre=centre, nominatif=True)
    centre_id = getattr(centre, "pk", centre)
    hors_ligne = contexte().hors_ligne
    score_max = 0
    doublon_probable = False
    with transaction.atomic():
        if beneficiaire is None and dossier_existant is not None:
            beneficiaire = dossier_existant
            decision_doublon = DecisionDoublon.DOSSIER_EXISTANT_UTILISE
        if beneficiaire is None:
            if not identite:
                raise RegleMetier("Identité de la bénéficiaire manquante.")
            verifier(acteur, "beneficiaire", "C", centre=centre, nominatif=True)
            _verifier_restreints(acteur, centre, identite, "C")
            inconnus = set(identite) - CHAMPS_MODIFIABLES - set(Beneficiaire.CHAMPS_RESTREINTS)
            if inconnus:
                raise RegleMetier("Champ inconnu : " + ", ".join(sorted(inconnus)))
            sig = _signature(identite["nom"], identite["prenoms"], identite.get("date_naissance"),
                             identite.get("annee_naissance"), identite.get("zone_residence"),
                             identite.get("telephone", ""), identite.get("autres_noms", ""))
            proches = chercher_doublons(sig)
            score_max = proches[0].score if proches else 0
            if score_max >= parametre("SEUIL_DOUBLON_BLOQUANT"):
                if hors_ligne:
                    doublon_probable = True
                elif decision_doublon != DecisionDoublon.PERSONNE_DIFFERENTE or not commentaire_doublon:
                    raise RegleMetier(
                        "Un dossier très proche existe déjà : ouvrez-le, ou déclarez « personne différente » "
                        "avec un commentaire.", code="doublon_bloquant",
                        details={"score": score_max, "dossiers": [
                            {"code": c.beneficiaire.code, "score": c.score} for c in proches[:5]]})
            decision_doublon = decision_doublon or DecisionDoublon.AUCUN
            jour = jour_reel()
            centre_obj = centre if hasattr(centre, "code") else _centre(centre_id)
            beneficiaire = Beneficiaire(
                code=code_annuel("BEN", centre_obj.code, jour.year), centre_rattachement_id=centre_id,
                cree_par=acteur, **{k: v for k, v in identite.items()}, **origine())
            if not beneficiaire.precision_naissance:
                beneficiaire.precision_naissance = PrecisionNaissance.EXACTE
            _remplir_cles(beneficiaire)
            beneficiaire.full_clean(exclude=["code", "nom_normalise", "cle_phonetique", "centre_rattachement",
                                             "cle_idempotence"], validate_unique=False, validate_constraints=False)
            beneficiaire.save()
            journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=beneficiaire, centre=centre_id,
                        apres=instantane(beneficiaire), motif=commentaire_doublon)
        else:
            if beneficiaire.statut == StatutBeneficiaire.FUSIONNE:
                raise RegleMetier("Ce dossier a été fusionné : utilisez le dossier conservé.",
                                  details={"dossier_conserve": str(beneficiaire.fusionne_dans_id)})
        jour = jour_reel()
        centre_obj = centre if hasattr(centre, "code") else _centre(centre_id)
        cand = Candidature.objects.create(
            code=code_annuel("CAN", centre_obj.code, jour.year), beneficiaire=beneficiaire, centre_id=centre_id,
            formation=formation, date_reception=date_reception or jour,
            doublon_decision=decision_doublon or DecisionDoublon.AUCUN, doublon_score=score_max,
            doublon_probable=doublon_probable, commentaire=commentaire_doublon, cree_par=acteur, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=cand, centre=centre_id, apres=instantane(cand))
        if beneficiaire.statut == StatutBeneficiaire.INACTIF:
            beneficiaire.statut = StatutBeneficiaire.ACTIF
            enregistrer(beneficiaire, acteur, ["statut"])
        if doublon_probable:
            notifier_role(centre_id, ("RC", "AA"), "doublon_probable",
                          f"Candidature {cand.code} créée hors ligne : doublon probable à vérifier.", cand)
    return cand


def _centre(centre_id):
    from caef.referentiels.models import Centre

    return Centre.objects.get(pk=centre_id)


def modifier_beneficiaire(acteur, beneficiaire, version=None, motif="", **champs):
    """Modification d'un dossier ; les champs restreints exigent le droit dédié."""
    verifier(acteur, "beneficiaire", "M", centre=beneficiaire.centre_rattachement_id, nominatif=True)
    verifier_version(beneficiaire, version)
    if beneficiaire.statut in (StatutBeneficiaire.FUSIONNE, StatutBeneficiaire.ARCHIVE):
        raise RegleMetier("Ce dossier n'est plus modifiable.")
    _verifier_restreints(acteur, beneficiaire.centre_rattachement_id, champs, "M")
    inconnus = set(champs) - CHAMPS_MODIFIABLES - set(Beneficiaire.CHAMPS_RESTREINTS)
    if inconnus:
        raise RegleMetier("Champ non modifiable : " + ", ".join(sorted(inconnus)))
    avant = instantane(beneficiaire)
    for k, v in champs.items():
        setattr(beneficiaire, k, v)
    _remplir_cles(beneficiaire)
    with transaction.atomic():
        enregistrer(beneficiaire, acteur)
        av, ap = difference(avant, instantane(beneficiaire))
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=beneficiaire,
                    centre=beneficiaire.centre_rattachement_id, avant=av, apres=ap, motif=motif)
    return beneficiaire


def lire_donnees_restreintes(acteur, beneficiaire) -> dict:
    """Consultation des données restreintes : droit dédié et trace systématique (SEC-04)."""
    verifier(acteur, "beneficiaire_restreint", "L", centre=beneficiaire.centre_rattachement_id, nominatif=True)
    journaliser(ActionJournal.CONSULTATION_SENSIBLE, utilisateur=acteur, objet=beneficiaire,
                centre=beneficiaire.centre_rattachement_id)
    return {
        "contact_urgence_nom": beneficiaire.contact_urgence_nom,
        "contact_urgence_tel": beneficiaire.contact_urgence_tel,
        "piece_identite_type": beneficiaire.piece_identite_type_id,
        "piece_identite_numero": beneficiaire.piece_identite_numero,
    }


def cloturer_dossier(acteur, beneficiaire, motif):
    verifier(acteur, "beneficiaire", "A", centre=beneficiaire.centre_rattachement_id, nominatif=True)
    if not motif:
        raise RegleMetier("Le motif de clôture est obligatoire (BEN-13).")
    return _statut_dossier(acteur, beneficiaire, StatutBeneficiaire.CLOTURE, motif)


def _statut_dossier(acteur, beneficiaire, statut, motif=""):
    avant = beneficiaire.statut
    with transaction.atomic():
        beneficiaire.statut = statut
        enregistrer(beneficiaire, acteur, ["statut"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=beneficiaire,
                    centre=beneficiaire.centre_rattachement_id, avant={"statut": avant}, apres={"statut": statut},
                    motif=motif)
    return beneficiaire


def recalculer_statuts_dossiers(jour=None):
    """« Inactif » : aucune activité depuis 12 mois (calculé, paramétrable ; SFD 4.4)."""
    jour = jour or timezone.localdate()
    limite = jour - timedelta(days=parametre("JOURS_INACTIVITE_DOSSIER"))
    actifs = Beneficiaire.objects.filter(statut=StatutBeneficiaire.ACTIF, cree_le__date__lt=limite)
    n = 0
    for b in actifs.iterator():
        recent = b.candidatures.filter(Q(date_reception__gte=limite) | ~Q(statut__in=[
            StatutCandidature.REJETEE, StatutCandidature.ANNULEE, StatutCandidature.INSCRITE])).exists() or \
            b.inscriptions.filter(Q(date_inscription__gte=limite) | Q(date_statut_final__isnull=True)).exists()
        if not recent:
            _statut_dossier(None, b, StatutBeneficiaire.INACTIF, "Aucune activité depuis 12 mois")
            n += 1
    return n


# --------------------------------------------------------------------------- candidature

def _transition(acteur, cand, statut, *, motif=None, commentaire="", valide=False, interim=False):
    avant = cand.statut
    with transaction.atomic():
        cand.statut = statut
        champs = ["statut"]
        if motif is not None:
            cand.motif = motif
            champs.append("motif")
        if commentaire:
            cand.commentaire = commentaire
            champs.append("commentaire")
        if statut == StatutCandidature.SOUMISE:
            cand.date_soumission = timezone.now()
            champs.append("date_soumission")
        if valide:
            cand.valide_par = acteur
            cand.valide_le = timezone.now()
            champs += ["valide_par", "valide_le"]
        enregistrer(cand, acteur, champs)
        journaliser(ActionJournal.VALIDATION if valide else ActionJournal.STATUT, utilisateur=acteur, objet=cand,
                    centre=cand.centre_id, avant={"statut": avant}, apres={"statut": statut},
                    motif=commentaire or (motif.libelle if motif is not None else ""), interim=interim)
    return cand


def soumettre_candidature(acteur, cand):
    verifier(acteur, "candidature", "M", centre=cand.centre_id, nominatif=True)
    exiger_statut(cand, (StatutCandidature.BROUILLON, StatutCandidature.INCOMPLETE), "Soumettre")
    b = cand.beneficiaire
    _remplir_cles(b)
    if b.completude < 100 and cand.statut == StatutCandidature.BROUILLON:
        manquants = _champs_manquants(b)
        if manquants:
            raise RegleMetier("Champs obligatoires manquants.", details={"manquants": manquants})
    return _transition(acteur, cand, StatutCandidature.SOUMISE)


def _champs_manquants(b):
    requis = parametre("CHAMPS_REQUIS_DOSSIER")
    manquants = []
    for champ in requis:
        if champ == "naissance":
            if not (b.date_naissance or b.annee_naissance or b.tranche_age):
                manquants.append(champ)
        elif getattr(b, b._meta.get_field(champ).attname, None) in (None, ""):
            manquants.append(champ)
    return manquants


def demander_complement(acteur, cand, motif, commentaire=""):
    """Soumise → Incomplète, par l'agent ou le responsable de centre, motif sélectionné."""
    d_agent = decider(acteur, "candidature", "M", centre=cand.centre_id, nominatif=True)
    if not d_agent.autorise:
        verifier(acteur, "candidature", "V", centre=cand.centre_id, nominatif=True)
    exiger_statut(cand, (StatutCandidature.SOUMISE,), "Demander un complément")
    if motif is None:
        raise RegleMetier("Le motif est obligatoire.")
    return _transition(acteur, cand, StatutCandidature.INCOMPLETE, motif=motif, commentaire=commentaire)


def valider_candidature(acteur, cand):
    """Soumise → Validée, par le responsable de centre (ou l'adjoint en intérim) ; dossier complet."""
    decision = verifier(acteur, "candidature", "V", centre=cand.centre_id, nominatif=True)
    exiger_statut(cand, (StatutCandidature.SOUMISE,), "Valider")
    if cand.cree_par_id == acteur.pk:
        from caef.commun.exceptions import SeparationDesTaches

        raise SeparationDesTaches("La personne qui a saisi la candidature ne peut pas la valider.",
                                  objet="candidature", action="V", centre_id=cand.centre_id,
                                  objet_type="candidature", objet_id=cand.pk)
    b = cand.beneficiaire
    _remplir_cles(b)
    if b.completude < 100:
        raise RegleMetier("Le dossier doit être complet à 100 % pour valider.",
                          details={"completude": b.completude, "manquants": _champs_manquants(b)})
    if cand.doublon_probable:
        raise RegleMetier("Doublon probable à vérifier avant validation (RG-OFF-05).", code="doublon_a_verifier")
    return _transition(acteur, cand, StatutCandidature.VALIDEE, valide=True, interim=decision.interim)


def lever_doute_doublon(acteur, cand, *, dossier_existant=None, commentaire=""):
    """Après une saisie hors ligne : rattacher la candidature au dossier existant, ou confirmer
    « personne différente »."""
    verifier(acteur, "candidature", "M", centre=cand.centre_id, nominatif=True)
    if not cand.doublon_probable:
        raise RegleMetier("Aucun doute de doublon sur cette candidature.")
    if not commentaire:
        raise RegleMetier("Le commentaire est obligatoire.")
    with transaction.atomic():
        avant = instantane(cand, ["beneficiaire", "doublon_decision", "doublon_probable"])
        if dossier_existant is not None:
            cand.beneficiaire = dossier_existant
            cand.doublon_decision = DecisionDoublon.DOSSIER_EXISTANT_UTILISE
        else:
            cand.doublon_decision = DecisionDoublon.PERSONNE_DIFFERENTE
        cand.doublon_probable = False
        cand.commentaire = commentaire
        enregistrer(cand, acteur)
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=cand, centre=cand.centre_id, avant=avant,
                    apres=instantane(cand, ["beneficiaire", "doublon_decision", "doublon_probable"]),
                    motif=commentaire)
    return cand


def rejeter_candidature(acteur, cand, motif, commentaire):
    decision = verifier(acteur, "candidature", "V", centre=cand.centre_id, nominatif=True)
    exiger_statut(cand, (StatutCandidature.SOUMISE,), "Rejeter")
    if motif is None or not commentaire:
        raise RegleMetier("Motif (référentiel) et commentaire obligatoires.")
    return _transition(acteur, cand, StatutCandidature.REJETEE, motif=motif, commentaire=commentaire,
                       valide=True, interim=decision.interim)


def placer_en_attente(acteur, cand, session=None):
    """Validée → En liste d'attente, par le responsable pédagogique : session complète ou non programmée."""
    verifier(acteur, "inscription", "C", centre=cand.centre_id)
    exiger_statut(cand, (StatutCandidature.VALIDEE,), "Placer en attente")
    if session is not None:
        from caef.formations.services import places_occupees

        if session.capacite and places_occupees(session) < session.capacite:
            raise RegleMetier("La session a encore des places : inscrivez directement.")
    return _transition(acteur, cand, StatutCandidature.EN_ATTENTE)


def annuler_candidature(acteur, cand, commentaire, motif=None):
    """Toute sauf Inscrite → Annulée ; motif obligatoire. La Matrice réserve « A » au RC et au RA
    (voir DECISIONS.md : la SFD cite l'agent)."""
    verifier(acteur, "candidature", "A", centre=cand.centre_id, nominatif=True)
    if cand.statut in (StatutCandidature.INSCRITE, StatutCandidature.ANNULEE):
        raise RegleMetier("Une candidature inscrite ou déjà annulée ne s'annule pas.")
    if not commentaire:
        raise RegleMetier("Le motif d'annulation est obligatoire.")
    return _transition(acteur, cand, StatutCandidature.ANNULEE, motif=motif, commentaire=commentaire)


# --------------------------------------------------------------------------- transfert

def demander_transfert(acteur, beneficiaire, centre_accueil, motif):
    """Demandé par le centre d'accueil (RG-BEN-06)."""
    verifier(acteur, "transfert", "C", centre=centre_accueil, nominatif=True)
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    if beneficiaire.centre_rattachement_id == getattr(centre_accueil, "pk", centre_accueil):
        raise RegleMetier("La bénéficiaire est déjà rattachée à ce centre.")
    if Transfert.objects.filter(beneficiaire=beneficiaire, statut=StatutTransfert.DEMANDE).exists():
        raise RegleMetier("Un transfert est déjà en attente pour ce dossier.")
    with transaction.atomic():
        t = Transfert.objects.create(beneficiaire=beneficiaire, centre_origine_id=beneficiaire.centre_rattachement_id,
                                     centre_accueil=centre_accueil, motif=motif, demande_par=acteur, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=t, centre=t.centre_origine_id,
                    apres=instantane(t), motif=motif)
        notifier_role(t.centre_origine_id, ("RC",), "transfert_demande",
                      f"Transfert du dossier {beneficiaire.code} demandé : à valider.", t)
    return t


def decider_transfert(acteur, transfert, accepte: bool, motif=""):
    """Validé par le centre d'origine ; le code et l'historique ne changent pas."""
    decision = verifier(acteur, "transfert", "V", centre=transfert.centre_origine_id, nominatif=True)
    exiger_statut(transfert, (StatutTransfert.DEMANDE,), "Décider du transfert")
    if not accepte and not motif:
        raise RegleMetier("Le motif du refus est obligatoire.")
    with transaction.atomic():
        transfert.statut = StatutTransfert.ACCEPTE if accepte else StatutTransfert.REFUSE
        transfert.decide_par = acteur
        transfert.decide_le = timezone.now()
        enregistrer(transfert, acteur, ["statut", "decide_par", "decide_le"])
        if accepte:
            b = transfert.beneficiaire
            b.centre_rattachement_id = transfert.centre_accueil_id
            enregistrer(b, acteur, ["centre_rattachement"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=transfert, centre=transfert.centre_origine_id,
                    avant={"statut": "demande"}, apres={"statut": transfert.statut}, motif=motif,
                    interim=decision.interim)
    return transfert


# --------------------------------------------------------------------------- fusion

CHAMPS_FUSIONNABLES = ("nom", "prenoms", "autres_noms", "date_naissance", "annee_naissance", "tranche_age", "sexe",
                       "telephone", "zone_residence", "niveau_etudes", "situation_entree", "consentement_date",
                       "consentement_mode", "autorisation_image")


def _verifier_droit_fusion(acteur, a, b):
    """RC du centre si un seul centre est concerné ; Suivi-évaluation si deux centres (RG-BEN-05)."""
    centres = {a.centre_rattachement_id, b.centre_rattachement_id}
    decisions = [verifier(acteur, "fusion", "V", centre=c, nominatif=True) for c in centres]
    if len(centres) > 1 and "SE" not in roles_de(acteur):
        raise AccesRefuse("Une fusion entre deux centres relève du Suivi-évaluation (RG-BEN-05).",
                          objet="fusion", action="V")
    return any(d.interim for d in decisions)


def fusionner(acteur, conserve, absorbe, choix: dict, paire=None):
    """Jamais automatique : le dossier conservé et, champ par champ, la valeur retenue."""
    if conserve.pk == absorbe.pk:
        raise RegleMetier("Choisissez deux dossiers distincts.")
    interim = _verifier_droit_fusion(acteur, conserve, absorbe)
    for b in (conserve, absorbe):
        if b.statut == StatutBeneficiaire.FUSIONNE:
            raise RegleMetier(f"Le dossier {b.code} est déjà fusionné.")
    inconnus = set(choix) - set(CHAMPS_FUSIONNABLES)
    if inconnus or any(v not in ("conserve", "absorbe") for v in choix.values()):
        raise RegleMetier("Choix de fusion invalide.", details={"champs": sorted(inconnus)})
    sessions_conserve = set(conserve.inscriptions.values_list("session_id", flat=True))
    if absorbe.inscriptions.filter(session_id__in=sessions_conserve).exists():
        raise RegleMetier("Les deux dossiers sont inscrits à la même session : régularisez d'abord l'inscription.")
    with transaction.atomic():
        valeurs_avant = instantane(conserve, CHAMPS_FUSIONNABLES)
        for champ, cote in choix.items():
            if cote == "absorbe":
                attname = Beneficiaire._meta.get_field(champ).attname
                setattr(conserve, attname, getattr(absorbe, attname))
        _remplir_cles(conserve)
        enregistrer(conserve, acteur)
        candidatures = list(absorbe.candidatures.values_list("pk", flat=True))
        inscriptions = list(absorbe.inscriptions.values_list("pk", flat=True))
        absorbe.candidatures.update(beneficiaire=conserve)
        from caef.formations.models import Inscription

        Inscription.objects.filter(pk__in=inscriptions).update(beneficiaire=conserve)
        statut_avant = absorbe.statut
        absorbe.statut = StatutBeneficiaire.FUSIONNE
        absorbe.fusionne_dans = conserve
        enregistrer(absorbe, acteur, ["statut", "fusionne_dans"])
        fusion = Fusion.objects.create(
            conserve=conserve, absorbe=absorbe, choix=choix, valeurs_avant=valeurs_avant,
            statut_absorbe_avant=statut_avant, candidatures=[str(i) for i in candidatures],
            inscriptions=[str(i) for i in inscriptions], paire=paire, fusionne_par=acteur,
            fusionne_le=timezone.now(), cree_par=acteur)
        if paire is not None:
            paire.statut = StatutPaire.FUSIONNEES
            paire.traitee_par = acteur
            paire.traitee_le = timezone.now()
            paire.save(update_fields=["statut", "traitee_par", "traitee_le"])
        journaliser(ActionJournal.FUSION, utilisateur=acteur, objet=fusion, centre=conserve.centre_rattachement_id,
                    avant={"conserve": valeurs_avant, "absorbe": absorbe.code},
                    apres={"conserve": instantane(conserve, CHAMPS_FUSIONNABLES), "choix": choix},
                    nb_lignes=len(candidatures) + len(inscriptions), interim=interim)
    return fusion


def annuler_fusion(acteur, fusion, motif):
    """Réversible pendant 30 jours (BEN-09)."""
    interim = _verifier_droit_fusion(acteur, fusion.conserve, fusion.absorbe)
    if fusion.annulee_le:
        raise RegleMetier("Cette fusion est déjà annulée.")
    if timezone.now() > fusion.fusionne_le + timedelta(days=parametre("FUSION_REVERSIBLE_JOURS")):
        raise RegleMetier("Le délai d'annulation de la fusion est dépassé.", code="fusion_irreversible")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    from caef.formations.models import Inscription

    with transaction.atomic():
        conserve, absorbe = fusion.conserve, fusion.absorbe
        for champ, valeur in fusion.valeurs_avant.items():
            f = Beneficiaire._meta.get_field(champ)
            setattr(conserve, f.attname, f.to_python(valeur) if valeur is not None else None)
        _remplir_cles(conserve)
        enregistrer(conserve, acteur)
        Candidature.objects.filter(pk__in=fusion.candidatures).update(beneficiaire=absorbe)
        Inscription.objects.filter(pk__in=fusion.inscriptions).update(beneficiaire=absorbe)
        absorbe.statut = fusion.statut_absorbe_avant
        absorbe.fusionne_dans = None
        enregistrer(absorbe, acteur, ["statut", "fusionne_dans"])
        fusion.annulee_par = acteur
        fusion.annulee_le = timezone.now()
        fusion.motif_annulation = motif
        enregistrer(fusion, acteur, ["annulee_par", "annulee_le", "motif_annulation"])
        if fusion.paire_id:
            PaireDoublon.objects.filter(pk=fusion.paire_id).update(statut=StatutPaire.A_TRAITER)
        journaliser(ActionJournal.FUSION, utilisateur=acteur, objet=fusion, centre=conserve.centre_rattachement_id,
                    avant={"statut": "fusionnee"}, apres={"statut": "annulee"}, motif=motif, interim=interim)
    return fusion


def declarer_paire_distincte(acteur, paire, commentaire):
    """« Ce n'est pas un doublon » (E-BEN-05)."""
    _verifier_droit_fusion(acteur, paire.beneficiaire_a, paire.beneficiaire_b)
    if not commentaire:
        raise RegleMetier("Le commentaire est obligatoire.")
    with transaction.atomic():
        paire.statut = StatutPaire.DISTINCTES
        paire.traitee_par = acteur
        paire.traitee_le = timezone.now()
        paire.commentaire = commentaire
        paire.save(update_fields=["statut", "traitee_par", "traitee_le", "commentaire"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=paire,
                    centre=paire.beneficiaire_a.centre_rattachement_id, apres={"statut": paire.statut},
                    motif=commentaire)
    return paire


def recalculer_paires() -> int:
    """RG-BEN-04 : analyse nocturne des paires suspectes, par blocs de clés phonétiques."""
    seuil = parametre("SEUIL_DOUBLON_INFORMATIF")
    blocs: dict[str, list] = {}
    dossiers = Beneficiaire.objects.exclude(statut=StatutBeneficiaire.FUSIONNE).only(
        "id", "nom", "prenoms", "autres_noms", "date_naissance", "annee_naissance", "precision_naissance",
        "zone_residence_id", "telephone", "cle_phonetique", "nom_normalise")
    signatures = {}
    for b in dossiers.iterator():
        signatures[b.pk] = _signature_dossier(b)
        for mot in set(b.cle_phonetique.split()):
            blocs.setdefault(mot, []).append(b.pk)
    deja = set(PaireDoublon.objects.values_list("beneficiaire_a_id", "beneficiaire_b_id"))
    nouvelles = 0
    vus = set()
    for ids in blocs.values():
        if len(ids) > 2000:  # mot trop fréquent : ce bloc n'aide pas à départager
            continue
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                cle = (a, b) if str(a) < str(b) else (b, a)
                if cle in vus:
                    continue
                vus.add(cle)
                score, champs = score_doublon(signatures[cle[0]], signatures[cle[1]])
                if score < seuil:
                    continue
                if cle in deja:
                    PaireDoublon.objects.filter(beneficiaire_a_id=cle[0], beneficiaire_b_id=cle[1],
                                                statut=StatutPaire.A_TRAITER).update(score=score,
                                                                                     champs_concordants=champs)
                    continue
                PaireDoublon.objects.create(beneficiaire_a_id=cle[0], beneficiaire_b_id=cle[1], score=score,
                                            champs_concordants=champs)
                nouvelles += 1
    return nouvelles
