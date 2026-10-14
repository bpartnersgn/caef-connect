"""Moteur de synchronisation : l'appareil propose, le serveur décide (DAT § 4.5, OFF-01 à OFF-08).

Envoi : chaque opération immuable (UUID de l'appareil) est rejouée par les mêmes services métier
qu'une saisie en ligne (droits, périmètre, règles, journal), dans sa propre transaction ; une
opération déjà reçue est ignorée et renvoie sa réponse d'origine.

Réception : changements du centre depuis le curseur de l'appareil, filtrés par droits et
périmètre ; un objet devenu illisible est signalé « à effacer ». Aucun champ restreint (R)
n'est envoyé à un appareil.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from django.apps import apps
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from caef.commun import contexte as ctx_mod
from caef.commun.exceptions import AccesRefuse, ErreurMetier, Introuvable, MoisVerrouille, RegleMetier
from caef.commun.services import parametre
from caef.habilitations.services import decider
from caef.journal.models import ActionJournal
from caef.journal.services import journaliser, journaliser_refus
from caef.notifications.services import notifier

from .models import (
    ConflitSynchronisation,
    JournalChangements,
    NatureChangement,
    OperationSynchronisation,
    ResultatOperation,
)
from .services import roles_hors_ligne


def _obj(chemin, pk):
    modele = apps.get_model(chemin)
    try:
        return modele._default_manager.get(pk=pk)
    except (modele.DoesNotExist, ValueError, TypeError):
        raise Introuvable(f"{modele._meta.verbose_name} introuvable.")


def _date(v):
    return parse_date(v) if isinstance(v, str) else v


# --------------------------------------------------------------------------- opérations prises en charge

def op_candidature_creer(u, d, op):
    from caef.beneficiaires.services import creer_candidature

    identite = None
    if d.get("identite"):
        identite = dict(d["identite"])
        for cle in ("date_naissance", "consentement_date"):
            if identite.get(cle):
                identite[cle] = _date(identite[cle])
        for cle, chemin in (("zone_residence", "referentiels.ZoneTerritoriale"),
                            ("niveau_etudes", "referentiels.ReferentielValeur"),
                            ("situation_entree", "referentiels.ReferentielValeur")):
            if identite.get(cle):
                identite[cle] = _obj(chemin, identite[cle])
        restreints = {"contact_urgence_nom", "contact_urgence_tel", "piece_identite_type", "piece_identite_numero"}
        if restreints & set(identite):
            raise RegleMetier("Les champs restreints ne se saisissent pas hors ligne (OFF-06).")
    cand = creer_candidature(
        u, centre=_obj("referentiels.Centre", d["centre"]), formation=_obj("formations.Formation", d["formation"]),
        date_reception=_date(d.get("date_reception")), identite=identite,
        dossier_existant=_obj("beneficiaires.Beneficiaire", d["beneficiaire"]) if d.get("beneficiaire") else None,
        decision_doublon=d.get("decision_doublon"), commentaire_doublon=d.get("commentaire_doublon", ""))
    return {"candidature": str(cand.pk), "code": cand.code, "beneficiaire": str(cand.beneficiaire_id),
            "code_beneficiaire": cand.beneficiaire.code, "doublon_probable": cand.doublon_probable}


CHAMPS_COORDONNEES = ("telephone", "zone_residence")


def op_beneficiaire_coordonnees(u, d, op):
    """Fusion champ par champ depuis la version de base ; un même champ modifié des deux côtés garde
    la valeur du serveur et crée un conflit (RG-OFF-05)."""
    from caef.beneficiaires.services import modifier_beneficiaire

    b = _obj("beneficiaires.Beneficiaire", d["beneficiaire"])
    base, champs = d.get("base", {}), d.get("champs", {})
    if set(champs) - set(CHAMPS_COORDONNEES):
        raise RegleMetier("Hors ligne, seules les coordonnées se mettent à jour.")
    a_appliquer, conflits = {}, []
    for champ, valeur in champs.items():
        actuel = getattr(b, b._meta.get_field(champ).attname)
        actuel = str(actuel) if actuel not in (None, "") else None
        if champ in base and (base[champ] or None) != actuel and (valeur or None) != actuel:
            conflits.append((champ, actuel, valeur))
        elif champ == "zone_residence":
            a_appliquer[champ] = _obj("referentiels.ZoneTerritoriale", valeur)
        else:
            a_appliquer[champ] = valeur
    if a_appliquer:
        modifier_beneficiaire(u, b, **a_appliquer)
    for champ, serveur, appareil in conflits:
        ConflitSynchronisation.objects.create(operation=op, centre_id=b.centre_rattachement_id, objet_type="beneficiaire",
                                              objet_id=b.pk, champ=champ, valeur_serveur=serveur or "",
                                              valeur_appareil=appareil or "")
    return {"conflits": [c[0] for c in conflits]}


def op_presences_saisir(u, d, op):
    """Une présence par séance et inscription ; la plus récente selon l'horodatage de l'appareil est
    retenue, le formateur est averti si les valeurs diffèrent (RG-OFF-05)."""
    from caef.formations.models import Presence
    from caef.formations.services import saisir_presences

    seance = _obj("formations.Seance", d["seance"])
    etats = dict(d["etats"])
    ecartees = []
    for ins_id, etat in list(etats.items()):
        p = Presence.objects.filter(seance=seance, inscription_id=ins_id).first()
        if p is not None and p.saisi_le and p.saisi_le > op.horodatage_appareil:
            del etats[ins_id]
            if p.etat != etat:
                ecartees.append(ins_id)
    saisir_presences(u, seance, etats, motif_tardif=d.get("motif_tardif", ""), valider=d.get("valider", True))
    if ecartees:
        notifier([u], "presence_ecartee", "Des présences saisies sur un autre appareil plus récemment ont été gardées.",
                 seance)
    return {"ecartees": ecartees}


def op_evaluation_saisir(u, d, op):
    from caef.formations.services import saisir_evaluation

    ev = saisir_evaluation(u, _obj("formations.Inscription", d["inscription"]), intitule=d["intitule"],
                           date=_date(d["date"]), type_resultat=d["type_resultat"], note=d.get("note"),
                           note_max=d.get("note_max"), appreciation=d.get("appreciation", ""))
    return {"evaluation": str(ev.pk)}


def op_vente_creer(u, d, op):
    from caef.boutique.services import vendre

    pdv = _obj("boutique.PointDeVente", d["point_de_vente"])
    lignes = [{**l, "produit": _obj("boutique.Produit", l["produit"])} for l in d["lignes"]]
    reglements = [{**r, "paiement": _obj("paiements.Paiement", r["paiement"]) if r.get("paiement") else None}
                  for r in d["reglements"]]
    v = vendre(u, pdv, lignes=lignes, reglements=reglements, numero_recu=d.get("numero_recu"),
               numero_recu_papier=d.get("numero_recu_papier"),
               date_heure_vente=parse_datetime(d["date_heure_vente"]) if d.get("date_heure_vente") else None,
               emplacement=d.get("emplacement", "boutique"))
    return {"vente": str(v.pk), "recu": v.numero_complet, "total": str(v.total)}


def op_stock_entree(u, d, op):
    from caef.boutique.services import entrer_en_stock

    m = entrer_en_stock(u, _obj("boutique.Produit", d["produit"]), type=d["type"], quantite=d["quantite"],
                        emplacement=d.get("emplacement", "boutique"), part_centre_pct=d.get("part_centre_pct"),
                        motif=d.get("motif", ""))
    return {"mouvement": str(m.pk)}


def op_stock_sortie(u, d, op):
    from caef.boutique.services import sortir_du_stock

    m = sortir_du_stock(u, _obj("boutique.Produit", d["produit"]), type=d["type"], quantite=d["quantite"],
                        motif=d.get("motif", ""), emplacement=d.get("emplacement", "boutique"))
    return {"mouvement": str(m.pk)}


def op_caisse_ouvrir(u, d, op):
    from caef.boutique.services import ouvrir_caisse

    s = ouvrir_caisse(u, _obj("boutique.PointDeVente", d["point_de_vente"]), fond_de_caisse=d["fond_de_caisse"],
                      jour=_date(d.get("date")))
    return {"session_caisse": str(s.pk)}


def op_caisse_compter(u, d, op):
    from caef.boutique.services import compter_caisse

    s = compter_caisse(u, _obj("boutique.SessionCaisse", d["session_caisse"]), montants_comptes=d["montants_comptes"],
                       motif_ecart=d.get("motif_ecart", ""), recus_papier_utilises=d.get("recus_papier_utilises", ()))
    return {"statut": s.statut, "ecart": str(s.ecart)}


def op_inventaire_compter(u, d, op):
    from caef.boutique.services import terminer_comptage

    inv = terminer_comptage(u, _obj("boutique.Inventaire", d["inventaire"]), d["comptages"])
    return {"statut": inv.statut}


def op_paiement_especes(u, d, op):
    from caef.facturation.models import Echeance
    from caef.paiements.services import encaisser_especes

    p = encaisser_especes(u, _obj("referentiels.Centre", d["centre"]), montant=d["montant"],
                          echeances=list(Echeance.objects.filter(pk__in=d.get("echeances", []))),
                          repartition=d.get("repartition"), numero_recu=d.get("numero_recu"))
    return {"paiement": str(p.pk), "recu": f"{p.serie_recu}-{p.numero_recu:06d}"}


def op_paiement_declarer(u, d, op):
    from caef.facturation.models import Echeance
    from caef.paiements.services import declarer_mobile_money

    p = declarer_mobile_money(u, _obj("referentiels.Centre", d["centre"]),
                              identifiant_transaction=d["identifiant_transaction"],
                              montant_declare=d["montant_declare"],
                              echeances=list(Echeance.objects.filter(pk__in=d.get("echeances", []))),
                              telephone=d.get("telephone", ""), numero_recu=d.get("numero_recu"))
    return {"paiement": str(p.pk), "statut": p.statut}


OPERATIONS = {
    "candidature.creer": op_candidature_creer,
    "beneficiaire.coordonnees": op_beneficiaire_coordonnees,
    "presences.saisir": op_presences_saisir,
    "evaluation.saisir": op_evaluation_saisir,
    "vente.creer": op_vente_creer,
    "stock.entree": op_stock_entree,
    "stock.sortie": op_stock_sortie,
    "caisse.ouvrir": op_caisse_ouvrir,
    "caisse.compter": op_caisse_compter,
    "inventaire.compter": op_inventaire_compter,
    "paiement.especes": op_paiement_especes,
    "paiement.declarer": op_paiement_declarer,
}


# --------------------------------------------------------------------------- envoi

def appliquer_lot(utilisateur, appareil, operations: list[dict], *, horloge_appareil=None,
                  plus_ancienne_en_attente=None) -> dict:
    """Applique un lot ordonné ; renvoie un résultat par opération."""
    if not roles_hors_ligne(utilisateur, appareil.centre_id):
        raise AccesRefuse("Votre rôle travaille en ligne seulement (RG-OFF-08).", objet="appareil", action="C",
                          centre_id=appareil.centre_id)
    maintenant = timezone.now()
    ecart = None
    if horloge_appareil:
        h = parse_datetime(horloge_appareil) if isinstance(horloge_appareil, str) else horloge_appareil
        ecart = int((h - maintenant).total_seconds())
    horloge_a_verifier = ecart is not None and abs(ecart) > parametre("ECART_HORLOGE_SECONDES")
    resultats = [appliquer(utilisateur, appareil, o, horloge_a_verifier) for o in operations]
    appareil.derniere_synchronisation = maintenant
    appareil.ecart_horloge_secondes = ecart
    appareil.plus_ancienne_operation_en_attente = (
        parse_datetime(plus_ancienne_en_attente) if isinstance(plus_ancienne_en_attente, str)
        else plus_ancienne_en_attente)
    appareil.save(update_fields=["derniere_synchronisation", "ecart_horloge_secondes",
                                 "plus_ancienne_operation_en_attente"])
    return {"resultats": resultats, "horloge_a_verifier": horloge_a_verifier, "heure_serveur": maintenant.isoformat()}


def appliquer(utilisateur, appareil, o: dict, horloge_a_verifier=False) -> dict:
    try:
        op_id = uuid.UUID(str(o["id"]))
    except (KeyError, ValueError):
        return {"id": o.get("id"), "resultat": ResultatOperation.REJETEE, "motif": "Identifiant d'opération invalide."}
    deja = OperationSynchronisation.objects.filter(pk=op_id).first()
    if deja is not None:
        return _resultat(deja, rejouee=True)
    type_operation = o.get("type", "")
    horodatage = parse_datetime(o.get("horodatage", "")) if o.get("horodatage") else None
    if horodatage is None:
        return {"id": str(op_id), "resultat": ResultatOperation.REJETEE, "motif": "Horodatage de l'appareil manquant."}
    op = OperationSynchronisation(id=op_id, appareil=appareil, utilisateur=utilisateur, type_operation=type_operation,
                                  objet_type=type_operation.split(".")[0], donnees=o.get("donnees") or {},
                                  version_base=o.get("version_base"), horodatage_appareil=horodatage,
                                  horloge_a_verifier=horloge_a_verifier)
    gestionnaire = OPERATIONS.get(type_operation)
    jeton = ctx_mod.definir(ctx_mod.Contexte(
        adresse_ip=ctx_mod.contexte().adresse_ip, appareil_id=str(appareil.pk), horodatage_appareil=horodatage,
        hors_ligne=True))
    erreur_refus = None
    try:
        if gestionnaire is None:
            raise RegleMetier("Opération non disponible hors ligne.", code="operation_inconnue")
        with transaction.atomic():
            op.resultat = ResultatOperation.APPLIQUEE
            op.save(force_insert=True)
            reponse = gestionnaire(utilisateur, op.donnees, op)
            if op.conflits.exists():
                op.resultat = ResultatOperation.EN_CONFLIT
            op.reponse = _json(reponse)
            op.save(update_fields=["resultat", "reponse"])
    except IntegrityError:
        if OperationSynchronisation.objects.filter(pk=op_id).exists():  # reçue en parallèle
            return _resultat(OperationSynchronisation.objects.get(pk=op_id), rejouee=True)
        _enregistrer_echec(op, ResultatOperation.REJETEE, "Donnée en double ou incohérente.")
    except MoisVerrouille as e:
        _enregistrer_echec(op, ResultatOperation.ECRITURE_TARDIVE, e.message)
        ConflitSynchronisation.objects.create(operation=op, centre_id=appareil.centre_id, objet_type=op.objet_type)
    except AccesRefuse as e:
        erreur_refus = e
        _enregistrer_echec(op, ResultatOperation.REJETEE, e.message)
    except ErreurMetier as e:
        _enregistrer_echec(op, ResultatOperation.REJETEE, e.message, details=e.details)
    finally:
        ctx_mod.restaurer(jeton)
    if erreur_refus is not None:
        journaliser_refus(utilisateur, erreur_refus)
    return _resultat(op)


def _enregistrer_echec(op, resultat, motif, details=None):
    op.resultat = resultat
    op.motif_rejet = motif
    op.reponse = _json(details) if details else None
    op.save(force_insert=True)


def _resultat(op, rejouee=False):
    r = {"id": str(op.pk), "resultat": op.resultat, "motif": op.motif_rejet, "reponse": op.reponse,
         "horloge_a_verifier": op.horloge_a_verifier}
    if rejouee:
        r["deja_recue"] = True
    return r


def _json(v):
    if isinstance(v, dict):
        return {k: _json(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_json(x) for x in v]
    if isinstance(v, (uuid.UUID, Decimal, datetime)):
        return str(v)
    return v


def rejouer_en_regularisation(acteur, op, motif):
    """L'opération est rejouée datée d'aujourd'hui, référencée au mois corrigé (RG-SRC-03), par le même
    service et avec les droits de son auteur ; la série web remplace la série de l'appareil."""
    from caef.pilotage.verrou import mois_de

    gestionnaire = OPERATIONS[op.type_operation]
    jeton = ctx_mod.definir(ctx_mod.Contexte(hors_ligne=False, supplements={
        "mois_corrige": mois_de(op.horodatage_appareil)}))
    try:
        donnees = dict(op.donnees)
        donnees.pop("numero_recu", None)
        reponse = gestionnaire(op.utilisateur, donnees, op)
    finally:
        ctx_mod.restaurer(jeton)
    journaliser(ActionJournal.VALIDATION, utilisateur=acteur, objet_type="operation_synchronisation", objet_id=op.pk,
                centre=op.appareil.centre_id, apres={"regularisation": _json(reponse)}, motif=motif)
    return reponse


