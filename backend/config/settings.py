"""Paramètres de CAEF Connect.

Tous les secrets et chaînes de connexion viennent de variables d'environnement
(brief développeur, règle 10). Aucune valeur sensible n'est écrite ici.
"""

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(nom, defaut=None, obligatoire=False):
    valeur = os.environ.get(nom, defaut)
    if obligatoire and not valeur:
        raise RuntimeError(f"Variable d'environnement manquante : {nom}")
    return valeur


def env_bool(nom, defaut=False):
    return str(os.environ.get(nom, defaut)).lower() in {"1", "true", "oui", "yes"}


def env_int(nom, defaut):
    return int(os.environ.get(nom, defaut))


ENVIRONNEMENT = env("CAEF_ENVIRONNEMENT", "developpement")  # developpement, recette, preproduction, production
DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = env("DJANGO_SECRET_KEY", obligatoire=True)
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
CSRF_TRUSTED_ORIGINS = [o for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "caef.commun",
    "caef.identite",
    "caef.referentiels",
    "caef.habilitations",
    "caef.journal",
    "caef.notifications",
    "caef.documents",
    "caef.beneficiaires",
    "caef.formations",
    "caef.partenaires",
    "caef.conventions",
    "caef.boutique",
    "caef.facturation",
    "caef.paiements",
    "caef.pilotage",
    "caef.synchronisation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "caef.identite.middleware.ExpirationSessionMiddleware",
    "caef.journal.middleware.ContexteRequeteMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "caef"),
        "USER": env("POSTGRES_USER", "caef"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        # Chaque service métier ouvre sa propre transaction (journal d'audit compris) ;
        # un refus d'accès est journalisé hors de toute transaction annulée.
        "ATOMIC_REQUESTS": False,
        "CONN_MAX_AGE": env_int("POSTGRES_CONN_MAX_AGE", 60),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "identite.Utilisateur"
AUTHENTICATION_BACKENDS = ["caef.identite.backends.BackendIdentifiant"]

# Argon2id en premier (DAT § 5.1, SEC-08).
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
     "OPTIONS": {"user_attributes": ("identifiant_connexion", "nom", "prenom")}},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Conakry"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Sessions : cookie sécurisé, HttpOnly, SameSite ; 30 minutes d'inactivité, 8 heures au plus (SEC-02).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = env_int("CAEF_SESSION_INACTIVITE_MINUTES", 30) * 60
SESSION_SAVE_EVERY_REQUEST = True
CAEF_SESSION_DUREE_MAX = timedelta(hours=env_int("CAEF_SESSION_DUREE_MAX_HEURES", 8))

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = env_int("DJANGO_HSTS_SECONDS", 0)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "caef.synchronisation.authentification.AuthentificationAppareil",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["caef.identite.permissions.UtilisateurAuthentifie"],
    "DEFAULT_PAGINATION_CLASS": "caef.commun.drf.Pagination",
    "PAGE_SIZE": 25,
    "EXCEPTION_HANDLER": "caef.commun.drf.gestionnaire_exceptions",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": env("CAEF_DEBIT_UTILISATEUR", "600/minute"),
        "anon": env("CAEF_DEBIT_ANONYME", "60/minute"),
        "connexion": env("CAEF_DEBIT_CONNEXION", "10/minute"),
    },
    "DATETIME_FORMAT": "iso-8601",
    "COERCE_DECIMAL_TO_STRING": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API CAEF Connect",
    "DESCRIPTION": "API interne de CAEF Connect (synchronisation de l'application terrain, "
                   "listes dynamiques, notifications des passerelles de paiement). DAT § 4.2.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", "redis://localhost:6379/1"),
    }
    if env("REDIS_URL")
    else {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

# Tâches de fond (DAT § 3.1) : calcul nocturne, consultations de statut, rapprochements.
CELERY_BROKER_URL = env("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TIMEZONE = TIME_ZONE

# Stockage d'objets compatible S3, chiffré (DAT § 3.1). En développement : disque local.
if env("S3_BUCKET"):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": env("S3_BUCKET"),
                "endpoint_url": env("S3_ENDPOINT_URL"),
                "access_key": env("S3_ACCESS_KEY"),
                "secret_key": env("S3_SECRET_KEY"),
                "region_name": env("S3_REGION", "us-east-1"),
                "default_acl": None,
                "querystring_auth": True,
                "object_parameters": {"ServerSideEncryption": "AES256"} if env_bool("S3_CHIFFREMENT_SERVEUR", True) else {},
                "file_overwrite": False,
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": env("CAEF_STOCKAGE_LOCAL", str(BASE_DIR / "stockage"))},
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

# Clé distincte pour les champs restreints chiffrés (pièce d'identité, secrets TOTP), DAT § 5.3.
CAEF_CLE_CHIFFREMENT_CHAMPS = env("CAEF_CLE_CHIFFREMENT_CHAMPS", obligatoire=True)

# Paramètres métier : positions d'attente du brief (section 5), tous réglables sans code.
CAEF = {
    # Jeu de démonstration fictif (manage.py generer_donnees_fictives) ; jamais en production.
    "MOT_DE_PASSE_DEMO": env("CAEF_MOT_DE_PASSE_DEMO", ""),
    "SEUIL_DOUBLON_BLOQUANT": env_int("CAEF_SEUIL_DOUBLON_BLOQUANT", 60),
    "SEUIL_DOUBLON_INFORMATIF": env_int("CAEF_SEUIL_DOUBLON_INFORMATIF", 40),
    "JOURS_BENEFICIAIRE_ACTIVE": env_int("CAEF_JOURS_BENEFICIAIRE_ACTIVE", 90),
    "SEUIL_PETITS_EFFECTIFS": env_int("CAEF_SEUIL_PETITS_EFFECTIFS", 5),
    "SEUIL_PRESENCE_DEFAUT": env_int("CAEF_SEUIL_PRESENCE_DEFAUT", 80),
    "DELAI_SAISIE_PRESENCES_JOURS": env_int("CAEF_DELAI_SAISIE_PRESENCES_JOURS", 7),
    "DEROGATION_CAPACITE_PCT": env_int("CAEF_DEROGATION_CAPACITE_PCT", 10),
    "ABSENCES_CONSECUTIVES_ALERTE": env_int("CAEF_ABSENCES_CONSECUTIVES_ALERTE", 3),
    "INACTIVITE_COMPTE_JOURS": env_int("CAEF_INACTIVITE_COMPTE_JOURS", 90),
    "ECHECS_BLOCAGE": env_int("CAEF_ECHECS_BLOCAGE", 5),
    "BLOCAGE_MINUTES": env_int("CAEF_BLOCAGE_MINUTES", 15),
    "ECHECS_SUSPENSION_HEURE": env_int("CAEF_ECHECS_SUSPENSION_HEURE", 10),
    "HORS_LIGNE_VALIDITE_HEURES": env_int("CAEF_HORS_LIGNE_VALIDITE_HEURES", 72),
    "ALERTE_SYNCHRO_HEURES": env_int("CAEF_ALERTE_SYNCHRO_HEURES", 48),
    "ECART_HORLOGE_SECONDES": env_int("CAEF_ECART_HORLOGE_SECONDES", 300),
    "PAIEMENT_NON_RETROUVE_HEURES": env_int("CAEF_PAIEMENT_NON_RETROUVE_HEURES", 24),
    "PAIEMENT_CONSULTATIONS_MINUTES": [1, 5, 15, 60],
    "DOCUMENT_TAILLE_MAX_OCTETS": env_int("CAEF_DOCUMENT_TAILLE_MAX_OCTETS", 10 * 1024 * 1024),
    "DOCUMENT_LIEN_SECONDES": env_int("CAEF_DOCUMENT_LIEN_SECONDES", 300),
    "CLOTURE_MENSUELLE_JOUR_LIMITE": env_int("CAEF_CLOTURE_MENSUELLE_JOUR_LIMITE", 10),
    "FUSION_REVERSIBLE_JOURS": env_int("CAEF_FUSION_REVERSIBLE_JOURS", 30),
    "JOURS_INACTIVITE_DOSSIER": env_int("CAEF_JOURS_INACTIVITE_DOSSIER", 365),
    # Champs requis pour un dossier complet : liste minimale à valider par la Direction (PRD H4).
    "CHAMPS_REQUIS_DOSSIER": ("nom", "prenoms", "sexe", "zone_residence", "consentement_date",
                              "consentement_mode", "naissance"),
    "HABILITATION_EXCEPTIONNELLE_JOURS_MAX": 30,
    # Seuil de seconde validation d'une proposition (RG-CNV-02, H5) : non fixé tant que la Direction ne l'a pas décidé.
    "SEUIL_SECONDE_VALIDATION_PROPOSITION": env("CAEF_SEUIL_SECONDE_VALIDATION_PROPOSITION", None),
    "FIABILITE_FAIBLE_PCT_MANQUANTS": 20,
    "PASSERELLE_MOBILE_MONEY": env("CAEF_PASSERELLE_MOBILE_MONEY", "declaratif"),
    "NUMERO_MARCHAND": env("CAEF_NUMERO_MARCHAND", ""),
    # Centre dont le comptable reçoit les paiements sans référence d'échéance valide (compte marchand commun, H16).
    "CENTRE_PAIEMENTS_NON_REFERENCES": env("CAEF_CENTRE_PAIEMENTS_NON_REFERENCES", ""),
}

# Secrets de la passerelle (coffre de secrets en production) ; aucun appel réel hors production.
PASSERELLE_SIMULATEUR_SECRET = env("CAEF_PASSERELLE_SIMULATEUR_SECRET", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO")},
}
