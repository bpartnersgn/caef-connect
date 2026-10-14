"""Boutique et salle d'exposition (SFD § 9, RG-BOU-01 à 16).

Montants entiers en GNF ; une vente validée n'est jamais modifiée (contre-écriture) ; le stock est
la somme des mouvements ; aucune donnée sur l'acheteur.
"""

from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from caef.commun.champs import verifier_gnf_entier
from caef.commun.codes import code_annuel, prochain_numero
from caef.commun.contexte import contexte
from caef.commun.exceptions import AccesRefuse, RegleMetier, SeparationDesTaches
from caef.commun.services import enregistrer, exiger_statut, jour_reel, maintenant, origine
from caef.habilitations.services import aujourd_hui, roles_de, verifier
from caef.journal.models import ActionJournal
from caef.journal.services import instantane, journaliser
from caef.notifications.services import notifier_role
from caef.pilotage.verrou import mois_de, mois_verrouille, verifier_mois_ouvert

from .models import (
    TYPES_ENTREE,
    TYPES_SORTIE,
    Depot,
    Emplacement,
    Inventaire,
    LigneInventaire,
    LigneVente,
    ModeReglement,
    MouvementStock,
    OrigineProduit,
    PointDeVente,
    PrixProduit,
    Produit,
    Reglement,
    Reversement,
    SessionCaisse,
    StatutCaisse,
    StatutInventaire,
    StatutReglement,
    StatutReversement,
    StatutVente,
    Vente,
    stock,
)


def _gnf(valeur, libelle="Le montant"):
    from django.core.exceptions import ValidationError

    try:
        verifier_gnf_entier(valeur, libelle)
    except ValidationError as e:
        raise RegleMetier(e.messages[0], code="montant_non_entier")
    return Decimal(valeur)


def point_de_vente_actif(centre_id) -> PointDeVente:
    pdv = PointDeVente.objects.filter(centre_id=centre_id, actif=True).first()
    if pdv is None:
        raise RegleMetier("Ce centre n'a pas de point de vente actif.")
    return pdv


def _centre(pdv):
    return pdv.centre_id


# --------------------------------------------------------------------------- catalogue et prix

def creer_produit(acteur, pdv, *, nom, categorie, unite, origine, beneficiaire_deposante=None, groupement="",
                  session_origine=None, formation_origine=None, seuil_alerte=None, prix=None):
    verifier(acteur, "produit", "C", centre=pdv.centre_id)
    if origine == OrigineProduit.DEPOT_VENTE and beneficiaire_deposante is None and not groupement:
        raise RegleMetier("Un produit en dépôt-vente porte sa productrice déposante ou son groupement.")
    if beneficiaire_deposante is not None and origine not in (OrigineProduit.DEPOT_VENTE,):
        raise RegleMetier("Une productrice déposante ne s'indique que pour un dépôt-vente.")
    with transaction.atomic():
        p = Produit.objects.create(
            code=code_annuel("PRD", pdv.centre.code, aujourd_hui().year), point_de_vente=pdv, nom=nom,
            categorie=categorie, unite=unite, origine=origine, beneficiaire_deposante=beneficiaire_deposante,
            groupement=groupement, session_origine=session_origine, formation_origine=formation_origine,
            seuil_alerte=seuil_alerte, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=p, centre=pdv.centre_id, apres=instantane(p))
        if prix is not None:
            definir_prix(acteur, p, prix, aujourd_hui())
    return p


def prix_en_vigueur(produit, jour=None) -> PrixProduit | None:
    jour = jour or aujourd_hui()
    return (PrixProduit.objects.filter(produit=produit, date_debut__lte=jour)
            .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=jour)).order_by("-date_debut").first())


def definir_prix(acteur, produit, prix, date_debut):
    """RG-BOU-12 : une nouvelle période datée ; l'ancienne se termine la veille."""
    verifier(acteur, "produit", "M", centre=produit.point_de_vente.centre_id)
    prix = _gnf(prix, "Le prix")
    if prix <= 0:
        raise RegleMetier("Le prix doit être supérieur à 0.")
    if date_debut < aujourd_hui():
        raise RegleMetier("Un prix ne s'antidate pas : il prend effet aujourd'hui ou plus tard.")
    with transaction.atomic():
        courant = PrixProduit.objects.select_for_update().filter(produit=produit, date_fin__isnull=True).first()
        if courant is not None:
            if courant.date_debut >= date_debut:
                raise RegleMetier("Un prix plus récent existe déjà pour cette date.")
            courant.date_fin = date_debut - timedelta(days=1)
            courant._mise_a_jour_autorisee = True
            courant.save(update_fields=["date_fin"])
        nouveau = PrixProduit.objects.create(produit=produit, prix=prix, date_debut=date_debut, auteur=acteur,
                                             cree_par=acteur)
        journaliser(ActionJournal.MODIFICATION, utilisateur=acteur, objet=produit,
                    centre=produit.point_de_vente.centre_id,
                    avant={"prix": str(courant.prix) if courant else None},
                    apres={"prix": str(prix), "date_debut": date_debut})
    return nouveau


# --------------------------------------------------------------------------- stock

