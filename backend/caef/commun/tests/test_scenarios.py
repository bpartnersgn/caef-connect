"""Scénarios transverses des règles non négociables (brief) et du plan de tests (doc 08)."""

import uuid

import pytest
from django.utils import timezone

from caef.commun.exceptions import AccesRefuse, MoisVerrouille, RegleMetier, SeparationDesTaches
from caef.commun.tests.outils import boutique, dossier_complet, session_ouverte, verrouiller_mois
from caef.journal.models import JournalAudit

# --------------------------------------------------------------------------- séparation des tâches

def test_la_saisie_d_une_candidature_ne_se_valide_pas_par_son_auteur(monde):
    """Une personne qui cumule la saisie (AA) et la validation (RC) ne valide pas sa propre saisie."""
    from datetime import timedelta

    from caef.beneficiaires import services as ben
    from caef.habilitations.models import Affectation
    from caef.habilitations.services import invalider_cache

    formation, _, _ = session_ouverte(monde)
    rc = monde["u"]["rc.cmr"]
    Affectation.objects.create(utilisateur=rc, role_id="AA", centre=monde["cmr"], motif="Cumul fictif",
                               date_debut=timezone.localdate() - timedelta(days=1))
    invalider_cache(rc)
    cand = ben.creer_candidature(rc, centre=monde["cmr"], formation=formation,
                                 identite=dossier_complet(zone=monde["zone"]))
    ben.soumettre_candidature(rc, cand)
    with pytest.raises(SeparationDesTaches):
        ben.valider_candidature(rc, cand)


def test_validation_d_une_candidature_journalisee_dans_la_meme_transaction(monde):
    from caef.beneficiaires import services as ben

    formation, _, _ = session_ouverte(monde)
    aa, rc = monde["u"]["aa.cmr"], monde["u"]["rc.cmr"]
    cand = ben.creer_candidature(aa, centre=monde["cmr"], formation=formation,
                                 identite=dossier_complet(zone=monde["zone"]))
    ben.soumettre_candidature(aa, cand)
    ben.valider_candidature(rc, cand)
    assert JournalAudit.objects.filter(objet_id=cand.pk, utilisateur=rc).exists()


def test_le_journal_est_en_ajout_seul(monde):
    from django.db import DatabaseError, transaction

    session_ouverte(monde)
    entree = JournalAudit.objects.first()
    with pytest.raises(DatabaseError), transaction.atomic():
        JournalAudit.objects.filter(pk=entree.pk).update(motif="altéré")


# --------------------------------------------------------------------------- périmètre

def test_un_autre_centre_est_refuse_et_le_refus_journalise(monde):
    from caef.beneficiaires import services as ben

    formation, _, _ = session_ouverte(monde)
    with pytest.raises(AccesRefuse):
        ben.creer_candidature(monde["u"]["aa.tsb"], centre=monde["cmr"], formation=formation,
                              identite=dossier_complet(zone=monde["zone"]))


def test_refus_hors_perimetre_par_l_api(monde_connectable, connecter):
    from caef.beneficiaires import services as ben

    m = monde_connectable
    formation, _, _ = session_ouverte(m)
    cand = ben.creer_candidature(m["u"]["aa.cmr"], centre=m["cmr"], formation=formation,
                                 identite=dossier_complet(zone=m["zone"]))
    avant = JournalAudit.objects.filter(action="acces_refuse").count()
    r = connecter("aa.tsb").get(f"/api/v1/beneficiaires/{cand.beneficiaire_id}/")
    assert r.status_code == 403
    assert JournalAudit.objects.filter(action="acces_refuse").count() == avant + 1
    assert connecter("aa.tsb").get("/api/v1/beneficiaires/").json()["count"] == 0


def test_le_formateur_ne_voit_que_nom_prenom_et_code(monde_connectable, connecter):
    from caef.beneficiaires import services as ben
    from caef.formations import services as form

    m = monde_connectable
    formation, session, _ = session_ouverte(m)
    cand = ben.creer_candidature(m["u"]["aa.cmr"], centre=m["cmr"], formation=formation,
                                 identite=dossier_complet(zone=m["zone"]))
    ben.soumettre_candidature(m["u"]["aa.cmr"], cand)
    ben.valider_candidature(m["u"]["rc.cmr"], cand)
    form.inscrire(m["u"]["rp.cmr"], cand, session)
    lignes = connecter("fo.cmr").get("/api/v1/beneficiaires/").json()["results"]
    assert len(lignes) == 1 and set(lignes[0]) == {"id", "code", "nom", "prenoms"}


