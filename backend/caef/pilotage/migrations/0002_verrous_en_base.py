"""Garde-fous en base de données, en plus des services métier.

1. Mois verrouillé (SRC-02, RG-SRC-02) : après validation de la clôture mensuelle, la base refuse
   toute écriture financière datée de ce mois (vente, règlement, session de caisse, reversement,
   contribution reçue, paiement). Une correction passe par une régularisation datée du mois courant.
2. Clôture validée et ses lignes : plus aucune modification.
3. Aucune suppression physique des enregistrements financiers ; ajout seul pour les mouvements de
   stock, ventes, lignes de vente, transactions de l'opérateur et journal des changements
   (RG-GEN-03, BOU-04, BOU-06, PAY-08).
"""

from django.db import migrations

TABLES_SANS_SUPPRESSION = [
    "vente", "ligne_vente", "reglement", "mouvement_stock", "prix_produit", "session_caisse", "inventaire",
    "ligne_inventaire", "reversement", "depot", "paiement", "affectation_paiement", "transaction_passerelle",
    "remboursement", "ligne_releve_operateur", "echeance", "exoneration", "tarif_service", "contribution",
    "convention", "cloture_mensuelle", "ligne_rapprochement", "module_centre", "operation_synchronisation",
    "journal_changements", "beneficiaire", "candidature", "inscription", "presence", "attestation",
]
TABLES_AJOUT_SEUL = ["mouvement_stock", "vente", "ligne_vente", "transaction_passerelle", "journal_changements"]

SQL = """
CREATE OR REPLACE FUNCTION caef_mois_verrouille(p_centre uuid, p_jour date) RETURNS boolean AS $$
    SELECT EXISTS (
        SELECT 1 FROM cloture_mensuelle
        WHERE centre_id = p_centre AND mois = to_char(p_jour, 'YYYY-MM') AND verrouillee
    );
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION caef_refuser_mois_verrouille(p_centre uuid, p_jour date) RETURNS void AS $$
BEGIN
    IF p_jour IS NOT NULL AND caef_mois_verrouille(p_centre, p_jour) THEN
        RAISE EXCEPTION 'Mois % verrouillé : passez par une écriture de régularisation datée du mois courant',
            to_char(p_jour, 'YYYY-MM') USING ERRCODE = 'check_violation';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Vente : centre du point de vente, date réelle de la vente.
CREATE OR REPLACE FUNCTION caef_verrou_vente() RETURNS trigger AS $$
BEGIN
    PERFORM caef_refuser_mois_verrouille(
        (SELECT centre_id FROM point_de_vente WHERE id = NEW.point_de_vente_id),
        (NEW.date_heure_vente AT TIME ZONE 'Africa/Conakry')::date);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER vente_mois_verrouille BEFORE INSERT ON vente
    FOR EACH ROW EXECUTE FUNCTION caef_verrou_vente();

CREATE OR REPLACE FUNCTION caef_verrou_reglement() RETURNS trigger AS $$
BEGIN
    PERFORM caef_refuser_mois_verrouille(p.centre_id, (v.date_heure_vente AT TIME ZONE 'Africa/Conakry')::date)
    FROM vente v JOIN point_de_vente p ON p.id = v.point_de_vente_id WHERE v.id = NEW.vente_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER reglement_mois_verrouille BEFORE INSERT ON reglement
    FOR EACH ROW EXECUTE FUNCTION caef_verrou_reglement();

CREATE OR REPLACE FUNCTION caef_verrou_session_caisse() RETURNS trigger AS $$
BEGIN
    PERFORM caef_refuser_mois_verrouille(
        (SELECT centre_id FROM point_de_vente WHERE id = NEW.point_de_vente_id), NEW.date);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER session_caisse_mois_verrouille BEFORE INSERT OR UPDATE ON session_caisse
    FOR EACH ROW EXECUTE FUNCTION caef_verrou_session_caisse();

CREATE OR REPLACE FUNCTION caef_verrou_reversement() RETURNS trigger AS $$
BEGIN
    IF NEW.date_paiement IS NOT NULL THEN
        PERFORM caef_refuser_mois_verrouille(
            (SELECT centre_id FROM point_de_vente WHERE id = NEW.point_de_vente_id), NEW.date_paiement);
    END IF;
    IF TG_OP = 'UPDATE' AND OLD.date_paiement IS NOT NULL THEN
        PERFORM caef_refuser_mois_verrouille(
            (SELECT centre_id FROM point_de_vente WHERE id = OLD.point_de_vente_id), OLD.date_paiement);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER reversement_mois_verrouille BEFORE INSERT OR UPDATE ON reversement
    FOR EACH ROW EXECUTE FUNCTION caef_verrou_reversement();

-- Contribution : seuls la réception et son montant sont des flux du mois ; la validation par la DG
-- et le rapprochement du comptable restent possibles après verrouillage.
CREATE OR REPLACE FUNCTION caef_verrou_contribution() RETURNS trigger AS $$
BEGIN
    IF NEW.financiere AND NEW.statut IN ('recue', 'validee') AND (
        TG_OP = 'INSERT'
        OR NEW.montant_recu IS DISTINCT FROM OLD.montant_recu
        OR NEW.date_reception IS DISTINCT FROM OLD.date_reception
        OR NEW.devise IS DISTINCT FROM OLD.devise
        OR OLD.statut NOT IN ('recue', 'validee')
    ) THEN
        PERFORM caef_refuser_mois_verrouille(NEW.centre_beneficiaire_id, NEW.date_reception);
        IF TG_OP = 'UPDATE' AND OLD.date_reception IS NOT NULL THEN
            PERFORM caef_refuser_mois_verrouille(OLD.centre_beneficiaire_id, OLD.date_reception);
        END IF;
    END IF;
    IF TG_OP = 'UPDATE' AND NEW.statut = 'annulee' AND OLD.statut IN ('recue', 'validee') AND OLD.financiere THEN
        PERFORM caef_refuser_mois_verrouille(OLD.centre_beneficiaire_id, OLD.date_reception);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER contribution_mois_verrouille BEFORE INSERT OR UPDATE ON contribution
    FOR EACH ROW EXECUTE FUNCTION caef_verrou_contribution();

CREATE OR REPLACE FUNCTION caef_verrou_paiement() RETURNS trigger AS $$
BEGIN
    IF NEW.statut IN ('confirme', 'declare') THEN
        PERFORM caef_refuser_mois_verrouille(NEW.centre_id,
            (COALESCE(NEW.confirme_le, NEW.cree_le) AT TIME ZONE 'Africa/Conakry')::date);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER paiement_mois_verrouille BEFORE INSERT ON paiement
    FOR EACH ROW EXECUTE FUNCTION caef_verrou_paiement();

-- Clôture validée et ses lignes : figées.
CREATE OR REPLACE FUNCTION caef_cloture_figee() RETURNS trigger AS $$
BEGIN
    IF OLD.verrouillee THEN
        RAISE EXCEPTION 'Clôture mensuelle validée : elle ne se modifie plus' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER cloture_mensuelle_figee BEFORE UPDATE ON cloture_mensuelle
    FOR EACH ROW EXECUTE FUNCTION caef_cloture_figee();

CREATE OR REPLACE FUNCTION caef_ligne_rapprochement_figee() RETURNS trigger AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM cloture_mensuelle WHERE id = COALESCE(NEW.cloture_mensuelle_id, OLD.cloture_mensuelle_id)
               AND verrouillee) THEN
        RAISE EXCEPTION 'Clôture mensuelle validée : ses lignes ne se modifient plus' USING ERRCODE = 'check_violation';
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER ligne_rapprochement_figee BEFORE INSERT OR UPDATE ON ligne_rapprochement
    FOR EACH ROW EXECUTE FUNCTION caef_ligne_rapprochement_figee();
"""