def _mouvement(acteur, produit, type_, quantite, *, motif="", emplacement=Emplacement.BOUTIQUE, quand=None, **liens):
    return MouvementStock.objects.create(produit=produit, type=type_, quantite=quantite,
                                         date_mouvement=quand or maintenant(), motif=motif, emplacement=emplacement,
                                         auteur=acteur, cree_par=acteur, **liens, **origine())


def _verifier_emplacement(centre_id, emplacement):
    if emplacement == Emplacement.SALLE_EXPOSITION:
        from caef.habilitations.services import module_actif

        if not module_actif(centre_id, "salle_exposition"):
            raise RegleMetier("La salle d'exposition n'est pas activée pour ce centre.")


def entrer_en_stock(acteur, produit, *, type, quantite, emplacement=Emplacement.BOUTIQUE, part_centre_pct=None,
                    motif=""):
    """E-BOU-03 : entrée de production, d'achat, ou dépôt-vente avec la part du centre."""
    centre_id = produit.point_de_vente.centre_id
    verifier(acteur, "stock_entree", "C", centre=centre_id)
    if type not in TYPES_ENTREE:
        raise RegleMetier("Type d'entrée inconnu.")
    quantite = Decimal(quantite)
    if quantite <= 0:
        raise RegleMetier("La quantité doit être supérieure à 0.")
    _verifier_emplacement(centre_id, emplacement)
    with transaction.atomic():
        depot = None
        if type == "entree_depot":
            if produit.origine != OrigineProduit.DEPOT_VENTE:
                raise RegleMetier("Ce produit n'est pas en dépôt-vente.")
            if part_centre_pct is None or not (0 <= Decimal(part_centre_pct) <= 100):
                raise RegleMetier("La part du centre (entre 0 et 100 %) est obligatoire pour un dépôt-vente.")
            depot = Depot.objects.create(beneficiaire=produit.beneficiaire_deposante,
                                         groupement="" if produit.beneficiaire_deposante_id else produit.groupement,
                                         produit=produit, quantite_deposee=quantite, part_centre_pct=part_centre_pct,
                                         date_depot=jour_reel(), cree_par=acteur, **origine())
        m = _mouvement(acteur, produit, type, quantite, motif=motif, emplacement=emplacement, depot=depot)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=m, centre=centre_id, apres=instantane(m))
    return m


def sortir_du_stock(acteur, produit, *, type, quantite, motif, emplacement=Emplacement.BOUTIQUE):
    """RG-BOU-03 : toute sortie (perte, don, échantillon, usage interne) exige un motif."""
    centre_id = produit.point_de_vente.centre_id
    verifier(acteur, "stock_entree", "C", centre=centre_id)
    if type not in TYPES_SORTIE:
        raise RegleMetier("Type de sortie inconnu.")
    if not motif:
        raise RegleMetier("Le motif de la sortie est obligatoire.")
    quantite = Decimal(quantite)
    if quantite <= 0:
        raise RegleMetier("La quantité doit être supérieure à 0.")
    with transaction.atomic():
        m = _mouvement(acteur, produit, type, -quantite, motif=motif, emplacement=emplacement)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=m, centre=centre_id, apres=instantane(m),
                    motif=motif)
    _alerter_stock(produit)
    return m


def transferer(acteur, produit, *, quantite, vers, motif=""):
    """RG-BOU-16 : sortant et entrant de même quantité, liés, sans effet sur le stock total."""
    centre_id = produit.point_de_vente.centre_id
    verifier(acteur, "salle_exposition", "C", centre=centre_id)
    depuis = Emplacement.BOUTIQUE if vers == Emplacement.SALLE_EXPOSITION else Emplacement.SALLE_EXPOSITION
    quantite = Decimal(quantite)
    if quantite <= 0:
        raise RegleMetier("La quantité doit être supérieure à 0.")
    if stock(produit, depuis) < quantite:
        raise RegleMetier("Quantité supérieure au stock de l'emplacement de départ.")
    with transaction.atomic():
        sortant = _mouvement(acteur, produit, "transfert", -quantite, motif=motif, emplacement=depuis)
        entrant = _mouvement(acteur, produit, "transfert", quantite, motif=motif, emplacement=vers,
                             transfert_lie=sortant)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=entrant, centre=centre_id,
                    apres={"produit": str(produit.pk), "quantite": str(quantite), "de": depuis, "vers": vers})
    return entrant


def _alerter_stock(produit):
    """RG-BOU-04 : stock négatif ou sous le seuil d'alerte."""
    s = stock(produit)
    if s < 0:
        notifier_role(produit.point_de_vente.centre_id, ("RC", "RA"), "stock_negatif",
                      f"Stock négatif pour {produit.nom} : à vérifier au prochain inventaire.", produit)
    elif produit.seuil_alerte is not None and s < produit.seuil_alerte:
        notifier_role(produit.point_de_vente.centre_id, ("RC", "RA", "VB"), "stock_sous_seuil",
                      f"Stock de {produit.nom} sous le seuil d'alerte.", produit)


# --------------------------------------------------------------------------- reçus