# --------------------------------------------------------------------------- réception

def _ser_beneficiaire(b, u):
    """Champs utiles au rôle ; jamais de champ restreint (OFF-06) ; le formateur ne voit que nom,
    prénom et code (RG-FOR-04)."""
    if not decider(u, "beneficiaire", "M", centre=b.centre_rattachement_id, nominatif=True).autorise:
        return {"id": str(b.pk), "code": b.code, "nom": b.nom, "prenoms": b.prenoms}
    return {"id": str(b.pk), "code": b.code, "nom": b.nom, "prenoms": b.prenoms, "annee_naissance": b.annee,
            "sexe": b.sexe, "telephone": b.telephone, "zone_residence": str(b.zone_residence_id),
            "statut": b.statut, "completude": b.completude, "version": b.version}


def _champs(*noms):
    def ser(o, u):
        r = {"id": str(o.pk)}
        for n in noms:
            v = getattr(o, n)
            r[n] = str(v.pk) if hasattr(v, "pk") else (str(v) if isinstance(v, (uuid.UUID, Decimal)) else
                                                       (v.isoformat() if hasattr(v, "isoformat") else v))
        return r
    return ser


def _ser_produit(p, u):
    from caef.boutique.models import stock
    from caef.boutique.services import prix_en_vigueur

    prix = prix_en_vigueur(p)
    return {"id": str(p.pk), "code": p.code, "nom": p.nom, "origine": p.origine, "actif": p.actif,
            "prix": str(prix.prix) if prix else None, "stock": str(stock(p)),
            "deposante": ({"code": p.beneficiaire_deposante.code, "nom": f"{p.beneficiaire_deposante.prenoms} "
                           f"{p.beneficiaire_deposante.nom}"} if p.beneficiaire_deposante_id else p.groupement or None)}


