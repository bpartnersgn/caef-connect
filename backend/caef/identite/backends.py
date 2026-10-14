from django.contrib.auth.backends import ModelBackend


class BackendIdentifiant(ModelBackend):
    """Authentification par identifiant de connexion ; un compte non actif ne s'authentifie pas.

    Le statut est relu à chaque requête : la désactivation coupe immédiatement les sessions
    ouvertes (RG-ADM-07, SEC-06).
    """

    def user_can_authenticate(self, user):
        return getattr(user, "is_active", False)

    def get_user_permissions(self, user_obj, obj=None):  # droits issus de la Matrice, pas de Django
        return set()

    def get_group_permissions(self, user_obj, obj=None):
        return set()