def _attribuer_recu(pdv, acteur, numero_propose=None):
    """RG-BOU-01 : série de l'appareil et numéro continu propre à l'appareil ; un numéro sauté
    (vente dont l'enregistrement a échoué sur l'appareil) est consigné comme annulé."""
    from caef.synchronisation.models import Appareil

    ctx = contexte()
    if ctx.appareil_id:
        appareil = Appareil.objects.select_for_update().get(pk=ctx.appareil_id)
        if appareil.point_de_vente_id != pdv.pk or not appareil.serie_recu:
            raise RegleMetier("Cet appareil n'a pas de série de reçus pour ce point de vente.")
        numero = numero_propose or appareil.dernier_numero_recu + 1
        if numero <= appareil.dernier_numero_recu:
            raise RegleMetier("Numéro de reçu déjà attribué sur cet appareil.", code="recu_deja_attribue")
        for saute in range(appareil.dernier_numero_recu + 1, numero):
            _consigner_numero_annule(pdv, acteur, appareil.serie_recu, saute)
        appareil.dernier_numero_recu = numero
        appareil.save(update_fields=["dernier_numero_recu"])
        return appareil.serie_recu, numero
    serie = f"{pdv.centre.code}-W"
    return serie, prochain_numero(f"RECU:{pdv.pk}:{serie}")


def _consigner_numero_annule(pdv, acteur, serie, numero):
    Vente.objects.create(point_de_vente=pdv, serie_recu=serie, numero_recu=numero, date_heure_vente=timezone.now(),
                         vendeur=acteur, total=0, statut=StatutVente.ANNULEE, cree_par=acteur,
                         motif_annulation="Numéro attribué à une vente non enregistrée (BOU-06).")


# --------------------------------------------------------------------------- ventes

def session_du_jour(pdv, jour) -> SessionCaisse | None:
    return SessionCaisse.objects.filter(point_de_vente=pdv, date=jour).first()


def vendre(acteur, pdv, *, lignes, reglements, numero_recu=None, numero_recu_papier=None, date_heure_vente=None,
           emplacement=Emplacement.BOUTIQUE):
    """E-BOU-04. `lignes` : [{produit, quantite, remise, motif_remise}] ; `reglements` :
    [{mode, montant, reference_externe, identifiant_transaction, telephone, paiement}].

    Le prix appliqué est le prix en vigueur à la date de la vente (S) ; le serveur calcule le total ;
    la somme des règlements doit l'égaler. Aucune donnée sur l'acheteur."""
    centre_id = pdv.centre_id
    verifier(acteur, "vente", "C", centre=centre_id)
    if not lignes:
        raise RegleMetier("Une vente comporte au moins une ligne.")
    if not reglements:
        raise RegleMetier("Au moins un règlement est requis.")
    _verifier_emplacement(centre_id, emplacement)
    quand = maintenant()
    if numero_recu_papier:
        # RG-BOU-13 : saisie différée le jour même, date et heure réelles du reçu papier.
        if date_heure_vente is None:
            raise RegleMetier("La date et l'heure réelles du reçu papier sont obligatoires.")
        if timezone.localdate(date_heure_vente) != timezone.localdate(quand):
            raise RegleMetier("Une vente sur reçu papier de secours se saisit le jour même.")
        if Vente.objects.filter(point_de_vente=pdv, numero_recu_papier=numero_recu_papier).exists():
            raise RegleMetier("Ce numéro de reçu papier est déjà saisi.", code="recu_papier_deja_saisi")
        quand = date_heure_vente
    jour = timezone.localdate(quand)
    verifier_mois_ouvert(centre_id, jour)
    session = session_du_jour(pdv, jour)
    if session is None or session.statut != StatutCaisse.OUVERTE:
        raise RegleMetier("La caisse de ce jour n'est pas ouverte.", code="caisse_non_ouverte")

    calcul = []
    total = Decimal(0)
    for l in lignes:
        produit = l["produit"]
        if produit.point_de_vente_id != pdv.pk or not produit.actif:
            raise RegleMetier(f"Produit indisponible : {produit.nom}.")
        quantite = Decimal(l["quantite"])
        if quantite <= 0:
            raise RegleMetier("La quantité doit être supérieure à 0.")
        prix = prix_en_vigueur(produit, jour)
        if prix is None:
            raise RegleMetier(f"Aucun prix en vigueur pour {produit.nom}.", code="prix_absent")
        remise = _gnf(l.get("remise") or 0, "La remise")
        brut = quantite * prix.prix
        if remise and not l.get("motif_remise"):
            raise RegleMetier("Une remise exige un motif.")
        if remise < 0 or remise > brut:
            raise RegleMetier("La remise est au plus égale au montant de la ligne.")
        montant = brut - remise
        _gnf(montant, "Le montant de la ligne")
        calcul.append((produit, quantite, prix.prix, remise, l.get("motif_remise", "")))
        total += montant
    somme = sum((_gnf(r["montant"], "Le règlement") for r in reglements), Decimal(0))
    if somme != total:
        raise RegleMetier(f"La somme des règlements ({somme}) doit égaler le total ({total}).",
                          code="reglements_total", details={"total": str(total), "reglements": str(somme)})

    with transaction.atomic():
        serie, numero = _attribuer_recu(pdv, acteur, numero_recu)
        vente = Vente.objects.create(point_de_vente=pdv, serie_recu=serie, numero_recu=numero,
                                     numero_recu_papier=numero_recu_papier, date_heure_vente=quand, vendeur=acteur,
                                     session_caisse=session, total=total, statut=StatutVente.VALIDEE,
                                     emplacement=emplacement, mois_corrige=contexte().supplements.get("mois_corrige", ""),
                                     cree_par=acteur, **origine())
        for produit, quantite, prix, remise, motif_remise in calcul:
            LigneVente.objects.create(vente=vente, produit=produit, quantite=quantite, prix_unitaire_applique=prix,
                                      remise=remise, motif_remise=motif_remise, cree_par=acteur)
            _mouvement(acteur, produit, "vente", -quantite, emplacement=emplacement, quand=quand, vente=vente)
        for r in reglements:
            _creer_reglement(acteur, vente, r)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=vente, centre=centre_id,
                    apres={"recu": vente.numero_complet, "total": str(total), "lignes": len(calcul)})
    for produit, *_ in calcul:
        _alerter_stock(produit)
    return vente


