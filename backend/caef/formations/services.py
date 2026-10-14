"""Sessions, séances, inscriptions, présences, résultats et attestations (SFD § 5, RG-FOR-01 à 12)."""

import math
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from caef.commun.codes import code_annuel
from caef.commun.exceptions import AccesRefuse, RegleMetier
from caef.commun.services import enregistrer, exiger_statut, jour_reel, maintenant, origine, parametre
from caef.habilitations.services import aujourd_hui, roles_de, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import instantane, journaliser
from caef.notifications.services import notifier_role

from .models import (
    STATUTS_FINAUX,
    Attestation,
    EtatPresence,
    Evaluation,
    Formateur,
    Inscription,
    Presence,
    Seance,
    SessionFormation,
    StatutAttestation,
    StatutParticipation,
    StatutSession,
)

# --------------------------------------------------------------------------- périmètre « (s) »

def formateur_de(utilisateur) -> Formateur | None:
    if not getattr(utilisateur, "is_authenticated", False):
        return None
    return Formateur.objects.filter(utilisateur=utilisateur, archive=False).first()


def est_formateur_de_session(utilisateur, session) -> bool:
    """Formateur principal, associé ou animateur d'une séance de la session (périmètre (s))."""
    session_id = getattr(session, "pk", session)
    return SessionFormation.objects.filter(pk=session_id).filter(q_sessions_du_formateur(utilisateur, "")).exists()


def q_sessions_du_formateur(utilisateur, prefixe: str) -> Q:
    """Filtre « sessions affectées » ; `prefixe` est le chemin vers la session (« » pour la session)."""
    p = f"{prefixe}__" if prefixe else ""
    return (
        Q(**{f"{p}formateur_principal__utilisateur": utilisateur})
        | Q(**{f"{p}formateurs_associes__utilisateur": utilisateur})
        | Q(**{f"{p}seances__formateur__utilisateur": utilisateur})
    )


# --------------------------------------------------------------------------- sessions

CHAMPS_OUVERTURE = ("formation", "centre", "periode", "date_debut", "date_fin", "lieu", "capacite",
                    "formateur_principal")


def creer_session(acteur, *, formation, centre, periode, date_debut, date_fin, **champs):
    verifier(acteur, "session", "C", centre=centre)
    if formation.portee == "centre" and formation.centre_id != getattr(centre, "pk", centre):
        raise RegleMetier("Cette formation est propre à un autre centre.")
    if formation.statut != "active":
        raise RegleMetier("La formation est inactive.")
    if date_fin < date_debut:
        raise RegleMetier("La date de fin doit suivre la date de début.")
    with transaction.atomic():
        session = SessionFormation.objects.create(
            code=code_annuel("SES", centre.code, date_debut.year, 4), formation=formation, centre=centre,
            periode=periode, date_debut=date_debut, date_fin=date_fin, cree_par=acteur, **champs, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=session, centre=centre,
                    apres=instantane(session))
    return session


def modifier_session(acteur, session, version=None, **champs):
    verifier(acteur, "session", "M", centre=session.centre_id)
    from caef.commun.services import verifier_version

    verifier_version(session, version)
    exiger_statut(session, (StatutSession.BROUILLON, StatutSession.OUVERTE, StatutSession.EN_COURS), "Modifier")
    autorises = {"lieu", "capacite", "formateur_principal", "date_debut", "date_fin", "programme"}
    if set(champs) - autorises:
        raise RegleMetier("Champ non modifiable : " + ", ".join(sorted(set(champs) - autorises)))
    avant = instantane(session)
    for nom, valeur in champs.items():
        setattr(session, nom, valeur)
    if session.date_fin < session.date_debut:
        raise RegleMetier("La date de fin doit suivre la date de début.")
    if session.capacite is not None and session.capacite < session.inscriptions.exclude(
            statut_participation=StatutParticipation.ABANDONNEE).count():
        raise RegleMetier("La capacité ne peut descendre sous le nombre d'inscrites.")
    with transaction.atomic():
        enregistrer(session, acteur)
        av, ap = _diff(avant, instantane(session))
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=session, centre=session.centre_id,
                    avant=av, apres=ap)
    return session


def _diff(avant, apres):
    from caef.journal.services import difference

    return difference(avant, apres)