# table → (objet de la Matrice, chemin vers le centre, nominatif, chemin vers la session, sérialiseur)
SYNCHRONISES = {
    "beneficiaire": ("beneficiaire", "centre_rattachement_id", True, None, _ser_beneficiaire),
    "candidature": ("candidature", "centre_id", True, None,
                    _champs("code", "beneficiaire", "formation", "statut", "doublon_probable")),
    "session_formation": ("session", "centre_id", False, "", _champs("code", "formation", "date_debut", "date_fin",
                                                                       "lieu", "capacite", "statut")),
    "seance": ("session", "session.centre_id", False, "session",
               _champs("session", "date", "heure_debut", "heure_fin", "formateur", "theme", "presences_validees")),
    "inscription": ("inscription", "session.centre_id", True, "session",
                    _champs("beneficiaire", "session", "statut_participation", "cheffe_de_classe", "taux_presence")),
    "presence": ("presence", "seance.session.centre_id", True, "seance.session",
                 _champs("seance", "inscription", "etat", "saisi_le")),
    "produit": ("produit", "point_de_vente.centre_id", False, None, _ser_produit),
    "session_caisse": ("caisse", "point_de_vente.centre_id", False, None,
                       _champs("date", "statut", "fond_de_caisse")),
    "echeance": ("echeance", "centre_id", True, None,
                 _champs("beneficiaire", "service_payant", "montant", "date_limite", "reference_paiement",
                         "restant_du", "statut")),
}