def test_le_jeton_d_appareil_ne_sert_qu_a_la_synchronisation(monde):
    from rest_framework.test import APIClient

    from caef.synchronisation import services as sync

    appareil = sync.enroler(monde["u"]["rc.cmr"], centre=monde["cmr"], libelle="Tablette fictive")
    jeton = sync.delivrer_jeton(monde["u"]["aa.cmr"], appareil)["jeton"]
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Appareil {jeton}")
    assert c.get("/api/v1/beneficiaires/").status_code == 403
    assert c.get("/api/v1/synchronisation/changements/").status_code == 200


# --------------------------------------------------------------------------- boutique et mois verrouillé

def test_le_prix_et_le_total_viennent_du_serveur(monde):
    from caef.boutique import services as bou

    pdv, produit = boutique(monde, prix=10000)
    vb = monde["u"]["vb.cmr"]
    bou.ouvrir_caisse(vb, pdv, fond_de_caisse=0)
    with pytest.raises(RegleMetier):
        bou.vendre(vb, pdv, lignes=[{"produit": produit, "quantite": 2, "prix": 1}],
                   reglements=[{"mode": "especes", "montant": 2}])
    v = bou.vendre(vb, pdv, lignes=[{"produit": produit, "quantite": 2}],
                   reglements=[{"mode": "especes", "montant": 20000}])
    assert v.total == 20000


def test_un_mois_valide_est_verrouille(monde):
    from caef.boutique import services as bou

    pdv, produit = boutique(monde)
    vb = monde["u"]["vb.cmr"]
    bou.ouvrir_caisse(vb, pdv, fond_de_caisse=0)
    verrouiller_mois(monde)
    with pytest.raises(MoisVerrouille):
        bou.vendre(vb, pdv, lignes=[{"produit": produit, "quantite": 1}],
                   reglements=[{"mode": "especes", "montant": 10000}])


def test_une_vente_validee_ne_s_annule_que_par_contre_ecriture(monde):
    from caef.boutique import services as bou

    pdv, produit = boutique(monde)
    vb, cpt = monde["u"]["vb.cmr"], monde["u"]["cpt.cmr"]
    bou.ouvrir_caisse(vb, pdv, fond_de_caisse=0)
    v = bou.vendre(vb, pdv, lignes=[{"produit": produit, "quantite": 1}],
                   reglements=[{"mode": "especes", "montant": 10000}])
    with pytest.raises(AccesRefuse):
        bou.annuler_vente(vb, v, "Erreur fictive")
    contre = bou.annuler_vente(cpt, v, "Erreur fictive")
    assert contre.total == -v.total and contre.serie_recu == "ANN"


# --------------------------------------------------------------------------- hors ligne

def _appareil(monde):
    from caef.synchronisation import services as sync

    return sync.enroler(monde["u"]["rc.cmr"], centre=monde["cmr"], libelle="Tablette fictive")


def _op_candidature(monde, formation, op_id=None):
    return {"id": str(op_id or uuid.uuid4()), "type": "candidature.creer",
            "horodatage": timezone.now().isoformat(),
            "donnees": {"centre": str(monde["cmr"].pk), "formation": str(formation.pk),
                        "identite": {**dossier_complet(zone=None), "zone_residence": str(monde["zone"].pk),
                                     "consentement_date": timezone.localdate().isoformat()}}}


def test_une_operation_recue_deux_fois_n_est_appliquee_qu_une_fois(monde):
    from caef.beneficiaires.models import Candidature
    from caef.synchronisation.moteur import appliquer_lot

    formation, _, _ = session_ouverte(monde)
    appareil = _appareil(monde)
    op = _op_candidature(monde, formation)
    r1 = appliquer_lot(monde["u"]["aa.cmr"], appareil, [op])["resultats"][0]
    r2 = appliquer_lot(monde["u"]["aa.cmr"], appareil, [op])["resultats"][0]
    assert r1["resultat"] == "appliquee", r1
    assert r2["resultat"] == "appliquee" and r2.get("deja_recue")
    assert Candidature.objects.count() == 1


