"""Journal des changements par centre, lu par les appareils au curseur (DAT § 4.5)."""

from django.db import connection

from .models import JournalChangements, NatureChangement


def publier(centre_id, objet, nature=NatureChangement.MODIFICATION):
    """Ajoute une entrée numérotée de façon croissante pour le centre, dans la transaction en cours."""
    centre_id = getattr(centre_id, "pk", centre_id)
    if centre_id is None:
        return None
    with connection.cursor() as curseur:
        # Verrou transactionnel par centre : numérotation sans doublon sous saisies concurrentes.
        curseur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [f"journal_changements:{centre_id}"])
    dernier = (JournalChangements.objects.filter(centre_id=centre_id).order_by("-numero")
               .values_list("numero", flat=True).first()) or 0
    return JournalChangements.objects.create(
        centre_id=centre_id, numero=dernier + 1, objet_type=objet._meta.db_table, objet_id=objet.pk,
        nature=nature, version=getattr(objet, "version", 1) or 1,
    )
