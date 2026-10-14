"""Le journal d'audit est en ajout seul, y compris pour l'administrateur (SEC-04)."""

from django.db import migrations

SQL = """
CREATE OR REPLACE FUNCTION caef_refuser_modification() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Table % en ajout seul : modification ou suppression interdite', TG_TABLE_NAME
        USING ERRCODE = 'insufficient_privilege';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER journal_audit_ajout_seul
    BEFORE UPDATE OR DELETE ON journal_audit
    FOR EACH ROW EXECUTE FUNCTION caef_refuser_modification();
CREATE TRIGGER journal_audit_pas_de_vidage
    BEFORE TRUNCATE ON journal_audit
    FOR EACH STATEMENT EXECUTE FUNCTION caef_refuser_modification();
"""

REVERSE = """
DROP TRIGGER IF EXISTS journal_audit_pas_de_vidage ON journal_audit;
DROP TRIGGER IF EXISTS journal_audit_ajout_seul ON journal_audit;
"""


class Migration(migrations.Migration):
    dependencies = [("journal", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
