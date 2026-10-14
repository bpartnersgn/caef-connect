"""Erreurs métier, avec des messages en français clair (brief § 6.1)."""


class ErreurMetier(Exception):
    statut_http = 400
    code = "erreur_metier"

    def __init__(self, message, *, code=None, details=None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details or {}


class RegleMetier(ErreurMetier):
    """Une règle de gestion (RG-xxx) refuse l'action."""

    statut_http = 400
    code = "regle_metier"


class TransitionInterdite(RegleMetier):
    code = "transition_interdite"


class Introuvable(ErreurMetier):
    statut_http = 404
    code = "introuvable"


class AccesRefuse(ErreurMetier):
    """Refus d'accès : toujours journalisé (SEC-01, SEC-04)."""

    statut_http = 403
    code = "acces_refuse"

    def __init__(self, message="Accès refusé.", *, objet=None, action=None, centre_id=None,
                 objet_type=None, objet_id=None, code=None, details=None):
        super().__init__(message, code=code, details=details)
        self.objet = objet
        self.action = action
        self.centre_id = centre_id
        self.objet_type = objet_type
        self.objet_id = objet_id


class ModuleNonActive(AccesRefuse):
    code = "module_non_active"

    def __init__(self, module, **kwargs):
        super().__init__("Module non activé.", **kwargs)
        self.module = module


class SeparationDesTaches(AccesRefuse):
    code = "separation_des_taches"


class MoisVerrouille(RegleMetier):
    """Écriture datée d'un mois dont la clôture est validée (RG-SRC-02, RG-OFF-07)."""

    statut_http = 409
    code = "mois_verrouille"


class ConflitVersion(ErreurMetier):
    statut_http = 409
    code = "conflit_version"

    def __init__(self, message="La fiche a été modifiée entre-temps : rechargez-la avant d'enregistrer.", **kwargs):
        super().__init__(message, **kwargs)


class DoubleAuthRequise(AccesRefuse):
    code = "double_auth_requise"