def ouvrir_session(acteur, session):
    """Brouillon → Ouverte : champs obligatoires remplis et au moins une séance planifiée (FOR-13)."""
    verifier(acteur, "session", "M", centre=session.centre_id)
    exiger_statut(session, (StatutSession.BROUILLON,), "Ouvrir les inscriptions")
    manquants = [c for c in CHAMPS_OUVERTURE if getattr(session, session._meta.get_field(c).attname) in (None, "")]
    if manquants:
        raise RegleMetier("Champs obligatoires manquants : " + ", ".join(manquants), details={"manquants": manquants})
    if not session.seances.filter(archive=False).exists():
        raise RegleMetier("Planifiez au moins une séance avant d'ouvrir les inscriptions.")
    return _changer_statut(acteur, session, StatutSession.OUVERTE, date_ouverture=timezone.now())


def demarrer_sessions_echues(jour=None):
    """Ouverte → En cours, automatiquement à la première séance passée, s'il y a au moins une inscrite."""
    jour = jour or aujourd_hui()
    demarrees = []
    for session in SessionFormation.objects.filter(statut=StatutSession.OUVERTE, seances__date__lte=jour).distinct():
        if session.inscriptions.exists():
            _changer_statut(None, session, StatutSession.EN_COURS)
            demarrees.append(session)
    return demarrees


def cloturer_session(acteur, session, commentaire=""):
    """En cours → Clôturée : présences saisies et statut final pour chaque inscrite (FOR-10, RG-FOR-11)."""
    verifier(acteur, "session", "M", centre=session.centre_id)
    exiger_statut(session, (StatutSession.EN_COURS,), "Clôturer")
    seances_sans_presences = [s for s in session.seances.filter(archive=False, date__lte=aujourd_hui())
                              if not s.presences_validees]
    if seances_sans_presences:
        raise RegleMetier("Des séances n'ont pas leurs présences validées.",
                          details={"seances": [str(s.pk) for s in seances_sans_presences]})
    if session.seances.filter(archive=False, date__gt=aujourd_hui()).exists():
        raise RegleMetier("Des séances restent à venir.")
    sans_statut = session.inscriptions.exclude(statut_participation__in=STATUTS_FINAUX)
    if sans_statut.exists():
        raise RegleMetier("Chaque inscrite doit avoir un statut final (achevée, non achevée ou abandonnée).",
                          details={"inscriptions": [str(i) for i in sans_statut.values_list("pk", flat=True)]})
    with transaction.atomic():
        session.commentaire_cloture = commentaire
        session.rapport_cloture = rapport_cloture(session, commentaire)
        _changer_statut(acteur, session, StatutSession.CLOTUREE, date_cloture=timezone.now())
    return session


def annuler_session(acteur, session, motif):
    """Brouillon ou Ouverte → Annulée, par le responsable de centre ; les inscrites repassent
    « Validée » (leur candidature), ou en liste d'attente si elles y étaient."""
    verifier(acteur, "session", "A", centre=session.centre_id)
    exiger_statut(session, (StatutSession.BROUILLON, StatutSession.OUVERTE), "Annuler")
    if not motif:
        raise RegleMetier("Le motif d'annulation est obligatoire.")
    from caef.beneficiaires.models import StatutCandidature

    with transaction.atomic():
        for ins in session.inscriptions.select_related("candidature"):
            cand = ins.candidature
            if cand.statut == StatutCandidature.INSCRITE:
                cand.statut = StatutCandidature.VALIDEE
                enregistrer(cand, acteur, ["statut"])
            ins.archive = True
            ins.archive_le = timezone.now()
            enregistrer(ins, acteur, ["archive", "archive_le"])
        session.motif_annulation = motif
        _changer_statut(acteur, session, StatutSession.ANNULEE, motif=motif)
    return session


def rouvrir_session(acteur, session, motif):
    """Clôturée → En cours, par le responsable de centre, motif obligatoire et journalisé (FOR-14)."""
    verifier(acteur, "session", "A", centre=session.centre_id)
    exiger_statut(session, (StatutSession.CLOTUREE,), "Rouvrir")
    if not motif:
        raise RegleMetier("Le motif de réouverture est obligatoire.")
    return _changer_statut(acteur, session, StatutSession.EN_COURS, motif=motif, date_cloture=None)


