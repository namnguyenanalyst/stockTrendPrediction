"""Importing E2E configuration cannot discover or contact a live application."""
import runpy
from pathlib import Path
import httpx
import pytest

CONFIG = Path(__file__).parents[1] / 'e2e/conftest.py'

def test_default_never_contacts_api(monkeypatch):
    for key in ['E2E_BASE_URL', 'E2E_FORCE_MOCK', 'E2E_MODE', 'E2E_TARGET_ENV']:
        monkeypatch.delenv(key, raising=False)
    def forbidden(*args, **kwargs):
        raise AssertionError('Unexpected network access')
    monkeypatch.setattr(httpx.Client, 'get', forbidden)
    assert runpy.run_path(str(CONFIG))['LIVE_AVAILABLE'] is False

def test_explicit_url_requires_live_acceptance(monkeypatch):
    monkeypatch.setenv('E2E_BASE_URL', 'http://localhost:8000')
    monkeypatch.delenv('E2E_MODE', raising=False)
    monkeypatch.delenv('E2E_FORCE_MOCK', raising=False)
    with pytest.raises(pytest.UsageError):
        runpy.run_path(str(CONFIG))

def test_development_health_rejected(monkeypatch):
    monkeypatch.setenv('E2E_BASE_URL', 'http://localhost:8000')
    monkeypatch.setenv('E2E_MODE', 'live')
    monkeypatch.setenv('E2E_TARGET_ENV', 'acceptance')
    monkeypatch.delenv('E2E_FORCE_MOCK', raising=False)
    def fake_get(self, url):
        return httpx.Response(200, json={'environment': 'development'})
    monkeypatch.setattr(httpx.Client, 'get', fake_get)
    with pytest.raises(pytest.UsageError):
        runpy.run_path(str(CONFIG))

def test_live_without_url_refused(monkeypatch):
    monkeypatch.setenv('E2E_MODE', 'live')
    monkeypatch.delenv('E2E_BASE_URL', raising=False)
    with pytest.raises(pytest.UsageError):
        runpy.run_path(str(CONFIG))
