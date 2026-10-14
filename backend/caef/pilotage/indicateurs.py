"""Calcul nocturne des indicateurs dans le schéma de pilotage (Référentiel des indicateurs, RG-TDB-01).

Règles communes (Référentiel § 2.2) :
- une valeur absente est « non renseignée » (None), jamais 0 ;
- un module désactivé pour le centre donne « Module non activé », jamais 0 (RG-ADM-20) ;
- les centres fictifs ne comptent jamais ; une bénéficiaire fusionnée non plus ;
- financier et en nature, déclaratif et vérifié, et chaque devise restent séparés ;
- taux à une décimale, montants à l'unité, aucun arrondi intermédiaire.
"""

import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from caef.habilitations.services import module_actif

from .models import FicheIndicateur, ValeurIndicateur


@dataclass
class Valeur:
    valeur: Decimal | None
    ventilation: str = ""
    valeur_declarative: Decimal | None = None
    numerateur: Decimal | None = None
    denominateur: Decimal | None = None
    nb_non_renseignes: int = 0
    niveau: str = "verifie"
    details: dict = field(default_factory=dict)


def taux(num, den) -> Decimal | None:
    if not den:
        return None
    return (Decimal(num) * 100 / Decimal(den)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _unite(v):
    return None if v is None else Decimal(v).quantize(Decimal(1), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- formation et bénéficiaires

def ind_01(centres, debut, fin):
    from caef.formations.models import SessionFormation

    n = SessionFormation.objects.filter(centre__in=centres, centre__statut="actif", statut__in=[
        "ouverte", "en_cours", "cloturee"], date_debut__lte=fin, date_fin__gte=debut).values("centre").distinct().count()
    return [Valeur(Decimal(n))]


def ind_02(centres, debut, fin):
    from caef.beneficiaires.models import Beneficiaire

    n = Beneficiaire.objects.filter(centre_rattachement__in=centres, cree_le__date__lte=fin).exclude(
        statut="fusionne").count()
    return [Valeur(Decimal(n))]


def ind_03(centres, debut, fin):
    from caef.formations.models import Inscription

    fenetre = fin - timedelta(days=_p("JOURS_BENEFICIAIRE_ACTIVE"))
    n = Inscription.objects.filter(session__centre__in=centres, archive=False, date_inscription__lte=fin).filter(
        Q(statut_participation__in=["inscrite", "commencee", "suspendue"])
        | Q(statut_participation="achevee", date_statut_final__gte=fenetre, date_statut_final__lte=fin)
    ).exclude(beneficiaire__statut="fusionne").values("beneficiaire").distinct().count()
    return [Valeur(Decimal(n))]


def ind_04(centres, debut, fin):
    from caef.beneficiaires.models import Candidature

    qs = Candidature.objects.filter(centre__in=centres, date_soumission__date__gte=debut,
                                    date_soumission__date__lte=fin).exclude(statut="brouillon")
    decidees = qs.filter(statut__in=["validee", "rejetee", "en_attente", "inscrite"]).count()
    validees = qs.filter(statut__in=["validee", "en_attente", "inscrite"]).count()
    return [Valeur(None, valeur_declarative=Decimal(qs.count()), niveau="declaratif",
                   details={"taux_validation": str(taux(validees, decidees)) if decidees else None})]


def ind_05(centres, debut, fin):
    from caef.formations.models import SessionFormation

    n = SessionFormation.objects.filter(centre__in=centres, date_ouverture__date__gte=debut,
                                        date_ouverture__date__lte=fin).count()
    return [Valeur(Decimal(n))]


def ind_06(centres, debut, fin):
    from caef.formations.models import SessionFormation

    n = SessionFormation.objects.filter(centre__in=centres, statut="cloturee", date_cloture__date__gte=debut,
                                        date_cloture__date__lte=fin, rapport_cloture__isnull=False).count()
    return [Valeur(Decimal(n))]


def ind_07(centres, debut, fin):
    from caef.formations.models import Inscription

    qs = Inscription.objects.filter(session__centre__in=centres, session__statut="cloturee", archive=False,
                                    session__date_cloture__date__gte=debut, session__date_cloture__date__lte=fin)
    finales = qs.filter(statut_participation__in=["achevee", "non_achevee", "abandonnee"]).count()
    achevees = qs.filter(statut_participation="achevee").count()
    manquantes = qs.count() - finales
    return [Valeur(taux(achevees, finales), numerateur=Decimal(achevees), denominateur=Decimal(finales),
                   nb_non_renseignes=manquantes)]


def ind_08(centres, debut, fin):
    from caef.formations.models import Presence, Seance

    seances = Seance.objects.filter(session__centre__in=centres, date__gte=debut, date__lte=fin, archive=False)
    validees = seances.filter(presences_validees=True)
    p = Presence.objects.filter(seance__in=validees)
    presents = p.filter(etat__in=["presente", "retard"]).count()
    attendues = p.exclude(etat="absence_justifiee").count()
    return [Valeur(taux(presents, attendues), numerateur=Decimal(presents), denominateur=Decimal(attendues),
                   nb_non_renseignes=seances.filter(presences_validees=False, date__lt=timezone.localdate()).count())]


def ind_09(centres, debut, fin):
    from caef.formations.models import Attestation

    qs = Attestation.objects.filter(inscription__session__centre__in=centres, statut="delivree",
                                    date_delivrance__gte=debut, date_delivrance__lte=fin)
    return [Valeur(Decimal(qs.count()),
                   details={"beneficiaires_distinctes": qs.values("inscription__beneficiaire").distinct().count()})]


def ind_10(centres, debut, fin):
    from caef.beneficiaires.models import Candidature

    qs = Candidature.objects.filter(centre__in=centres, valide_le__date__gte=debut, valide_le__date__lte=fin,
                                    date_soumission__isnull=False)
    delais = [(c.valide_le - c.date_soumission).days for c in qs.only("valide_le", "date_soumission")]
    if not delais:
        return [Valeur(None)]
    return [Valeur(Decimal(statistics.median(delais)).quantize(Decimal("0.1")),
                   details={"moyenne": str(Decimal(statistics.mean(delais)).quantize(Decimal("0.1"))),
                            "nombre": len(delais)})]


# --------------------------------------------------------------------------- RSE

def _par_devise(qs, champ):
    return {d: t for d, t in qs.values_list("devise").annotate(t=Sum(champ))}


def ind_20(centres, debut, fin):
    from caef.conventions.models import Convention

    n = Convention.objects.filter(centres__in=centres, statut__in=["signee", "en_execution"],
                                  date_signature__lte=fin).values("partenaire").distinct().count()
    return [Valeur(Decimal(n))]


def ind_21(centres, debut, fin):
    from caef.conventions.models import Proposition

    qs = Proposition.objects.filter(centres_beneficiaires__in=centres, statut__in=["soumise", "acceptee", "refusee"],
                                    date_envoi__gte=debut, date_envoi__lte=fin).distinct()
    return [Valeur(None, ventilation=f"devise:{d}", valeur_declarative=_unite(t), niveau="declaratif")
            for d, t in _par_devise(qs, "montant_sollicite").items()] or [Valeur(None, niveau="declaratif")]


def ind_22(centres, debut, fin):
    from caef.conventions.models import Convention

    qs = Convention.objects.filter(centres__in=centres, date_signature__gte=debut, date_signature__lte=fin).exclude(
        statut="en_preparation").distinct()
    return [Valeur(_unite(t), ventilation=f"devise:{d}") for d, t in _par_devise(qs, "montant_accorde").items()] \
        or [Valeur(Decimal(0))]


def ind_23(centres, debut, fin):
    from caef.conventions.models import Contribution

    base = Contribution.objects.filter(centre_beneficiaire__in=centres, financiere=True, date_reception__gte=debut,
                                       date_reception__lte=fin)
    valides = _par_devise(base.filter(statut="validee"), "montant_recu")
    recues = _par_devise(base.filter(statut="recue"), "montant_recu")
    devises = set(valides) | set(recues) or {"GNF"}
    return [Valeur(_unite(valides.get(d, 0)), ventilation=f"devise:{d}", valeur_declarative=_unite(recues.get(d)))
            for d in devises]


def ind_24(centres, debut, fin):
    from caef.conventions.models import Contribution

    qs = Contribution.objects.filter(centre_beneficiaire__in=centres, financiere=False, statut="validee",
                                     date_reception__gte=debut, date_reception__lte=fin)
    sans_valeur = qs.filter(valeur_estimee__isnull=True).count()
    valeurs = _par_devise(qs.filter(valeur_estimee__isnull=False), "valeur_estimee")
    return [Valeur(_unite(t), ventilation=f"devise:{d}", nb_non_renseignes=sans_valeur) for d, t in valeurs.items()] \
        or [Valeur(None, nb_non_renseignes=sans_valeur)]


def ind_26(centres, debut, fin):
    from caef.partenaires.models import Opportunite

    qs = Opportunite.objects.filter(centres__in=centres, modifie_le__date__gte=debut, modifie_le__date__lte=fin,
                                    statut__in=["gagnee", "perdue"]).distinct()
    gagnees = qs.filter(statut="gagnee").count()
    return [Valeur(taux(gagnees, qs.count()), numerateur=Decimal(gagnees), denominateur=Decimal(qs.count()))]


def ind_27(centres, debut, fin):
    from caef.conventions.models import Engagement

    qs = Engagement.objects.filter(Q(centre__in=centres) | Q(convention__centres__in=centres), etat="en_retard").distinct()
    return [Valeur(Decimal(qs.filter(partie=p).count()), ventilation=f"partie:{p}") for p in ("partenaire", "caef")]


def ind_28(centres, debut, fin):
    from caef.conventions.models import Convention

    n = Convention.objects.filter(centres__in=centres, statut="en_execution", date_fin__gte=fin,
                                  date_fin__lte=fin + timedelta(days=90)).distinct().count()
    return [Valeur(Decimal(n))]


# --------------------------------------------------------------------------- qualité des données et adoption

def ind_30(centres, debut, fin):
    from caef.beneficiaires.models import Beneficiaire

    qs = Beneficiaire.objects.filter(centre_rattachement__in=centres, statut="actif")
    n = qs.count()
    if not n:
        return [Valeur(None)]
    moyenne = qs.aggregate(m=Sum("completude"))["m"] / Decimal(n)
    return [Valeur(moyenne.quantize(Decimal("0.1")), details={"part_complets": str(taux(qs.filter(completude=100).count(), n))})]


def ind_31(centres, debut, fin):
    from caef.beneficiaires.models import PaireDoublon

    qs = PaireDoublon.objects.filter(Q(beneficiaire_a__centre_rattachement__in=centres)
                                     | Q(beneficiaire_b__centre_rattachement__in=centres),
                                     detectee_le__date__gte=debut, detectee_le__date__lte=fin).distinct()
    traitees = qs.exclude(statut="a_traiter").count()
    return [Valeur(Decimal(qs.count()), details={"part_traitee": str(taux(traitees, qs.count()))})]


def ind_33(centres, debut, fin):
    from caef.formations.models import Seance

    tenues = Seance.objects.filter(session__centre__in=centres, date__gte=debut, date__lte=fin, archive=False)
    dans_delai = sum(1 for s in tenues.filter(presences_validees=True)
                     if timezone.localdate(s.presences_validees_le) <= s.date + timedelta(days=2))
    return [Valeur(taux(dans_delai, tenues.count()), numerateur=Decimal(dans_delai), denominateur=Decimal(tenues.count()))]


def ind_34(centres, debut, fin):
    from caef.conventions.models import Contribution

    qs = Contribution.objects.filter(centre_beneficiaire__in=centres, statut__in=["recue", "validee"])
    justifiees = qs.filter(statut="validee", justificatifs__isnull=False).distinct().count()
    en_attente = qs.filter(statut="recue", date_reception__lt=fin - timedelta(days=30)).count()
    return [Valeur(taux(justifiees, qs.count()), details={"recues_en_attente_30_jours": en_attente})]


def ind_40(centres, debut, fin):
    from caef.habilitations.models import Affectation
    from caef.identite.models import Utilisateur
    from caef.journal.models import JournalAudit

    ids = Affectation.objects.filter(centre__in=centres, archive=False).exclude(role_id="ADM").values("utilisateur")
    comptes = Utilisateur.objects.filter(pk__in=ids, statut="actif")
    depuis = fin - timedelta(days=30)
    actifs = comptes.filter(last_login__date__gte=depuis, pk__in=JournalAudit.objects.filter(
        horodatage__date__gte=depuis, horodatage__date__lte=fin).exclude(
        action__in=["connexion", "echec_connexion", "acces_refuse"]).values("utilisateur")).count()
    return [Valeur(taux(actifs, comptes.count()), numerateur=Decimal(actifs), denominateur=Decimal(comptes.count()))]


# --------------------------------------------------------------------------- boutique et clôture

def _ventes_non_annulees(centres, debut, fin):
    from caef.boutique.models import Vente

    return Vente.objects.filter(point_de_vente__centre__in=centres, statut="validee", contre_ecriture__isnull=True,
                                date_heure_vente__date__gte=debut, date_heure_vente__date__lte=fin)


def _caisse_validee(qs):
    return qs.filter(session_caisse__statut__in=["validee", "validee_avec_ecart"])


def ind_45(centres, debut, fin):
    qs = _ventes_non_annulees(centres, debut, fin)
    verif = _caisse_validee(qs).aggregate(t=Sum("total"))["t"]
    decl = qs.exclude(pk__in=_caisse_validee(qs).values("pk")).aggregate(t=Sum("total"))["t"]
    return [Valeur(_unite(verif or 0), valeur_declarative=_unite(decl))]


def ind_46(centres, debut, fin):
    qs = _ventes_non_annulees(centres, debut, fin)
    verif = _caisse_validee(qs).count()
    return [Valeur(Decimal(verif), valeur_declarative=Decimal(qs.count() - verif))]


def ind_47(centres, debut, fin):
    from caef.boutique.models import Reversement

    qs = Reversement.objects.filter(point_de_vente__centre__in=centres, statut="paye", date_paiement__gte=debut,
                                    date_paiement__lte=fin)
    return [Valeur(_unite(qs.aggregate(t=Sum("montant_reverse"))["t"] or 0),
                   details={"productrices_payees": qs.values("beneficiaire", "groupement").distinct().count()})]


def ind_48(centres, debut, fin):
    from caef.boutique.models import SessionCaisse

    qs = SessionCaisse.objects.filter(point_de_vente__centre__in=centres, date__gte=debut, date__lte=fin,
                                      statut__in=["validee", "validee_avec_ecart"])
    avec = qs.filter(statut="validee_avec_ecart")
    return [Valeur(taux(avec.count(), qs.count()), numerateur=Decimal(avec.count()), denominateur=Decimal(qs.count()),
                   details={"ecart_cumule": str(avec.aggregate(t=Sum("ecart"))["t"] or 0)})]


def ind_49(centres, debut, fin):
    from caef.boutique.models import LigneVente

    lignes = LigneVente.objects.filter(vente__in=_ventes_non_annulees(centres, debut, fin),
                                       produit__origine__in=["depot_vente", "groupement"])
    n = lignes.values("produit__beneficiaire_deposante", "produit__groupement").distinct().count()
    return [Valeur(Decimal(n))]


def ind_50(centres, debut, fin):
    from .cloture import bornes
    from .models import ClotureMensuelle

    aujourd = timezone.localdate()
    mois = []
    d = debut.replace(day=1)
    while d <= fin:
        cle = f"{d.year:04d}-{d.month:02d}"
        _, dernier = bornes(cle)
        limite = dernier + timedelta(days=10)
        if dernier < aujourd and not (aujourd <= limite):
            mois.append((cle, limite))
        d = (dernier + timedelta(days=1))
    if not mois:
        return [Valeur(None)]
    total = len(mois) * len(centres)
    ok = 0
    avec_ecart = 0
    for cle, limite in mois:
        qs = ClotureMensuelle.objects.filter(centre__in=centres, mois=cle, verrouillee=True,
                                             validee_le__date__lte=limite)
        ok += qs.count()
        avec_ecart += qs.filter(statut="validee_avec_ecart").count()
    return [Valeur(taux(ok, total), numerateur=Decimal(ok), denominateur=Decimal(total),
                   details={"mois_valides_avec_ecart": avec_ecart})]


# --------------------------------------------------------------------------- registre et calcul

INDICATEURS = {
    "IND-01": ("Centres actifs", ind_01, "socle", False),
    "IND-02": ("Bénéficiaires enregistrées", ind_02, "socle", True),
    "IND-03": ("Bénéficiaires actives", ind_03, "socle", True),
    "IND-04": ("Candidatures reçues", ind_04, "socle", True),
    "IND-05": ("Sessions de formation ouvertes", ind_05, "socle", True),
    "IND-06": ("Sessions de formation clôturées", ind_06, "socle", True),
    "IND-07": ("Taux d'achèvement", ind_07, "socle", True),
    "IND-08": ("Taux d'assiduité", ind_08, "socle", True),
    "IND-09": ("Attestations délivrées", ind_09, "socle", True),
    "IND-10": ("Délai de traitement des candidatures", ind_10, "socle", True),
    "IND-20": ("Partenariats RSE actifs", ind_20, "socle", False),
    "IND-21": ("Montant sollicité", ind_21, "socle", False),
    "IND-22": ("Montant accordé", ind_22, "socle", False),
    "IND-23": ("Montant encaissé", ind_23, "socle", True),
    "IND-24": ("Valeur des contributions en nature reçues", ind_24, "socle", True),
    "IND-26": ("Taux de transformation", ind_26, "socle", False),
    "IND-27": ("Engagements en retard", ind_27, "socle", True),
    "IND-28": ("Conventions à renouveler", ind_28, "socle", False),
    "IND-30": ("Complétude des dossiers", ind_30, "socle", True),
    "IND-31": ("Doublons détectés", ind_31, "socle", True),
    "IND-33": ("Présences saisies dans les délais", ind_33, "socle", True),
    "IND-34": ("Contributions reçues justifiées", ind_34, "socle", False),
    "IND-40": ("Utilisateurs actifs", ind_40, "socle", True),
    "IND-45": ("Chiffre d'affaires de la boutique", ind_45, "boutique", True),
    "IND-46": ("Nombre de ventes", ind_46, "boutique", True),
    "IND-47": ("Revenus reversés aux productrices", ind_47, "boutique", True),
    "IND-48": ("Taux de clôtures de caisse avec écart", ind_48, "boutique", True),
    "IND-49": ("Productrices actives en boutique", ind_49, "boutique", True),
    "IND-50": ("Clôtures mensuelles rapprochées dans les délais", ind_50, "socle", True),
}


def _p(nom):
    from caef.commun.services import parametre

    return parametre(nom)


def synchroniser_fiches():
    for code, (libelle, _, module, _) in INDICATEURS.items():
        FicheIndicateur.objects.get_or_create(code=code, defaults={"libelle": libelle, "module": module})


def _enregistrer(code, version, centre, debut, fin, v: Valeur, module_non_active=False):
    ValeurIndicateur.objects.update_or_create(
        indicateur=code, centre=centre, periode_debut=debut, periode_fin=fin, ventilation=v.ventilation,
        defaults=dict(version_fiche=version, valeur=v.valeur, valeur_declarative=v.valeur_declarative,
                      numerateur=v.numerateur, denominateur=v.denominateur, nb_non_renseignes=v.nb_non_renseignes,
                      module_non_active=module_non_active, niveau=v.niveau, details=v.details,
                      calcule_le=timezone.now()))


def calculer(debut: date, fin: date, codes=None):
    """Par centre réel puis au national (centres fictifs exclus). Une valeur figée (période close)
    n'est jamais recalculée (RG-TDB-04)."""
    from caef.referentiels.models import Centre

    synchroniser_fiches()
    reels = list(Centre.objects.filter(fictif=False))
    fiches = {f.code: f for f in FicheIndicateur.objects.all()}
    for code, (_, fonction, module, par_centre) in INDICATEURS.items():
        if codes and code not in codes:
            continue
        if fiches[code].statut == "retiree":
            continue
        version = fiches[code].version
        if ValeurIndicateur.objects.filter(indicateur=code, periode_debut=debut, periode_fin=fin, fige=True).exists():
            continue
        with transaction.atomic():
            if par_centre:
                for c in reels:
                    if module != "socle" and not module_actif(c.pk, module, fin):
                        _enregistrer(code, version, c, debut, fin, Valeur(None), module_non_active=True)
                        continue
                    for v in fonction([c], debut, fin):
                        _enregistrer(code, version, c, debut, fin, v)
            actifs = [c for c in reels if module == "socle" or module_actif(c.pk, module, fin)]
            for v in fonction(actifs, debut, fin):
                v.details = {**v.details, "centres_couverts": f"{len(actifs)} centres sur {len(reels)}"}
                _enregistrer(code, version, None, debut, fin, v, module_non_active=not actifs)


def calculer_indicateurs(jour=None):
    """Tâche nocturne : mois courant et mois précédent."""
    from .cloture import bornes

    jour = jour or timezone.localdate()
    calculer(*bornes(f"{jour.year:04d}-{jour.month:02d}"))
    precedent_fin = jour.replace(day=1) - timedelta(days=1)
    calculer(precedent_fin.replace(day=1), precedent_fin)