def _changer_statut(acteur, session, statut, motif="", **champs):
    avant = session.statut
    session.statut = statut
    for k, v in champs.items():
        setattr(session, k, v)
    with transaction.atomic():
        session.marquer_modifie(acteur)
        session.save()
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=session, centre=session.centre_id,
                    avant={"statut": avant}, apres={"statut": statut}, motif=motif)
    return session


# --------------------------------------------------------------------------- séances

def planifier_seance(acteur, session, *, date, heure_debut, heure_fin, formateur, theme=""):
    verifier(acteur, "session", "M", centre=session.centre_id)
    exiger_statut(session, (StatutSession.BROUILLON, StatutSession.OUVERTE, StatutSession.EN_COURS),
                  "Planifier une séance")
    if not (session.date_debut <= date <= session.date_fin):
        raise RegleMetier("La séance doit se situer dans les dates de la session.")
    if heure_fin <= heure_debut:
        raise RegleMetier("L'heure de fin doit suivre l'heure de début.")
    _verifier_chevauchement_formateur(formateur, date, heure_debut, heure_fin)
    with transaction.atomic():
        seance = Seance.objects.create(session=session, date=date, heure_debut=heure_debut, heure_fin=heure_fin,
                                       formateur=formateur, theme=theme, cree_par=acteur, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=seance, centre=session.centre_id,
                    apres=instantane(seance))
    return seance


def _verifier_chevauchement_formateur(formateur, date, debut, fin, exclure=None):
    """RG-FOR-02 : un formateur ne peut animer deux séances qui se chevauchent."""
    qs = Seance.objects.filter(formateur=formateur, date=date, archive=False, heure_debut__lt=fin,
                               heure_fin__gt=debut).exclude(session__statut=StatutSession.ANNULEE)
    if exclure is not None:
        qs = qs.exclude(pk=exclure.pk)
    autre = qs.select_related("session").first()
    if autre:
        raise RegleMetier(
            f"Le formateur anime déjà une séance qui se chevauche ({autre.session.code}, "
            f"{autre.heure_debut:%H:%M}-{autre.heure_fin:%H:%M}).", code="chevauchement_formateur")


# --------------------------------------------------------------------------- inscriptions

def places_occupees(session) -> int:
    return session.inscriptions.filter(archive=False).exclude(
        statut_participation=StatutParticipation.ABANDONNEE).count()


def capacite_maximale_avec_derogation(session) -> int:
    return session.capacite + math.floor(session.capacite * parametre("DEROGATION_CAPACITE_PCT") / 100)


def inscrire(acteur, candidature, session, *, derogation_motif=""):
    """RG-FOR-05 et RG-FOR-03 : candidature validée ou en attente, session ouverte ou en cours,
    place disponible (ou dérogation de 10 % au plus par le responsable de centre, motivée),
    pas d'autre inscription active sur des séances simultanées."""
    from caef.beneficiaires.models import StatutCandidature

    verifier(acteur, "inscription", "C", centre=session.centre_id)
    exiger_statut(candidature, (StatutCandidature.VALIDEE, StatutCandidature.EN_ATTENTE), "Inscrire")
    exiger_statut(session, (StatutSession.OUVERTE, StatutSession.EN_COURS), "Inscrire")
    if candidature.formation_id != session.formation_id:
        raise RegleMetier("La candidature porte sur une autre formation.")
    if candidature.centre_id != session.centre_id:
        raise RegleMetier("La session se tient dans un autre centre que celui de la candidature.")
    beneficiaire = candidature.beneficiaire
    if Inscription.objects.filter(beneficiaire=beneficiaire, session=session, archive=False).exists():
        raise RegleMetier("Cette bénéficiaire est déjà inscrite à la session.")

    occupees = places_occupees(session)
    derogation = False
    if occupees >= session.capacite:
        if not derogation_motif:
            raise RegleMetier("Session complète : placez la candidature en liste d'attente ou demandez une "
                              "dérogation au responsable de centre.", code="session_complete",
                              details={"capacite": session.capacite, "occupees": occupees})
        if not roles_de(acteur, session.centre_id) & {"RC", "RA"}:
            raise AccesRefuse("Seul le responsable de centre peut déroger à la capacité (RG-FOR-03).",
                              objet="inscription", action="C", centre_id=session.centre_id)
        if occupees + 1 > capacite_maximale_avec_derogation(session):
            raise RegleMetier("La dérogation dépasse 10 % de la capacité.", code="derogation_depassee")
        derogation = True

    _verifier_seances_simultanees(beneficiaire, session)
    with transaction.atomic():
        ins = Inscription.objects.create(
            beneficiaire=beneficiaire, session=session, candidature=candidature, date_inscription=jour_reel(),
            derogation_motif=derogation_motif if derogation else "", derogation_par=acteur if derogation else None,
            cree_par=acteur, **origine())
        avant = candidature.statut
        candidature.statut = StatutCandidature.INSCRITE
        enregistrer(candidature, acteur, ["statut"])
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=ins, centre=session.centre_id,
                    apres=instantane(ins), motif=derogation_motif if derogation else "")
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=candidature, centre=session.centre_id,
                    avant={"statut": avant}, apres={"statut": candidature.statut})
        # RG-PAY-02 : échéances des services liés, si le module est activé et un tarif en vigueur.
        from caef.facturation.services import creer_echeances_inscription

        creer_echeances_inscription(acteur, ins)
    return ins


