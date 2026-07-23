"""Regresné testy autorizácie (Fáza 0 — P0-1/P0-2).

Overujú, že:
  - endpointy vynucujú VLASTNÍCTVO objektu, nie len jeho existenciu (IDOR / BOLA),
  - registrácia je chránená a nedá sa cez ňu eskalovať na admina.

Spustenie:
    py -m pytest tests/test_authz.py -v

Pozn.: env sa nastavuje PRED importom aplikácie, lebo base_repo číta DB_BACKEND /
SQLITE_PATH pri importe a backend.main vytvorí tabuľky + seed admina pri štarte.
"""
import hashlib

import pytest
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py (spoločná testová SQLite DB).
import backend.main as main  # noqa: E402
from repositories import user_repo, project_repo, task_repo, client_repo, org_repo  # noqa: E402


def _sha(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app)


@pytest.fixture(scope="module")
def seed():
    """Vytvorí testovacích používateľov + dáta. Vráti mapu mien na id."""
    # admin (id 1) je nasadený automaticky v create_database(), v "default" organizácii
    org_id = org_repo.get_organization_by_slug("default")["id"]

    user_repo.create_user("alice", _sha("pw"), "Alice Manager", "manager", None, org_id)
    user_repo.create_user("bob", _sha("pw"), "Bob Employee", "employee", None, org_id)
    user_repo.create_user("carol", _sha("pw"), "Carol Employee", "employee", None, org_id)

    ids = {u["username"]: u["id"] for u in user_repo.get_all_users(org_id)}

    # Projekt vlastní BOB; CAROL je nezúčastnená.
    project_id = project_repo.create_project(ids["bob"], "Bobov projekt", "desc", org_id)
    # Úloha v projekte priradená bobovi.
    task_id = task_repo.create_task(
        project_id=project_id, name="Úloha", assigned_to=ids["bob"], created_by=ids["bob"],
    )
    # Klient, ktorého advisor je CAROL (employee).
    client_id = client_repo.create_client(
        "Klient X", advisor_id=ids["carol"], organization_id=org_id, email="x@x.sk"
    )

    return {
        "ids": ids,
        "project_id": project_id,
        "task_id": task_id,
        "client_id": client_id,
    }


def _token(client, username, password="pw"):
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, f"login {username} zlyhal: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── P0-2: IDOR na projektoch ─────────────────────────────────────────────────

def test_owner_can_read_own_project(client, seed):
    r = client.get(f"/projects/{seed['project_id']}", headers=_token(client, "bob"))
    assert r.status_code == 200


def test_unrelated_user_cannot_read_project(client, seed):
    r = client.get(f"/projects/{seed['project_id']}", headers=_token(client, "carol"))
    assert r.status_code == 403


def test_admin_can_read_any_project(client, seed):
    r = client.get(f"/projects/{seed['project_id']}", headers=_token(client, "admin", "admin123"))
    assert r.status_code == 200


def test_missing_project_is_404(client, seed):
    r = client.get("/projects/999999", headers=_token(client, "admin", "admin123"))
    assert r.status_code == 404


# ── P0-2: IDOR na úlohách ────────────────────────────────────────────────────

def test_assignee_can_read_task(client, seed):
    r = client.get(f"/tasks/{seed['task_id']}", headers=_token(client, "bob"))
    assert r.status_code == 200


def test_unrelated_user_cannot_read_task(client, seed):
    r = client.get(f"/tasks/{seed['task_id']}", headers=_token(client, "carol"))
    assert r.status_code == 403


def test_unrelated_user_cannot_patch_task(client, seed):
    r = client.patch(
        f"/tasks/{seed['task_id']}",
        json={"status": "completed"},
        headers=_token(client, "carol"),
    )
    assert r.status_code == 403


# ── P0-2: IDOR na klientoch (najcitlivejšie — financie/MiFID) ────────────────

def test_advisor_can_read_own_client(client, seed):
    r = client.get(f"/clients/{seed['client_id']}", headers=_token(client, "carol"))
    assert r.status_code == 200


def test_unrelated_employee_cannot_read_client(client, seed):
    # bob je employee a NIE je advisorom tohto klienta → 403
    r = client.get(f"/clients/{seed['client_id']}", headers=_token(client, "bob"))
    assert r.status_code == 403


def test_manager_can_read_any_client(client, seed):
    r = client.get(f"/clients/{seed['client_id']}", headers=_token(client, "alice"))
    assert r.status_code == 200


# ── P0-1: registrácia — žiadna eskalácia na admina ──────────────────────────

def test_register_requires_auth(client, seed):
    r = client.post("/auth/register", json={
        "username": "hacker", "password": "pw123456", "full_name": "H", "role": "admin",
    })
    assert r.status_code == 401  # bez tokenu


def test_employee_cannot_register_anyone(client, seed):
    r = client.post("/auth/register",
        json={"username": "x1", "password": "pw123456", "full_name": "X", "role": "employee"},
        headers=_token(client, "bob"),
    )
    assert r.status_code == 403  # employee nesmie vytvárať používateľov


def test_manager_cannot_create_admin(client, seed):
    r = client.post("/auth/register",
        json={"username": "x2", "password": "pw123456", "full_name": "X", "role": "admin"},
        headers=_token(client, "alice"),
    )
    assert r.status_code == 403


def test_manager_can_create_employee(client, seed):
    r = client.post("/auth/register",
        json={"username": "newemp", "password": "pw123456", "full_name": "New", "role": "employee"},
        headers=_token(client, "alice"),
    )
    assert r.status_code == 201


def test_admin_can_create_manager(client, seed):
    r = client.post("/auth/register",
        json={"username": "newmgr", "password": "pw123456", "full_name": "Mgr", "role": "manager"},
        headers=_token(client, "admin", "admin123"),
    )
    assert r.status_code == 201