def _creer_reglement(acteur, vente, r):
    mode = r["mode"]
    if mode not in ModeReglement.values:
        raise RegleMetier("Mode de règlement inconnu (espèces, Mobile Money, virement, chèque).")
    montant = _gnf(r["montant"], "Le règlement")
    if montant <= 0:
        raise RegleMetier("Un règlement est positif.")
    paiement = None
    statut = StatutReglement.CONFIRME
    reference = r.get("reference_externe", "")
    if mode in (ModeReglement.VIREMENT, ModeReglement.CHEQUE):
        if not reference:
            raise RegleMetier("La référence du virement ou du chèque est obligatoire.")
        statut = StatutReglement.DECLARE
    if mode == ModeReglement.MOBILE_MONEY:
        from caef.paiements import services as paiements

        paiement = paiements.paiement_pour_vente(acteur, vente, montant, paiement=r.get("paiement"),
                                                 identifiant_transaction=r.get("identifiant_transaction", ""),
                                                 telephone=r.get("telephone", ""))
        statut = StatutReglement.CONFIRME if paiement.statut == "confirme" else StatutReglement.DECLARE
        reference = paiement.identifiant_transaction
    return Reglement.objects.create(vente=vente, mode=mode, montant=montant, reference_externe=reference,
                                    paiement=paiement, statut=statut, cree_par=acteur)


def annuler_vente(acteur, vente, motif):
    """RG-BOU-02 : contre-écriture liée, motivée, datée du jour de l'annulation ; remet les quantités
    en stock et neutralise les règlements ; le reçu d'origine reste consultable « Annulée »."""
    pdv = vente.point_de_vente
    verifier(acteur, "vente_annulation", "A", centre=pdv.centre_id)
    if vente.statut != StatutVente.VALIDEE or vente.vente_annulation_id:
        raise RegleMetier("Seule une vente validée s'annule.")
    if Vente.objects.filter(vente_annulation=vente).exists():
        raise RegleMetier("Cette vente est déjà annulée.")
    if not motif:
        raise RegleMetier("Le motif d'annulation est obligatoire.")
    quand = timezone.now()
    mois_origine = mois_de(vente.date_heure_vente)
    regularisation = mois_verrouille(pdv.centre_id, vente.date_heure_vente)
    with transaction.atomic():
        serie = "ANN"
        numero = prochain_numero(f"RECU:{pdv.pk}:{serie}")
        contre = Vente.objects.create(
            point_de_vente=pdv, serie_recu=serie, numero_recu=numero, date_heure_vente=quand, vendeur=acteur,
            session_caisse=_session_ouverte_ou_rien(pdv, timezone.localdate(quand)), total=-vente.total,
            statut=StatutVente.ANNULEE, motif_annulation=motif, vente_annulation=vente,
            mois_corrige=mois_origine if regularisation else "", emplacement=vente.emplacement, cree_par=acteur)
        for m in vente.mouvements.all():
            _mouvement(acteur, m.produit, "annulation", -m.quantite, motif=motif, emplacement=m.emplacement,
                       quand=quand, vente=contre, mouvement_annule=m)
        for r in vente.reglements.all():
            Reglement.objects.create(vente=contre, mode=r.mode, montant=-r.montant, reference_externe=r.reference_externe,
                                     paiement=r.paiement, statut=r.statut, cree_par=acteur)
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=vente, centre=pdv.centre_id,
                    avant={"statut": "validee"}, apres={"statut": "annulee", "contre_ecriture": str(contre.pk)},
                    motif=motif)
    return contre


def _session_ouverte_ou_rien(pdv, jour):
    s = session_du_jour(pdv, jour)
    return s if s and s.statut == StatutCaisse.OUVERTE else None


# --------------------------------------------------------------------------- caisse

