"""Service habilitations : rôle, périmètre, module et intérim, vérifiés côté serveur (SEC-01).

Ordre des contrôles (DAT § 4.1, règle 6) : module activé pour le centre, puis droit de la Matrice
pour l'une des affectations actives, puis périmètre, puis conditions (intérim, à défaut de CPT).
Tout ce qui n'est pas explicitement accordé est refusé.
"""

from dataclasses import dataclass, field
from datetime import date

from django.db.models import Q
from django.utils import timezone

from caef.commun.exceptions import AccesRefuse, ModuleNonActive

from .matrice import MODULE_SOCLE, matrice
from .models import Affectation, InterimResponsable, ModuleCentre, StatutModule


def aujourd_hui() -> date:
    return timezone.localdate()


# --------------------------------------------------------------------------- modules par centre

def module_actif(centre_id, module: str, jour: date | None = None) -> bool:
    """Statut en vigueur : ligne validée de date d'effet la plus récente (ADM-08)."""
    if module in (None, MODULE_SOCLE):
        return True
    jour = jour or aujourd_hui()
    if module == "salle_exposition" and not module_actif(centre_id, "boutique", jour):
        return False
    ligne = (
        ModuleCentre.objects.filter(centre_id=centre_id, module=module, valide_par__isnull=False,
                                    date_effet__lte=jour)
        .order_by("-date_effet", "-valide_le")
        .first()
    )
    return bool(ligne and ligne.statut == StatutModule.ACTIF)


def modules_actifs(centre_id, jour: date | None = None) -> list[str]:
    from .models import ModuleOptionnel

    return [m for m in ModuleOptionnel.values if module_actif(centre_id, m, jour)]


# --------------------------------------------------------------------------- affectations et intérims

def affectations_actives(utilisateur, jour: date | None = None) -> list[Affectation]:
    """Affectations en cours, rôle actif ; celles d'un rôle propre à un module désactivé pour le
    centre (VB sans boutique) sont suspendues (règle 9)."""
    if not getattr(utilisateur, "is_authenticated", False) or not utilisateur.is_active:
        return []
    jour = jour or aujourd_hui()
    cache = getattr(utilisateur, "_caef_affectations", None)
    if cache and cache[0] == jour:
        return cache[1]
    m = matrice()
    resultat = []
    qs = (
        Affectation.objects.select_related("role", "centre")
        .filter(utilisateur=utilisateur, archive=False, role__actif=True, date_debut__lte=jour)
        .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=jour))
    )
    for aff in qs:
        role = m.roles.get(aff.role_id)
        if role is None:
            continue
        if role.module != MODULE_SOCLE and aff.centre_id and not module_actif(aff.centre_id, role.module, jour):
            continue
        resultat.append(aff)
    utilisateur._caef_affectations = (jour, resultat)
    return resultat


def invalider_cache(utilisateur):
    if hasattr(utilisateur, "_caef_affectations"):
        del utilisateur._caef_affectations


def roles_de(utilisateur, centre_id=None) -> set[str]:
    return {
        a.role_id for a in affectations_actives(utilisateur)
        if centre_id is None or a.national or a.centre_id == centre_id
    }


def interim_en_cours(adjoint, centre_id, jour: date | None = None) -> InterimResponsable | None:
    """Un intérim ne vaut qu'entre ses dates, sans copie de droits (USR-09, RG-ADM-14)."""
    jour = jour or aujourd_hui()
    return (
        InterimResponsable.objects.filter(
            adjoint=adjoint, centre_id=centre_id, archive=False, date_debut__lte=jour, date_fin__gte=jour
        )
        .filter(Q(interrompu_le__isnull=True) | Q(interrompu_le__gt=jour))
        .first()
    )


def centre_a_un_comptable(centre_id, jour: date | None = None) -> bool:
    jour = jour or aujourd_hui()
    return (
        Affectation.objects.filter(role_id="CPT", centre_id=centre_id, archive=False, date_debut__lte=jour,
                                   utilisateur__statut="actif")
        .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=jour))
        .exists()
    )


# --------------------------------------------------------------------------- décision

@dataclass
class Decision:
    autorise: bool
    motif: str = ""
    perimetre: str | None = None
    interim: bool = False
    lecture_historique: bool = False
    agrege_seulement: bool = False
    module_inactif: str | None = None


def _perimetre_couvre(droit, aff, objet, centre_id) -> bool:
    if not objet.centre or centre_id is None:
        return True
    if droit.perimetre in ("n", "ag"):
        return objet.reseau or aff.national or aff.centre_id == centre_id
    return aff.national or aff.centre_id == centre_id


