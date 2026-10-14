"""Envoi des notifications par canal ; au MVP, seul le canal application est actif (SFD 8.4)."""

from django.db.models import Q

from .models import Canal, Notification


class CanalApplication:
    def envoyer(self, destinataire, type_evenement, message, objet=None):
        return Notification.objects.create(
            destinataire=destinataire,
            type_evenement=type_evenement,
            objet_type=objet._meta.db_table if objet is not None else "",
            objet_id=getattr(objet, "pk", None),
            message=message[:300],
            canal=Canal.APPLICATION,
        )


CANAUX = {Canal.APPLICATION: CanalApplication()}


def notifier(destinataires, type_evenement, message, objet=None, canal=Canal.APPLICATION):
    vus = set()
    resultat = []
    for d in destinataires:
        if d is None or d.pk in vus:
            continue
        vus.add(d.pk)
        resultat.append(CANAUX[canal].envoyer(d, type_evenement, message, objet))
    return resultat


def utilisateurs_du_role(centre_id, *roles):
    from caef.habilitations.models import Affectation
    from caef.habilitations.services import aujourd_hui
    from caef.identite.models import Utilisateur

    jour = aujourd_hui()
    ids = (
        Affectation.objects.filter(role_id__in=roles, archive=False, date_debut__lte=jour)
        .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=jour))
        .filter(Q(centre_id=centre_id) | Q(national=True))
        .values_list("utilisateur_id", flat=True)
    )
    return list(Utilisateur.objects.filter(pk__in=ids, statut="actif"))


def notifier_role(centre_id, roles, type_evenement, message, objet=None):
    return notifier(utilisateurs_du_role(centre_id, *roles), type_evenement, message, objet)


def notifier_responsables_des_centres_de(utilisateur, type_evenement, message):
    from caef.habilitations.models import Affectation

    centres = set(Affectation.objects.filter(utilisateur=utilisateur, centre__isnull=False)
                  .values_list("centre_id", flat=True))
    for cid in centres:
        notifier_role(cid, ("RC",), type_evenement, message, utilisateur)
