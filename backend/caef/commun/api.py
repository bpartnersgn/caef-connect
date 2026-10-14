"""Briques communes de l'API REST /api/v1 (DAT § 4.2)."""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import mixins, viewsets

from caef.commun.exceptions import AccesRefuse
from caef.habilitations.services import decider, portee


def q_perimetre(utilisateur, objet, *, champ_centre="centre", champ_session=None, champ_propre=None,
                nominatif=False, action="L"):
    """Filtre de périmètre appliqué à toute liste, recherche, fiche ou export (RG-GEN-01, SEC-01).

    Renvoie None si l'utilisateur n'a aucun droit de lecture sur l'objet.
    """
    p = portee(utilisateur, objet, action, nominatif=nominatif)
    if p.vide:
        return None
    if p.national or champ_centre is None:
        q = Q()
    else:
        q = Q(**{f"{champ_centre}__in": p.centres}) if p.centres else Q(pk__in=[])
    if p.centres_sessions and champ_session is not None:
        from caef.formations.services import q_sessions_du_formateur

        q_s = Q(**{f"{champ_centre}__in": p.centres_sessions}) & q_sessions_du_formateur(utilisateur, champ_session)
        q = q_s if (not p.centres and not p.national) else (q | q_s)
    if p.propre and champ_propre is not None:
        q_p = Q(**{champ_propre: utilisateur})
        q = q_p if (not p.centres and not p.national and not p.centres_sessions) else (q | q_p)
    return q


class VueMetier(viewsets.GenericViewSet):
    """Vue de base : le filtre de périmètre est appliqué par défaut à toute requête de lecture.

    Chaque vue déclare l'objet de la Matrice qu'elle expose (`objet`) et le chemin vers le centre
    de l'objet (`champ_centre`). Un identifiant hors périmètre renvoie un refus journalisé, pas
    un simple « introuvable » (CA-T1, TS-01).
    """

    objet: str = ""
    nominatif: bool = False
    champ_centre: str | None = "centre"
    champ_session: str | None = None
    champ_propre: str | None = None
    lookup_value_regex = "[0-9a-f-]{36}"

    def queryset_base(self):
        return self.queryset.all()

    def get_queryset(self):
        q = q_perimetre(self.request.user, self.objet, champ_centre=self.champ_centre,
                        champ_session=self.champ_session, champ_propre=self.champ_propre,
                        nominatif=self.nominatif)
        if q is None:
            decision = decider(self.request.user, self.objet, "L")
            raise AccesRefuse(decision.motif or "Accès refusé.", objet=self.objet, action="L")
        qs = self.queryset_base().filter(q)
        if self.champ_session is not None:
            qs = qs.distinct()
        if not qs.ordered:
            qs = qs.order_by("pk")  # UUIDv7 : ordre de création, pagination stable
        return qs

    def get_object(self):
        cle = self.kwargs[self.lookup_url_kwarg or self.lookup_field]
        try:
            obj = self.get_queryset().get(**{self.lookup_field: cle})
        except ObjectDoesNotExist:
            modele = self.queryset_base().model
            existe = modele._default_manager.filter(**{self.lookup_field: cle}).first()
            if existe is None:
                raise
            centre = self._centre_de(existe)
            raise AccesRefuse("Hors de votre périmètre.", objet=self.objet, action="L",
                              centre_id=centre, objet_type=modele._meta.db_table, objet_id=existe.pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def _centre_de(self, obj):
        if not self.champ_centre:
            return None
        valeur = obj
        for morceau in self.champ_centre.split("__"):
            valeur = getattr(valeur, morceau, None)
            if valeur is None:
                return None
        return getattr(valeur, "pk", valeur)


class VueLectureMetier(mixins.ListModelMixin, mixins.RetrieveModelMixin, VueMetier):
    pass
