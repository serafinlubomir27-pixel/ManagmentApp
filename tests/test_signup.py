"""M2 — testy self-signupu, e-mailovej identity a resetu hesla.

Spustenie:
    py -m pytest tests/test_signup.py -v
"""
import pytest
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main
from repositories import user_repo, org_repo
from repositories.base_repo import get_connection

client = TestClient(main.app)


def _latest_reset_token(user_id: int) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT token FROM password_resets WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return row["token"] if row else None
    finally:
        conn.close()


# ── Signup ───────────────────────────────────────────────────────────────────

def test_signup_creates_org_and_admin():
    r = client.post("/auth/signup", json={
        "email": "founder@acme.sk", "password": "superheslo1",
        "full_name": "Founder", "organization_name": "Acme s.r.o.",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["role"] == "admin"
    assert body["access_token"]

    user = user_repo.get_by_email("founder@acme.sk")
    assert user is not None
    # Vlastná organizácia, nie "default"
    default_org = org_repo.get_organization_by_slug("default")
    assert user["organization_id"] != default_org["id"]


def test_signup_duplicate_email_conflicts():
    payload = {
        "email": "dup@acme.sk", "password": "superheslo1",
        "full_name": "A", "organization_name": "Org1",
    }
    assert client.post("/auth/signup", json=payload).status_code == 201
    r2 = client.post("/auth/signup", json={**payload, "organization_name": "Org2"})
    assert r2.status_code == 409


def test_signup_rejects_short_password():
    r = client.post("/auth/signup", json={
        "email": "weak@acme.sk", "password": "short",
        "full_name": "W", "organization_name": "WeakOrg",
    })
    assert r.status_code == 400


def test_signup_rejects_bad_email():
    r = client.post("/auth/signup", json={
        "email": "not-an-email", "password": "superheslo1",
        "full_name": "X", "organization_name": "BadOrg",
    })
    assert r.status_code == 400


# ── Login cez e-mail ─────────────────────────────────────────────────────────

def test_login_by_email():
    client.post("/auth/signup", json={
        "email": "login@acme.sk", "password": "superheslo1",
        "full_name": "L", "organization_name": "LoginOrg",
    })
    r = client.post("/auth/login", data={"username": "login@acme.sk", "password": "superheslo1"})
    assert r.status_code == 200


def test_login_by_username_still_works():
    # admin je seedovaný v conftest s username 'admin' a heslom 'admin123' (bez e-mailu)
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200


# ── Reset hesla ──────────────────────────────────────────────────────────────

def test_password_reset_roundtrip():
    client.post("/auth/signup", json={
        "email": "reset@acme.sk", "password": "povodneheslo1",
        "full_name": "R", "organization_name": "ResetOrg",
    })
    uid = user_repo.get_by_email("reset@acme.sk")["id"]

    # forgot → vždy 200, token vznikne v DB
    assert client.post("/auth/forgot-password", json={"email": "reset@acme.sk"}).status_code == 200
    token = _latest_reset_token(uid)
    assert token

    # reset s tokenom
    r = client.post("/auth/reset-password", json={"token": token, "new_password": "noveheslo123"})
    assert r.status_code == 200

    # staré heslo už neplatí, nové áno
    assert client.post("/auth/login", data={"username": "reset@acme.sk", "password": "povodneheslo1"}).status_code == 401
    assert client.post("/auth/login", data={"username": "reset@acme.sk", "password": "noveheslo123"}).status_code == 200

    # token je jednorazový
    r2 = client.post("/auth/reset-password", json={"token": token, "new_password": "este_ine1"})
    assert r2.status_code == 400


def test_forgot_password_unknown_email_is_generic_200():
    # Neexistujúci e-mail → stále 200 (žiadna enumerácia účtov)
    r = client.post("/auth/forgot-password", json={"email": "nikto@nikde.sk"})
    assert r.status_code == 200