REVERSE = """
DROP TRIGGER IF EXISTS ligne_rapprochement_figee ON ligne_rapprochement;
DROP TRIGGER IF EXISTS cloture_mensuelle_figee ON cloture_mensuelle;
DROP TRIGGER IF EXISTS paiement_mois_verrouille ON paiement;
DROP TRIGGER IF EXISTS contribution_mois_verrouille ON contribution;
DROP TRIGGER IF EXISTS reversement_mois_verrouille ON reversement;
DROP TRIGGER IF EXISTS session_caisse_mois_verrouille ON session_caisse;
DROP TRIGGER IF EXISTS reglement_mois_verrouille ON reglement;
DROP TRIGGER IF EXISTS vente_mois_verrouille ON vente;
DROP FUNCTION IF EXISTS caef_ligne_rapprochement_figee();
DROP FUNCTION IF EXISTS caef_cloture_figee();
DROP FUNCTION IF EXISTS caef_verrou_paiement();
DROP FUNCTION IF EXISTS caef_verrou_contribution();
DROP FUNCTION IF EXISTS caef_verrou_reversement();
DROP FUNCTION IF EXISTS caef_verrou_session_caisse();
DROP FUNCTION IF EXISTS caef_verrou_reglement();
DROP FUNCTION IF EXISTS caef_verrou_vente();
DROP FUNCTION IF EXISTS caef_refuser_mois_verrouille(uuid, date);
DROP FUNCTION IF EXISTS caef_mois_verrouille(uuid, date);
"""


def _sql_suppressions():
    lignes = []
    for table in TABLES_SANS_SUPPRESSION:
        lignes.append(
            f"CREATE TRIGGER {table}_sans_suppression BEFORE DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION caef_refuser_modification();"
        )
    for table in TABLES_AJOUT_SEUL:
        lignes.append(
            f"CREATE TRIGGER {table}_ajout_seul BEFORE UPDATE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION caef_refuser_modification();"
        )
    return "\n".join(lignes)


def _sql_suppressions_inverse():
    lignes = [f"DROP TRIGGER IF EXISTS {t}_sans_suppression ON {t};" for t in TABLES_SANS_SUPPRESSION]
    lignes += [f"DROP TRIGGER IF EXISTS {t}_ajout_seul ON {t};" for t in TABLES_AJOUT_SEUL]
    return "\n".join(lignes)


class Migration(migrations.Migration):
    dependencies = [
        ("pilotage", "0001_initial"),
        ("journal", "0002_journal_ajout_seul"),
        ("boutique", "0001_initial"),
        ("paiements", "0001_initial"),
        ("facturation", "0001_initial"),
        ("conventions", "0001_initial"),
        ("habilitations", "0001_initial"),
        ("synchronisation", "0001_initial"),
        ("beneficiaires", "0002_initial"),
        ("formations", "0001_initial"),
    ]
    operations = [
        migrations.RunSQL(SQL, REVERSE),
        migrations.RunSQL(_sql_suppressions(), _sql_suppressions_inverse()),
    ]