def _verifier_seances_simultanees(beneficiaire, session):
    actives = Inscription.objects.filter(beneficiaire=beneficiaire, archive=False).exclude(
        statut_participation__in=STATUTS_FINAUX).exclude(session=session).exclude(
        session__statut__in=[StatutSession.ANNULEE, StatutSession.CLOTUREE])
    for seance in session.seances.filter(archive=False):
        conflit = Seance.objects.filter(session__inscriptions__in=actives, date=seance.date, archive=False,
                                        heure_debut__lt=seance.heure_fin, heure_fin__gt=seance.heure_debut).first()
        if conflit:
            raise RegleMetier("La bénéficiaire suit déjà une séance simultanée dans une autre session.",
                              code="seances_simultanees")


def designer_cheffe_de_classe(acteur, inscription):
    """Une seule par session, désignée par le formateur de la session ou le RP (Matrice § 2.1)."""
    session = inscription.session
    verifier(acteur, "presence", "M", centre=session.centre_id, session=session)
    if Inscription.objects.filter(session=session, cheffe_de_classe=True).exclude(pk=inscription.pk).exists():
        raise RegleMetier("Une cheffe de classe est déjà désignée pour cette session (TF-ORG-01).",
                          code="cheffe_de_classe_existante")
    with transaction.atomic():
        inscription.cheffe_de_classe = True
        enregistrer(inscription, acteur, ["cheffe_de_classe"])
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=inscription, centre=session.centre_id,
                    avant={"cheffe_de_classe": False}, apres={"cheffe_de_classe": True})
    return inscription


def changer_participation(acteur, inscription, statut, *, motif_sortie=None, motif=""):
    """Suspendue ou reprise, ou Abandonnée (motif du référentiel obligatoire) ; jamais automatique."""
    session = inscription.session
    verifier(acteur, "inscription", "M", centre=session.centre_id)
    permis = {
        StatutParticipation.SUSPENDUE: (StatutParticipation.INSCRITE, StatutParticipation.COMMENCEE),
        StatutParticipation.COMMENCEE: (StatutParticipation.SUSPENDUE,),
        StatutParticipation.ABANDONNEE: (StatutParticipation.INSCRITE, StatutParticipation.COMMENCEE,
                                         StatutParticipation.SUSPENDUE),
    }
    if statut not in permis:
        raise RegleMetier("Les statuts Achevée et Non achevée se décident à la clôture (RG-FOR-09).")
    exiger_statut(inscription, permis[statut], "Changer la participation", champ="statut_participation")
    if statut == StatutParticipation.ABANDONNEE and motif_sortie is None:
        raise RegleMetier("Le motif d'abandon (référentiel) est obligatoire.")
    if statut == StatutParticipation.SUSPENDUE and not motif:
        raise RegleMetier("Le motif de suspension est obligatoire.")
    avant = inscription.statut_participation
    with transaction.atomic():
        inscription.statut_participation = statut
        if statut == StatutParticipation.ABANDONNEE:
            inscription.motif_sortie = motif_sortie
            inscription.date_statut_final = jour_reel()
        enregistrer(inscription)
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=inscription, centre=session.centre_id,
                    avant={"statut_participation": avant}, apres={"statut_participation": statut}, motif=motif)
    return inscription