def decider(utilisateur, objet: str, action: str, *, centre=None, session=None, cible_utilisateur=None,
            nominatif: bool = False, jour: date | None = None) -> Decision:
    """Décide sans lever d'exception. `centre` : centre de l'objet visé (instance ou identifiant)."""
    m = matrice()
    obj = m.objet(objet)
    jour = jour or aujourd_hui()
    centre_id = getattr(centre, "pk", centre)
    affectations = affectations_actives(utilisateur, jour)
    if not affectations:
        return Decision(False, "Aucune affectation active.")

    module_inactif = (
        obj.module if (obj.centre and centre_id is not None and not module_actif(centre_id, obj.module, jour))
        else None
    )

    meilleure = None
    motif_refus = "Droit absent de la Matrice des rôles."
    for aff in affectations:
        droit = m.droit(aff.role_id, objet, action)
        if droit is None:
            continue
        if not _perimetre_couvre(droit, aff, obj, centre_id):
            motif_refus = "Hors de votre périmètre."
            continue
        if module_inactif:
            if action == "L" and aff.role_id in m.lecture_historique:
                return Decision(True, perimetre=droit.perimetre, lecture_historique=True,
                                module_inactif=module_inactif)
            motif_refus = "Module non activé."
            continue
        if droit.perimetre == "s" and session is not None and not _est_formateur_de(utilisateur, session):
            motif_refus = "Session hors de vos sessions affectées."
            continue
        if droit.perimetre == "p" and cible_utilisateur is not None and \
                getattr(cible_utilisateur, "pk", cible_utilisateur) != utilisateur.pk:
            motif_refus = "Seule votre propre fiche est accessible."
            continue
        if nominatif and droit.perimetre == "ag":
            motif_refus = "Vous ne voyez que des données agrégées, sans nom."
            continue
        interim = False
        if droit.condition == "interim" and aff.role_id == "RA":
            cid = centre_id if centre_id is not None else aff.centre_id
            if interim_en_cours(utilisateur, cid, jour) is None:
                motif_refus = "Validation réservée au responsable de centre hors intérim déclaré."
                continue
            interim = True
        if droit.condition == "a_defaut_cpt":
            cid = centre_id if centre_id is not None else aff.centre_id
            if centre_a_un_comptable(cid, jour):
                motif_refus = "Validation réservée au comptable du centre."
                continue
        decision = Decision(True, perimetre=droit.perimetre, interim=interim,
                            agrege_seulement=droit.perimetre == "ag")
        if not interim and not decision.agrege_seulement:
            return decision
        if meilleure is None or (meilleure.interim and not interim):
            meilleure = decision
    if meilleure:
        return meilleure
    if module_inactif:
        return Decision(False, "Module non activé.", module_inactif=module_inactif)
    return Decision(False, motif_refus)


def verifier(utilisateur, objet: str, action: str, **kwargs) -> Decision:
    """Comme `decider`, mais lève AccesRefuse (journalisé par l'appelant) en cas de refus."""
    decision = decider(utilisateur, objet, action, **kwargs)
    if decision.autorise:
        return decision
    centre = kwargs.get("centre")
    contexte_refus = dict(objet=objet, action=action, centre_id=getattr(centre, "pk", centre),
                          objet_type=kwargs.get("objet_type"), objet_id=kwargs.get("objet_id"))
    if decision.module_inactif:
        raise ModuleNonActive(decision.module_inactif, **contexte_refus)
    raise AccesRefuse(decision.motif or "Accès refusé.", **contexte_refus)


def _est_formateur_de(utilisateur, session) -> bool:
    from caef.formations.services import est_formateur_de_session

    return est_formateur_de_session(utilisateur, session)


# --------------------------------------------------------------------------- périmètre des listes

@dataclass
class Portee:
    """Ce qu'un utilisateur peut lister pour un objet : tout le réseau ou un ensemble de centres."""

    national: bool = False
    centres: set = field(default_factory=set)
    centres_sessions: set = field(default_factory=set)  # centres où seul (s) s'applique
    propre: bool = False
    agrege_seulement: bool = False
    lecture_historique: set = field(default_factory=set)

    @property
    def vide(self):
        return not (self.national or self.centres or self.centres_sessions or self.propre)


def portee(utilisateur, objet: str, action: str = "L", *, nominatif: bool = False,
           jour: date | None = None) -> Portee:
    from caef.referentiels.models import Centre

    m = matrice()
    obj = m.objet(objet)
    jour = jour or aujourd_hui()
    p = Portee()
    tous_les_centres = None
    agrege = True
    for aff in affectations_actives(utilisateur, jour):
        droit = m.droit(aff.role_id, objet, action)
        if droit is None:
            continue
        if nominatif and droit.perimetre == "ag":
            continue
        if droit.condition == "interim" and aff.role_id == "RA":
            if aff.centre_id is None or interim_en_cours(utilisateur, aff.centre_id, jour) is None:
                continue
        agrege = agrege and droit.perimetre == "ag"
        if droit.perimetre == "p":
            p.propre = True
            continue
        national = (not obj.centre) or obj.reseau or (aff.national and droit.perimetre in ("n", "ag", "c"))
        if national:
            if tous_les_centres is None:
                tous_les_centres = set(Centre.objects.values_list("pk", flat=True))
            centres = tous_les_centres
        else:
            centres = {aff.centre_id} if aff.centre_id else set()
        for cid in centres:
            if obj.centre and obj.module != MODULE_SOCLE and not module_actif(cid, obj.module, jour):
                if action == "L" and aff.role_id in m.lecture_historique:
                    p.lecture_historique.add(cid)
                    p.centres.add(cid)
                continue
            if droit.perimetre == "s":
                p.centres_sessions.add(cid)
            else:
                p.centres.add(cid)
    p.centres_sessions -= p.centres
    if tous_les_centres is not None and p.centres == tous_les_centres and not p.centres_sessions:
        p.national = True
    p.agrege_seulement = agrege and not p.vide
    return p