def _chemin(o, chemin):
    for morceau in chemin.split("."):
        o = getattr(o, morceau)
    return o


def changements(utilisateur, appareil, curseur: int, limite: int = 500) -> dict:
    entrees = list(JournalChangements.objects.filter(centre_id=appareil.centre_id, numero__gt=curseur)
                   .order_by("numero")[:limite])
    vus = {}
    for e in entrees:
        vus[(e.objet_type, e.objet_id)] = e
    sortie = []
    for (objet_type, objet_id), e in vus.items():
        conf = SYNCHRONISES.get(objet_type)
        if conf is None:
            continue
        objet_matrice, chemin_centre, nominatif, chemin_session, ser = conf
        modele = next(m for m in apps.get_models() if m._meta.db_table == objet_type)
        o = modele._default_manager.filter(pk=objet_id).first()
        if o is None or getattr(o, "archive", False) or e.nature == NatureChangement.ARCHIVAGE:
            sortie.append({"objet_type": objet_type, "id": str(objet_id), "action": "effacer"})
            continue
        session = _chemin(o, chemin_session) if chemin_session else (o if chemin_session == "" else None)
        d = decider(utilisateur, objet_matrice, "L", centre=_chemin(o, chemin_centre), nominatif=nominatif,
                    session=session)
        if not d.autorise or d.agrege_seulement:
            sortie.append({"objet_type": objet_type, "id": str(objet_id), "action": "effacer"})
            continue
        sortie.append({"objet_type": objet_type, "id": str(objet_id), "action": "ecrire", "donnees": ser(o, utilisateur)})
    nouveau = entrees[-1].numero if entrees else curseur
    return {"curseur": nouveau, "changements": sortie, "suite": len(entrees) == limite}