def ouvrir_caisse(acteur, pdv, *, fond_de_caisse, jour=None):
    verifier(acteur, "caisse", "C", centre=pdv.centre_id)
    jour = jour or jour_reel()
    fond = _gnf(fond_de_caisse, "Le fond de caisse")
    if fond < 0:
        raise RegleMetier("Le fond de caisse ne peut être négatif.")
    verifier_mois_ouvert(pdv.centre_id, jour)
    if SessionCaisse.objects.filter(point_de_vente=pdv, date=jour).exists():
        raise RegleMetier("Une caisse est déjà ouverte ce jour-là.", code="caisse_deja_ouverte")
    with transaction.atomic():
        s = SessionCaisse.objects.create(point_de_vente=pdv, date=jour, ouverte_par=acteur, fond_de_caisse=fond,
                                         cree_par=acteur, **origine())
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=s, centre=pdv.centre_id, apres=instantane(s))
    return s


def montants_theoriques(session) -> dict:
    """Théorique par mode : fond de caisse en espèces plus les règlements de la journée (annulations comprises)."""
    totaux = {ModeReglement.ESPECES.value: Decimal(session.fond_de_caisse)}
    for mode, montant in (Reglement.objects.filter(vente__session_caisse=session)
                          .values_list("mode").annotate(t=Sum("montant"))):
        totaux[mode] = totaux.get(mode, Decimal(0)) + montant
    return {k: str(v) for k, v in totaux.items()}


def appareils_non_synchronises(pdv, jour) -> list:
    """OFF-08 : appareils du point de vente dont les ventes du jour ne sont pas toutes reçues."""
    from caef.synchronisation.models import Appareil, StatutAppareil

    fin = timezone.make_aware(datetime.combine(jour + timedelta(days=1), time.min))
    restants = []
    for a in Appareil.objects.filter(point_de_vente=pdv, statut=StatutAppareil.ACTIF):
        if a.plus_ancienne_operation_en_attente and a.plus_ancienne_operation_en_attente < fin:
            restants.append(a)
        elif a.derniere_synchronisation is None:
            restants.append(a)
    return restants


def compter_caisse(acteur, session, *, montants_comptes: dict, motif_ecart="", recus_papier_utilises=(),
                   derogation_appareils=False):
    """Ouverte → Comptée : montants comptés par mode ; motif si écart ; reçus papier du jour saisis ;
    ventes du jour de tous les appareils synchronisées (RG-BOU-13, OFF-08)."""
    pdv = session.point_de_vente
    verifier(acteur, "caisse", "C", centre=pdv.centre_id)
    exiger_statut(session, (StatutCaisse.OUVERTE,), "Compter la caisse")
    manquants = [n for n in recus_papier_utilises
                 if not Vente.objects.filter(point_de_vente=pdv, numero_recu_papier=n).exists()]
    if manquants:
        raise RegleMetier("Des reçus papier de secours ne sont pas saisis.", code="recus_papier_non_saisis",
                          details={"recus": manquants})
    retard = appareils_non_synchronises(pdv, session.date)
    if retard:
        raise RegleMetier("Des appareils du point de vente n'ont pas envoyé toutes les ventes du jour.",
                          code="appareils_non_synchronises", details={"appareils": [a.libelle for a in retard]})
    theorique = montants_theoriques(session)
    comptes = {m: str(_gnf(v, "Le montant compté")) for m, v in montants_comptes.items()}
    modes = set(theorique) | set(comptes)
    ecart = sum((Decimal(comptes.get(m, 0)) - Decimal(theorique.get(m, 0)) for m in modes), Decimal(0))
    if ecart != 0 and not motif_ecart:
        raise RegleMetier("Un écart non nul exige un motif.", code="ecart_sans_motif", details={"ecart": str(ecart)})
    with transaction.atomic():
        session.montants_theoriques = theorique
        session.montants_comptes = comptes
        session.ecart = ecart
        session.motif_ecart = motif_ecart
        session.compte_par = acteur
        session.compte_le = timezone.now()
        session.statut = StatutCaisse.COMPTEE
        enregistrer(session, acteur)
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=session, centre=pdv.centre_id,
                    avant={"statut": "ouverte"}, apres={"statut": "comptee", "ecart": str(ecart)}, motif=motif_ecart)
    return session


def a_saisi_des_ventes(utilisateur, session) -> bool:
    return Vente.objects.filter(point_de_vente=session.point_de_vente, vendeur=utilisateur,
                                date_heure_vente__date=session.date).exists() or \
        Vente.objects.filter(session_caisse=session, vendeur=utilisateur).exists()