# --------------------------------------------------------------------------- présences

def saisir_presences(acteur, seance, etats: dict, *, motif_tardif="", valider=True):
    """Feuille de présence d'une séance (E-FOR-07).

    `etats` : {inscription_id: état}. RG-FOR-06 : du jour de la séance à J+7 ; au-delà, seul le
    responsable pédagogique saisit, avec motif. Un formateur ne saisit que pour ses sessions.
    """
    session = seance.session
    verifier(acteur, "presence", "C", centre=session.centre_id, session=session)
    exiger_statut(session, (StatutSession.OUVERTE, StatutSession.EN_COURS), "Saisir les présences")
    jour = jour_reel()
    if jour < seance.date:
        raise RegleMetier("Les présences se saisissent à partir du jour de la séance.")
    tardive = jour > seance.date + timedelta(days=parametre("DELAI_SAISIE_PRESENCES_JOURS"))
    if tardive:
        if "RP" not in roles_de(acteur, session.centre_id):
            raise AccesRefuse("Après 7 jours, seul le responsable pédagogique saisit les présences (RG-FOR-06).",
                              objet="presence", action="C", centre_id=session.centre_id)
        if not motif_tardif:
            raise RegleMetier("Le motif de la saisie tardive est obligatoire (RG-FOR-06).")
    inscriptions = {str(i.pk): i for i in session.inscriptions.filter(archive=False)}
    inconnues = [k for k in etats if str(k) not in inscriptions]
    if inconnues:
        raise RegleMetier("Inscription étrangère à la session.", details={"inscriptions": inconnues})
    valeurs = set(EtatPresence.values)
    instant = maintenant()
    with transaction.atomic():
        for ins_id, etat in etats.items():
            if etat not in valeurs:
                raise RegleMetier(f"État de présence inconnu : {etat}.")
            ins = inscriptions[str(ins_id)]
            if ins.statut_participation in (StatutParticipation.ABANDONNEE, StatutParticipation.SUSPENDUE):
                continue
            if seance.date < ins.date_inscription:
                continue
            presence = Presence.objects.filter(seance=seance, inscription=ins).first()
            if presence is None:
                presence = Presence.objects.create(seance=seance, inscription=ins, etat=etat, saisi_par=acteur,
                                                   saisi_le=instant, saisie_tardive_motif=motif_tardif if tardive else "",
                                                   cree_par=acteur, **origine())
                journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=presence, centre=session.centre_id,
                            apres={"etat": etat}, motif=motif_tardif if tardive else "")
            elif presence.etat != etat:
                ancien = presence.etat
                presence.etat = etat
                presence.saisi_par = acteur
                presence.saisi_le = instant
                if tardive:
                    presence.saisie_tardive_motif = motif_tardif
                enregistrer(presence, acteur)
                journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=presence,
                            centre=session.centre_id, avant={"etat": ancien}, apres={"etat": etat},
                            motif=motif_tardif if tardive else "")
            if ins.statut_participation == StatutParticipation.INSCRITE and \
                    etat in (EtatPresence.PRESENTE, EtatPresence.RETARD):
                ins.statut_participation = StatutParticipation.COMMENCEE
                enregistrer(ins, acteur, ["statut_participation"])
            _mettre_a_jour_taux(ins)
        if valider:
            seance.presences_validees = True
            seance.presences_validees_le = timezone.now()
            enregistrer(seance, acteur, ["presences_validees", "presences_validees_le"])
        _alerter_absences_consecutives(session, inscriptions.values())
    return seance


