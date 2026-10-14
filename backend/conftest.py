"""Fixtures communes : un monde entièrement fictif (règle 7), un compte par rôle."""

import pytest
from django.test import override_settings

from caef.commun.fictif import creer_socle

MOT_DE_PASSE = "Mot-de-passe-de-test-1"


@pytest.fixture(autouse=True)
def _reglages_de_test(settings):
    settings.PASSERELLE_SIMULATEUR_SECRET = "secret-de-test-fictif"
    settings.CAEF = {**settings.CAEF, "PASSERELLE_MOBILE_MONEY": "simulateur"}
    settings.STORAGES = {**settings.STORAGES, "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}
    with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
        yield


@pytest.fixture
def monde(db):
    return creer_socle()


@pytest.fixture
def monde_connectable(db):
    return creer_socle(MOT_DE_PASSE)


@pytest.fixture
def connecter():
    from rest_framework.test import APIClient

    def _connecter(identifiant):
        c = APIClient()
        r = c.post("/api/v1/auth/connexion/", {"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE},
                   format="json")
        assert r.status_code == 200, r.content
        return c

    return _connecter
