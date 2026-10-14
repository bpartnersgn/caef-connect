"""Alimente les tables `role` et `permission` depuis matrice.yaml (DAT § 5.2)."""

from django.db import transaction

from .matrice import matrice


def synchroniser_matrice(**kwargs):
    from .models import Permission, Role

    m = matrice()
    with transaction.atomic():
        for code, r in m.roles.items():
            Role.objects.update_or_create(
                code=code,
                defaults={"libelle": r.libelle, "titre_organigramme": r.titre, "double_auth": r.double_auth,
                          "hors_ligne": r.hors_ligne, "actif": True},
            )
        attendues = set()
        for code, objet in m.objets.items():
            for role, droits in objet.droits.items():
                for action, droit in droits.items():
                    attendues.add((role, code, action))
                    Permission.objects.update_or_create(
                        role_id=role, objet=code, action=action,
                        defaults={"perimetre": droit.perimetre, "condition": droit.condition, "module": objet.module},
                    )
        for p in Permission.objects.all():
            if (p.role_id, p.objet, p.action) not in attendues:
                p.delete()