def taux_presence(inscription) -> Decimal | None:
    """RG-FOR-08 : (présente + retard) / séances passées depuis l'inscription ; absence justifiée
    exclue du dénominateur si la formation le prévoit. Aucune séance passée : non renseigné."""
    formation = inscription.session.formation
    seances = inscription.session.seances.filter(archive=False, date__lte=aujourd_hui(),
                                                 date__gte=inscription.date_inscription)
    total = seances.count()
    presences = {p.seance_id: p.etat for p in inscription.presences.all()}
    if formation.absence_justifiee_exclue:
        total -= sum(1 for s in seances if presences.get(s.pk) == EtatPresence.ABSENCE_JUSTIFIEE)
    if total <= 0:
        return None
    presents = sum(1 for e in presences.values() if e in (EtatPresence.PRESENTE, EtatPresence.RETARD))
    return (Decimal(presents) * 100 / Decimal(total)).quantize(Decimal("0.1"))


def _mettre_a_jour_taux(inscription):
    taux = taux_presence(inscription)
    if taux != inscription.taux_presence:
        inscription.taux_presence = taux
        inscription.save(update_fields=["taux_presence"])


def _alerter_absences_consecutives(session, inscriptions):
    """RG-FOR-07 : trois absences non justifiées consécutives alertent le RP ; jamais d'abandon automatique."""
    seuil = parametre("ABSENCES_CONSECUTIVES_ALERTE")
    for ins in inscriptions:
        if ins.statut_participation in STATUTS_FINAUX:
            continue
        derniers = list(Presence.objects.filter(inscription=ins).order_by("-seance__date", "-seance__heure_debut")
                        .values_list("etat", flat=True)[:seuil])
        if len(derniers) == seuil and all(e == EtatPresence.ABSENTE for e in derniers):
            notifier_role(session.centre_id, ("RP",), "absences_consecutives",
                          f"{seuil} absences non justifiées consécutives dans la session {session.code} : "
                          f"confirmez ou non l'abandon.", ins)


# --------------------------------------------------------------------------- résultats et clôture

def saisir_evaluation(acteur, inscription, *, intitule, date, type_resultat, note=None, note_max=None,
                      appreciation=""):
    session = inscription.session
    verifier(acteur, "evaluation", "C", centre=session.centre_id, session=session)
    with transaction.atomic():
        ev = Evaluation.objects.create(inscription=inscription, intitule=intitule, date=date,
                                       type_resultat=type_resultat, note=note, note_max=note_max,
                                       appreciation=appreciation, cree_par=acteur, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=ev, centre=session.centre_id,
                    apres=instantane(ev))
    return ev


def modifier_evaluation(acteur, evaluation, **champs):
    """RG-FOR-10 : l'ancienne valeur reste dans l'historique (journal)."""
    session = evaluation.inscription.session
    verifier(acteur, "evaluation", "M", centre=session.centre_id, session=session)
    avant = instantane(evaluation)
    for k in ("note", "note_max", "appreciation", "intitule", "date"):
        if k in champs:
            setattr(evaluation, k, champs[k])
    with transaction.atomic():
        enregistrer(evaluation, acteur)
        av, ap = _diff(avant, instantane(evaluation))
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=evaluation, centre=session.centre_id,
                    avant=av, apres=ap, motif=champs.get("motif", ""))
    return evaluation


def proposition_achevement(inscription) -> str:
    """RG-FOR-09 : proposition selon le seuil de présence et, si requise, l'évaluation."""
    formation = inscription.session.formation
    taux = taux_presence(inscription)
    if taux is None or taux < formation.seuil_presence_pct:
        return StatutParticipation.NON_ACHEVEE
    if formation.evaluation_requise and not inscription.evaluations.filter(archive=False).exists():
        return StatutParticipation.NON_ACHEVEE
    return StatutParticipation.ACHEVEE


def propositions_de_cloture(session) -> list[dict]:
    return [
        {"inscription": str(i.pk), "proposition": proposition_achevement(i), "taux_presence": taux_presence(i)}
        for i in session.inscriptions.filter(archive=False).exclude(
            statut_participation=StatutParticipation.ABANDONNEE)
    ]


