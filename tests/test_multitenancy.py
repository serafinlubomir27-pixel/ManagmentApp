"""M1 — testy izolácie organizácií (multi-tenancy).

Overujú, že používateľ jednej organizácie sa nedostane k dátam inej — ani priamo cez ID.
Cross-org prístup musí vrátiť **404** (nie 403), aby neprezradil, že objekt v cudzej
organizácii vôbec existuje.

Pozor: admin je admin SVOJEJ organizácie, nie globálny — preto sú tieto testy vedené
pod adminom, kde je riziko úniku najvyššie.

Spustenie:
    py -m pytest tests/test_multitenancy.py -v
"""
import hashlib

import pytest
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main
from repositories import user_repo, project_repo, task_repo, client_repo, org_repo

client = TestClient(main.app)


def _sha(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


@pytest.fixture(scope="module")
def orgs():
    """Dve nezávislé organizácie, každá s adminom, projektom, úlohou a klientom."""
    data = {}
    for key, name in (("a", "Org A"), ("b", "Org B")):
        org_id = org_repo.create_organization(name, f"org-{key}-mt")
        user_repo.create_user(f"{key}_admin", _sha("pw"), f"{name} Admin", "admin", None, org_id)
        uid = user_repo.get_by_username(f"{key}_admin")["id"]
        pid = project_repo.create_project(uid, f"{name} projekt", "", org_id)
        tid = task_repo.create_task(
            project_id=pid, name=f"{name} uloha", assigned_to=uid, created_by=uid
        )
        cid = client_repo.create_client(f"{name} klient", advisor_id=uid, organization_id=org_id)
        data[key] = {"org_id": org_id, "uid": uid, "pid": pid, "tid": tid, "cid": cid}
    return data


def _token(username: str):
    r = client.post("/auth/login", data={"username": username, "password": "pw"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── Cross-org prístup cez priame ID → 404 ────────────────────────────────────

def test_can_read_own_org_project(orgs):
    assert client.get(f"/projects/{orgs['a']['pid']}", headers=_token("a_admin")).status_code == 200


def test_cannot_read_other_org_project(orgs):
    assert client.get(f"/projects/{orgs['b']['pid']}", headers=_token("a_admin")).status_code == 404


def test_cannot_list_other_org_tasks(orgs):
    r = client.get(f"/projects/{orgs['b']['pid']}/tasks", headers=_token("a_admin"))
    assert r.status_code == 404


def test_cannot_read_other_org_task(orgs):
    assert client.get(f"/tasks/{orgs['b']['tid']}", headers=_token("a_admin")).status_code == 404


def test_cannot_patch_other_org_task(orgs):
    r = client.patch(f"/tasks/{orgs['b']['tid']}", json={"status": "completed"}, headers=_token("a_admin"))
    assert r.status_code == 404


def test_cannot_delete_other_org_project(orgs):
    r = client.delete(f"/projects/{orgs['b']['pid']}", headers=_token("a_admin"))
    assert r.status_code == 404


def test_cannot_read_other_org_client(orgs):
    assert client.get(f"/clients/{orgs['b']['cid']}", headers=_token("a_admin")).status_code == 404


def test_cannot_patch_other_org_client(orgs):
    r = client.patch(f"/clients/{orgs['b']['cid']}", json={"name": "hacked"}, headers=_token("a_admin"))
    assert r.status_code == 404


def test_cannot_modify_other_org_user(orgs):
    r = client.patch(f"/team/{orgs['b']['uid']}", json={"role": "employee"}, headers=_token("a_admin"))
    assert r.status_code == 404


# ── Zoznamy vracajú výhradne vlastnú organizáciu ─────────────────────────────

def test_team_all_lists_only_own_org(orgs):
    users = client.get("/team/all", headers=_token("a_admin")).json()
    names = {u["username"] for u in users}
    assert "a_admin" in names
    assert "b_admin" not in names


def test_clients_list_only_own_org(orgs):
    names = {c["name"] for c in client.get("/clients/", headers=_token("a_admin")).json()}
    assert "Org A klient" in names
    assert "Org B klient" not in names


def test_projects_list_excludes_other_org(orgs):
    names = {p["name"] for p in client.get("/projects/", headers=_token("a_admin")).json()}
    assert "Org A projekt" in names
    assert "Org B projekt" not in names


# ── Pozvánka viaže nového používateľa na organizáciu tvorcu ──────────────────

def test_invite_binds_new_user_to_creator_org(orgs):
    h = _token("a_admin")
    token = client.post("/invites", json={"role": "employee"}, headers=h).json()["token"]

    r = client.post(
        f"/invites/{token}/accept",
        json={"username": "invited_mt", "password": "pw123456", "full_name": "Invited"},
    )
    assert r.status_code == 201

    invited = user_repo.get_by_username("invited_mt")
    assert invited["organization_id"] == orgs["a"]["org_id"]