def valider_caisse(acteur, session):
    """Comptée → Validée (écart nul) ou Validée avec écart (écart motivé), par le CPT, ou à défaut
    de CPT par le RC ou le RA ; jamais par quelqu'un qui a saisi des ventes ce jour-là (RG-BOU-06)."""
    pdv = session.point_de_vente
    decision = verifier(acteur, "caisse_validation", "V", centre=pdv.centre_id)
    exiger_statut(session, (StatutCaisse.COMPTEE,), "Valider la caisse")
    if a_saisi_des_ventes(acteur, session):
        raise SeparationDesTaches("Vous avez saisi des ventes ce jour-là : la validation revient à une autre "
                                  "personne (RG-BOU-06).", objet="caisse_validation", action="V",
                                  centre_id=pdv.centre_id, objet_type="session_caisse", objet_id=session.pk)
    statut = StatutCaisse.VALIDEE if session.ecart == 0 else StatutCaisse.VALIDEE_AVEC_ECART
    with transaction.atomic():
        session.statut = statut
        session.valide_par = acteur
        session.valide_le = timezone.now()
        enregistrer(session, acteur, ["statut", "valide_par", "valide_le"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=session, centre=pdv.centre_id,
                    avant={"statut": "comptee"}, apres={"statut": statut, "ecart": str(session.ecart)},
                    interim=decision.interim)
    return session


def renvoyer_caisse(acteur, session, motif):
    pdv = session.point_de_vente
    verifier(acteur, "caisse_validation", "V", centre=pdv.centre_id)
    exiger_statut(session, (StatutCaisse.COMPTEE,), "Renvoyer au recomptage")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        session.statut = StatutCaisse.OUVERTE
        session.motif_recomptage = motif
        enregistrer(session, acteur, ["statut", "motif_recomptage"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=session, centre=pdv.centre_id,
                    avant={"statut": "comptee"}, apres={"statut": "ouverte"}, motif=motif)
    return session


# --------------------------------------------------------------------------- inventaire

def ouvrir_inventaire(acteur, pdv):
    """Quantités théoriques figées à l'ouverture, par produit et emplacement ; ouvert par le RC ou le RA."""
    verifier(acteur, "inventaire_comptage", "C", centre=pdv.centre_id)
    if not roles_de(acteur, pdv.centre_id) & {"RC", "RA"}:
        raise AccesRefuse("L'inventaire est ouvert par le responsable de centre ou son adjoint.",
                          objet="inventaire_comptage", action="C", centre_id=pdv.centre_id)
    if Inventaire.objects.filter(point_de_vente=pdv).exclude(statut=StatutInventaire.VALIDE).exists():
        raise RegleMetier("Un inventaire est déjà en cours.")
    with transaction.atomic():
        inv = Inventaire.objects.create(point_de_vente=pdv, date_inventaire=aujourd_hui(), ouvert_par=acteur,
                                        cree_par=acteur)
        quantites = (MouvementStock.objects.filter(produit__point_de_vente=pdv)
                     .values("produit_id", "emplacement").annotate(q=Sum("quantite")))
        vus = set()
        for q in quantites:
            LigneInventaire.objects.create(inventaire=inv, produit_id=q["produit_id"], emplacement=q["emplacement"],
                                           quantite_theorique=q["q"])
            vus.add((q["produit_id"], q["emplacement"]))
        for p in Produit.objects.filter(point_de_vente=pdv, actif=True):
            if (p.pk, Emplacement.BOUTIQUE) not in vus:
                LigneInventaire.objects.create(inventaire=inv, produit=p, emplacement=Emplacement.BOUTIQUE,
                                               quantite_theorique=0)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=inv, centre=pdv.centre_id,
                    nb_lignes=inv.lignes.count())
    return inv


def terminer_comptage(acteur, inv, comptages: dict):
    """`comptages` : {ligne_id: {"quantite": q, "motif": "..."}} ; motif pour chaque écart."""
    pdv = inv.point_de_vente
    verifier(acteur, "inventaire_comptage", "C", centre=pdv.centre_id)
    exiger_statut(inv, (StatutInventaire.EN_COMPTAGE,), "Terminer le comptage")
    lignes = {str(l.pk): l for l in inv.lignes.all()}
    if set(map(str, comptages)) != set(lignes):
        raise RegleMetier("Chaque ligne doit avoir sa quantité comptée.")
    with transaction.atomic():
        for lid, c in comptages.items():
            l = lignes[str(lid)]
            l.quantite_comptee = Decimal(c["quantite"])
            l.ecart = l.quantite_comptee - l.quantite_theorique
            l.motif = c.get("motif", "")
            if l.ecart != 0 and not l.motif:
                raise RegleMetier(f"Motif obligatoire pour l'écart sur {l.produit.nom}.")
            l.save()
        inv.compte_par = acteur
        inv.statut = StatutInventaire.COMPTE
        enregistrer(inv, acteur, ["compte_par", "statut"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=inv, centre=pdv.centre_id,
                    avant={"statut": "en_comptage"}, apres={"statut": "compte"})
    return inv


def valider_inventaire(acteur, inv):
    """RG-BOU-07 : par le RC ou le RA (sans intérim), jamais par celui qui a compté ; chaque écart
    devient un mouvement « ajustement inventaire »."""
    pdv = inv.point_de_vente
    verifier(acteur, "inventaire_validation", "V", centre=pdv.centre_id)
    exiger_statut(inv, (StatutInventaire.COMPTE,), "Valider l'ajustement")
    if inv.compte_par_id == acteur.pk:
        raise SeparationDesTaches("La personne qui a compté ne valide pas l'ajustement (RG-BOU-07).",
                                  objet="inventaire_validation", action="V", centre_id=pdv.centre_id,
                                  objet_type="inventaire", objet_id=inv.pk)
    with transaction.atomic():
        n = 0
        for l in inv.lignes.select_related("produit"):
            if l.ecart:
                _mouvement(acteur, l.produit, "ajustement_inventaire", l.ecart, motif=l.motif or "Inventaire",
                           emplacement=l.emplacement, inventaire=inv)
                n += 1
        inv.valide_par = acteur
        inv.valide_le = timezone.now()
        inv.statut = StatutInventaire.VALIDE
        enregistrer(inv, acteur, ["valide_par", "valide_le", "statut"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=inv, centre=pdv.centre_id,
                    apres={"statut": "valide", "ajustements": n}, nb_lignes=n)
    return inv


def faire_recompter(acteur, inv, motif):
    pdv = inv.point_de_vente
    verifier(acteur, "inventaire_validation", "V", centre=pdv.centre_id)
    exiger_statut(inv, (StatutInventaire.COMPTE,), "Faire recompter")
    if not motif:
        raise RegleMetier("Le motif est obligatoire.")
    with transaction.atomic():
        inv.statut = StatutInventaire.EN_COMPTAGE
        inv.motif_recomptage = motif
        inv.compte_par = None
        enregistrer(inv, acteur, ["statut", "motif_recomptage", "compte_par"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=inv, centre=pdv.centre_id,
                    avant={"statut": "compte"}, apres={"statut": "en_comptage"}, motif=motif)
    return inv


# --------------------------------------------------------------------------- reversements

def _filtre_deposante(beneficiaire=None, groupement=""):
    if beneficiaire is not None:
        return Q(produit__beneficiaire_deposante=beneficiaire)
    return Q(produit__groupement=groupement, produit__beneficiaire_deposante__isnull=True)


def _part_centre(produit, jour) -> Decimal:
    depot = (Depot.objects.filter(produit=produit, date_depot__lte=jour).order_by("-date_depot", "-cree_le").first()
             or Depot.objects.filter(produit=produit).order_by("date_depot").first())
    return Decimal(depot.part_centre_pct) if depot else Decimal(0)


def montant_du(pdv, *, beneficiaire=None, groupement="", debut=None, fin=None) -> Decimal:
    """RG-BOU-08 : ventes validées non annulées des produits en dépôt-vente sur la période, moins la
    part du centre convenue au dépôt. Arrondi au franc près à la fin du calcul."""
    lignes = LigneVente.objects.filter(
        _filtre_deposante(beneficiaire, groupement), vente__point_de_vente=pdv, vente__statut=StatutVente.VALIDEE,
        vente__contre_ecriture__isnull=True, produit__origine=OrigineProduit.DEPOT_VENTE,
    ).select_related("vente", "produit")
    if debut:
        lignes = lignes.filter(vente__date_heure_vente__date__gte=debut)
    if fin:
        lignes = lignes.filter(vente__date_heure_vente__date__lte=fin)
    total = Decimal(0)
    for l in lignes:
        part = _part_centre(l.produit, timezone.localdate(l.vente.date_heure_vente))
        total += l.montant * (Decimal(100) - part) / Decimal(100)
    return total.quantize(Decimal(1), rounding=ROUND_HALF_UP)


def solde_restant_du(pdv, *, beneficiaire=None, groupement="", jusqua=None) -> Decimal:
    """Montants dus cumulés moins reversements payés."""
    du = montant_du(pdv, beneficiaire=beneficiaire, groupement=groupement, fin=jusqua)
    q = Q(beneficiaire=beneficiaire) if beneficiaire is not None else Q(groupement=groupement, beneficiaire__isnull=True)
    paye = Reversement.objects.filter(q, point_de_vente=pdv, statut=StatutReversement.PAYE).aggregate(
        t=Sum("montant_reverse"))["t"] or Decimal(0)
    return du - paye


def preparer_reversement(acteur, pdv, *, periode_debut, periode_fin, montant_reverse, beneficiaire=None,
                         groupement=""):
    """Par le comptable ; montant reversé au plus égal au solde restant dû, déduction faite des
    reversements préparés ou validés non encore payés."""
    verifier(acteur, "reversement_preparation", "C", centre=pdv.centre_id)
    if (beneficiaire is None) == (not groupement):
        raise RegleMetier("Indiquez une productrice déposante ou un groupement.")
    montant = _gnf(montant_reverse, "Le montant reversé")
    if montant <= 0:
        raise RegleMetier("Le montant reversé doit être positif.")
    du_periode = montant_du(pdv, beneficiaire=beneficiaire, groupement=groupement, debut=periode_debut,
                            fin=periode_fin)
    solde = solde_restant_du(pdv, beneficiaire=beneficiaire, groupement=groupement, jusqua=periode_fin)
    q = Q(beneficiaire=beneficiaire) if beneficiaire is not None else Q(groupement=groupement, beneficiaire__isnull=True)
    engage = Reversement.objects.filter(q, point_de_vente=pdv).exclude(statut=StatutReversement.PAYE).aggregate(
        t=Sum("montant_reverse"))["t"] or Decimal(0)
    if montant > solde - engage:
        raise RegleMetier("Le montant reversé dépasse le solde restant dû.", code="reversement_superieur_au_solde",
                          details={"solde_restant_du": str(solde - engage)})
    with transaction.atomic():
        r = Reversement.objects.create(point_de_vente=pdv, beneficiaire=beneficiaire, groupement=groupement,
                                       periode_debut=periode_debut, periode_fin=periode_fin, montant_du=du_periode,
                                       montant_reverse=montant, prepare_par=acteur, cree_par=acteur)
        journaliser(ActionJournal.CREATION, utilisateur=acteur, objet=r, centre=pdv.centre_id, apres=instantane(r))
        notifier_role(pdv.centre_id, ("RC", "RA"), "reversement_a_valider", "Reversement préparé : à valider.", r)
    return r


def valider_reversement(acteur, r):
    pdv = r.point_de_vente
    decision = verifier(acteur, "reversement_validation", "V", centre=pdv.centre_id)
    exiger_statut(r, (StatutReversement.PREPARE,), "Valider")
    if r.prepare_par_id == acteur.pk:
        raise SeparationDesTaches("La personne qui a préparé le reversement ne le valide pas (RG-BOU-09).",
                                  objet="reversement_validation", action="V", centre_id=pdv.centre_id,
                                  objet_type="reversement", objet_id=r.pk)
    with transaction.atomic():
        r.statut = StatutReversement.VALIDE
        r.valide_par = acteur
        r.valide_le = timezone.now()
        enregistrer(r, acteur, ["statut", "valide_par", "valide_le"])
        journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet=r, centre=pdv.centre_id,
                    avant={"statut": "prepare"}, apres={"statut": "valide"}, interim=decision.interim)
    return r


def payer_reversement(acteur, r, *, date_paiement, mode, piece_justificative):
    """Validé → Payé, par le comptable : date, mode et pièce ; auteur différent du valideur."""
    pdv = r.point_de_vente
    verifier(acteur, "reversement_validation", "M", centre=pdv.centre_id)
    exiger_statut(r, (StatutReversement.VALIDE,), "Marquer payé")
    if r.valide_par_id == acteur.pk:
        raise SeparationDesTaches("La personne qui a validé le reversement ne le marque pas payé (RG-BOU-09).",
                                  objet="reversement_validation", action="M", centre_id=pdv.centre_id,
                                  objet_type="reversement", objet_id=r.pk)
    if not (date_paiement and mode and piece_justificative):
        raise RegleMetier("Date, mode et pièce justificative sont obligatoires.")
    if piece_justificative.objet_type != "reversement" or piece_justificative.objet_id != r.pk:
        raise RegleMetier("La pièce doit être déposée sur ce reversement.")
    verifier_mois_ouvert(pdv.centre_id, date_paiement)
    with transaction.atomic():
        r.statut = StatutReversement.PAYE
        r.date_paiement = date_paiement
        r.mode = mode
        r.piece_justificative = piece_justificative
        r.paye_par = acteur
        enregistrer(r, acteur, ["statut", "date_paiement", "mode", "piece_justificative", "paye_par"])
        journaliser(ActionJournal.STATUT, utilisateur=acteur, objet=r, centre=pdv.centre_id,
                    avant={"statut": "valide"}, apres={"statut": "paye", "date_paiement": date_paiement})
    return r


# --------------------------------------------------------------------------- tableau de bord

def volet_boutique(pdv, debut, fin) -> dict:
    """E-BOU-08 : chiffre d'affaires (ventes moins annulations), nombre de ventes, stock valorisé,
    ruptures et stocks sous seuil, écarts de caisse, reversements dus."""
    ventes = Vente.objects.filter(point_de_vente=pdv, date_heure_vente__date__gte=debut,
                                  date_heure_vente__date__lte=fin)
    ca = ventes.filter(statut__in=[StatutVente.VALIDEE, StatutVente.ANNULEE]).aggregate(t=Sum("total"))["t"]
    produits = []
    valorise = Decimal(0)
    for p in Produit.objects.filter(point_de_vente=pdv, actif=True):
        s = stock(p)
        prix = prix_en_vigueur(p)
        if prix and s > 0:
            valorise += s * prix.prix
        if s <= 0 or (p.seuil_alerte is not None and s < p.seuil_alerte):
            produits.append({"produit": p.nom, "stock": str(s), "seuil": str(p.seuil_alerte)
                             if p.seuil_alerte is not None else None})
    ecarts = SessionCaisse.objects.filter(point_de_vente=pdv, date__gte=debut, date__lte=fin).exclude(
        ecart=0).exclude(ecart__isnull=True).values("date", "ecart", "motif_ecart", "statut")
    return {
        "chiffre_affaires": str(ca) if ca is not None else "0",
        "nombre_ventes": ventes.filter(statut=StatutVente.VALIDEE, contre_ecriture__isnull=True).count(),
        "nombre_annulations": ventes.filter(statut=StatutVente.ANNULEE, vente_annulation__isnull=False).count(),
        "stock_valorise": str(valorise),
        "alertes_stock": produits,
        "ecarts_caisse": [{**e, "date": e["date"].isoformat(), "ecart": str(e["ecart"])} for e in ecarts],
    }