def confirmer_statut_final(acteur, inscription, statut, *, motif_derogation=""):
    """Le RP confirme la proposition ; toute dérogation est motivée et journalisée (FOR-08)."""
    session = inscription.session
    verifier(acteur, "evaluation", "V", centre=session.centre_id)
    if statut not in (StatutParticipation.ACHEVEE, StatutParticipation.NON_ACHEVEE):
        raise RegleMetier("Statut final attendu : Achevée ou Non achevée.")
    exiger_statut(inscription, (StatutParticipation.INSCRITE, StatutParticipation.COMMENCEE,
                                StatutParticipation.SUSPENDUE), "Confirmer le statut final",
                  champ="statut_participation")
    proposition = proposition_achevement(inscription)
    if statut != proposition and not motif_derogation:
        raise RegleMetier("Ce statut diffère de la proposition : le motif de la dérogation est obligatoire.",
                          code="derogation_sans_motif", details={"proposition": proposition})
    avant = inscription.statut_participation
    with transaction.atomic():
        inscription.statut_participation = statut
        inscription.date_statut_final = jour_reel()
        inscription.taux_presence = taux_presence(inscription)
        enregistrer(inscription, acteur)
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=inscription, centre=session.centre_id,
                    avant={"statut_participation": avant},
                    apres={"statut_participation": statut, "proposition": proposition},
                    motif=motif_derogation)
    return inscription


def rapport_cloture(session, commentaire="") -> dict:
    """RG-FOR-11 : rapport de clôture (R-01) généré automatiquement."""
    inscriptions = list(session.inscriptions.filter(archive=False).select_related("motif_sortie"))
    abandons = {}
    for i in inscriptions:
        if i.statut_participation == StatutParticipation.ABANDONNEE:
            cle = i.motif_sortie.libelle if i.motif_sortie else "non renseigné"
            abandons[cle] = abandons.get(cle, 0) + 1
    taux = [i.taux_presence for i in inscriptions if i.taux_presence is not None]
    return {
        "session": session.code,
        "inscrites": len(inscriptions),
        "commencees": sum(1 for i in inscriptions if i.statut_participation != StatutParticipation.INSCRITE),
        "achevees": sum(1 for i in inscriptions if i.statut_participation == StatutParticipation.ACHEVEE),
        "non_achevees": sum(1 for i in inscriptions if i.statut_participation == StatutParticipation.NON_ACHEVEE),
        "abandons_par_motif": abandons,
        "attestations": Attestation.objects.filter(inscription__session=session,
                                                   statut=StatutAttestation.DELIVREE).count(),
        # Moyenne des taux renseignés ; aucun taux : non renseigné (null), jamais 0.
        "taux_presence_moyen": str((sum(taux) / len(taux)).quantize(Decimal("0.1"))) if taux else None,
        "commentaire": commentaire,
        "genere_le": timezone.now().isoformat(),
    }


def delivrer_attestation(acteur, inscription):
    """Seulement si la participation est « Achevée » et que la formation prévoit une attestation."""
    session = inscription.session
    verifier(acteur, "attestation", "V", centre=session.centre_id)
    if inscription.statut_participation != StatutParticipation.ACHEVEE:
        raise RegleMetier("L'attestation exige une participation « Achevée » (FOR-07).")
    if not session.formation.attestation_prevue:
        raise RegleMetier("Cette formation ne prévoit pas d'attestation.")
    if Attestation.objects.filter(inscription=inscription, statut=StatutAttestation.DELIVREE).exists():
        raise RegleMetier("Une attestation est déjà délivrée pour cette inscription.")
    jour = aujourd_hui()
    with transaction.atomic():
        att = Attestation.objects.create(
            inscription=inscription, numero=code_annuel("ATT", session.centre.code, jour.year),
            date_delivrance=jour, delivre_par=acteur, cree_par=acteur)
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=att, centre=session.centre_id,
                    apres=instantane(att))
    return att


def annuler_attestation(acteur, attestation, motif):
    session = attestation.inscription.session
    verifier(acteur, "attestation", "V", centre=session.centre_id)
    exiger_statut(attestation, (StatutAttestation.DELIVREE,), "Annuler")
    if not motif:
        raise RegleMetier("Le motif d'annulation est obligatoire.")
    with transaction.atomic():
        attestation.statut = StatutAttestation.ANNULEE
        attestation.motif_annulation = motif
        enregistrer(attestation, acteur, ["statut", "motif_annulation"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=attestation, centre=session.centre_id,
                    avant={"statut": "delivree"}, apres={"statut": "annulee"}, motif=motif)
    return attestation
