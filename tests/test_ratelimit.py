"""M4 — test rate limitingu na verejných auth endpointoch.

Limiter je v testoch globálne vypnutý (conftest), tu ho dočasne zapneme a overíme,
že opakované volania forgot-password (limit 5/hodina) vrátia 429.
"""
import pytest
from fastapi.testclient import TestClient

import backend.main as main
from backend.ratelimit import limiter

client = TestClient(main.app)


@pytest.fixture
def rate_limit_on():
    """Dočasne zapne limiter a po teste vyčistí jeho stav."""
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.reset()
    limiter.enabled = False


def test_forgot_password_is_rate_limited(rate_limit_on):
    # limit je 5/hour → 6. volanie musí byť 429
    codes = [
        client.post("/auth/forgot-password", json={"email": "spam@x.sk"}).status_code
        for _ in range(6)
    ]
    assert codes[:5] == [200] * 5, codes
    assert codes[5] == 429, codes


def test_no_limit_when_disabled():
    # S vypnutým limiterom (default v testoch) prejde ľubovoľný počet volaní
    assert limiter.enabled is False
    codes = [
        client.post("/auth/forgot-password", json={"email": "ok@x.sk"}).status_code
        for _ in range(8)
    ]
    assert all(c == 200 for c in codes), codes