def test_une_operation_hors_ligne_dans_un_mois_verrouille_devient_ecriture_tardive(monde):
    from caef.synchronisation.models import ConflitSynchronisation
    from caef.synchronisation.moteur import appliquer_lot

    pdv, produit = boutique(monde)
    vb = monde["u"]["vb.cmr"]
    appareil = _appareil(monde)
    from caef.boutique import services as bou

    bou.ouvrir_caisse(vb, pdv, fond_de_caisse=0)
    verrouiller_mois(monde)
    op = {"id": str(uuid.uuid4()), "type": "vente.creer", "horodatage": timezone.now().isoformat(),
          "donnees": {"point_de_vente": str(pdv.pk), "lignes": [{"produit": str(produit.pk), "quantite": 1}],
                      "reglements": [{"mode": "especes", "montant": 10000}]}}
    r = appliquer_lot(vb, appareil, [op])["resultats"][0]
    assert r["resultat"] == "ecriture_tardive"
    assert ConflitSynchronisation.objects.filter(operation_id=op["id"]).exists()


def test_le_mode_hors_ligne_est_refuse_aux_roles_en_ligne(monde):
    from caef.synchronisation import services as sync

    appareil = _appareil(monde)
    with pytest.raises(AccesRefuse):
        sync.delivrer_jeton(monde["u"]["rse.national"], appareil)


# --------------------------------------------------------------------------- paiements

def _notifier(client, corps: dict, signature=None):
    import json

    from caef.paiements.passerelles import passerelle

    brut = json.dumps(corps).encode()
    sig = signature if signature is not None else passerelle("simulateur").signer(brut)
    return client.post("/api/v1/paiements/notifications/simulateur/", brut, content_type="application/json",
                       HTTP_X_SIGNATURE=sig)


def test_notification_a_signature_invalide_refusee_et_journalisee(monde, client):
    avant = JournalAudit.objects.filter(action="acces_refuse").count()
    r = _notifier(client, {"status": "SUCCESS", "transaction_id": "TX-FICTIF-1", "amount": 1000}, signature="faux")
    assert r.status_code == 401
    assert JournalAudit.objects.filter(action="acces_refuse").count() == avant + 1


def test_le_montant_confirme_vient_de_l_operateur_et_la_notification_est_idempotente(monde, client):
    from caef.paiements import services as pay
    from caef.paiements.models import TransactionPasserelle

    p = pay.declarer_mobile_money(monde["u"]["aa.cmr"], monde["cmr"], identifiant_transaction="TX-FICTIF-2",
                                  montant_declare=100000)
    assert p.statut == "declare"
    corps = {"status": "SUCCESS", "transaction_id": "TX-FICTIF-2", "amount": 95000, "fee": 1000}
    assert _notifier(client, corps).status_code == 200
    assert _notifier(client, corps).status_code == 200
    p.refresh_from_db()
    assert p.statut == "confirme" and p.montant_confirme == 95000
    assert TransactionPasserelle.objects.filter(identifiant_operateur="TX-FICTIF-2").count() == 1


def test_un_identifiant_de_transaction_ne_sert_qu_une_fois(monde):
    from caef.paiements import services as pay

    pay.declarer_mobile_money(monde["u"]["aa.cmr"], monde["cmr"], identifiant_transaction="TX-FICTIF-3",
                              montant_declare=5000)
    with pytest.raises(RegleMetier):
        pay.declarer_mobile_money(monde["u"]["aa.cmr"], monde["cmr"], identifiant_transaction="TX-FICTIF-3",
                                  montant_declare=5000)


# --------------------------------------------------------------------------- valeurs absentes

def test_une_valeur_absente_n_est_pas_zero(monde):
    """Aucune séance passée : le taux de présence est « non renseigné », pas 0 %."""
    from caef.beneficiaires import services as ben
    from caef.formations import services as form

    formation, session, _ = session_ouverte(monde, decalage_seance=3)
    cand = ben.creer_candidature(monde["u"]["aa.cmr"], centre=monde["cmr"], formation=formation,
                                 identite=dossier_complet(zone=monde["zone"]))
    ben.soumettre_candidature(monde["u"]["aa.cmr"], cand)
    ben.valider_candidature(monde["u"]["rc.cmr"], cand)
    inscription = form.inscrire(monde["u"]["rp.cmr"], cand, session)
    assert form.taux_presence(inscription) is None
