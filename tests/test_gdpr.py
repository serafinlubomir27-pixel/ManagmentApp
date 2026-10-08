"""GDPR práva dotknutej osoby — export dát + zmazanie organizácie."""
import pytest
from fastapi.testclient import TestClient

import backend.main as main
from repositories.base_repo import get_connection

client = TestClient(main.app)


def _signup(email: str, org: str):
    r = client.post("/auth/signup", json={
        "email": email, "password": "superheslo1", "full_name": "Owner", "organization_name": org,
    })
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _count(sql: str, params=()) -> int:
    conn = get_connection()
    try:
        return conn.execute(sql, params).fetchone()["c"]
    finally:
        conn.close()


# ── Export ────────────────────────────────────────────────────────────────

def test_export_returns_org_data_without_passwords():
    h = _signup("gdpr1@acme.sk", "GdprOrg1")
    client.post("/projects/", json={"name": "P1"}, headers=h)

    data = client.get("/organization/export", headers=h).json()
    assert data["organization"]["name"] == "GdprOrg1"
    assert len(data["users"]) == 1
    assert "password" not in data["users"][0]        # heslá sa neexportujú
    assert len(data["projects"]) == 1
    assert "clients" in data and "tasks" in data      # kompletná štruktúra


# ── Zmazanie ──────────────────────────────────────────────────────────────

def test_delete_requires_matching_confirmation():
    h = _signup("gdpr2@acme.sk", "GdprOrg2")
    r = client.post("/organization/delete", json={"confirm": "nesprávne"}, headers=h)
    assert r.status_code == 400


def test_delete_removes_all_org_data():
    h = _signup("gdpr3@acme.sk", "GdprOrg3")
    pid = client.post("/projects/", json={"name": "P1"}, headers=h).json()["id"]
    client.post(f"/projects/{pid}/tasks", json={"name": "T", "duration": 2}, headers=h)

    assert _count("SELECT count(*) c FROM organizations WHERE name = ?", ("GdprOrg3",)) == 1

    r = client.post("/organization/delete", json={"confirm": "GdprOrg3"}, headers=h)
    assert r.status_code == 200

    # organizácia, jej používatelia aj projekty sú preč
    assert _count("SELECT count(*) c FROM organizations WHERE name = ?", ("GdprOrg3",)) == 0
    assert _count("SELECT count(*) c FROM users WHERE email = ?", ("gdpr3@acme.sk",)) == 0


def test_delete_removes_crm_data_of_clients():
    """Regresia: CRM tabuľky odkazujú na users, takže musia zmiznúť pred nimi.

    Bez toho PostgreSQL zmazanie používateľa odmietne pre porušenie cudzieho
    kľúča a právo na výmaz by sa nedalo uplatniť.
    """
    h = _signup("gdpr.crm@acme.sk", "GdprCrmOrg")
    cid = client.post("/clients/", json={"name": "Klient s CRM"}, headers=h).json()["id"]

    client.post(f"/clients/{cid}/activities",
                json={"activity_type": "call", "subject": "hovor"}, headers=h)
    client.post(f"/clients/{cid}/tasks", json={"title": "follow-up"}, headers=h)
    client.patch(f"/clients/{cid}/pipeline", json={"stage": "contact"}, headers=h)

    assert _count("SELECT COUNT(*) AS c FROM client_activities WHERE client_id = ?", (cid,)) > 0
    assert _count("SELECT COUNT(*) AS c FROM client_tasks WHERE client_id = ?", (cid,)) == 1
    assert _count("SELECT COUNT(*) AS c FROM deal_stage_history WHERE client_id = ?", (cid,)) == 1

    r = client.post("/organization/delete", json={"confirm": "GdprCrmOrg"}, headers=h)
    assert r.status_code == 200, r.text

    for table in ("client_activities", "client_tasks", "deal_stage_history"):
        assert _count(f"SELECT COUNT(*) AS c FROM {table} WHERE client_id = ?", (cid,)) == 0, \
            f"{table} po zmazaní organizácie nezostáva prázdna"


def test_erasure_removes_task_groups():
    """Etapy sú viazané na projekt — pri výmaze organizácie musia zmiznúť tiež.

    Rovnaká pasca ako pri CRM tabuľkách: tasks.group_id na ne odkazuje, takže
    nesprávne poradie by PostgreSQL odmietol a právo na výmaz by prestalo fungovať.
    """
    h = _signup("gdpr.groups@acme.sk", "GdprGroupsOrg")
    pid = client.post("/projects/", json={"name": "S etapami"}, headers=h).json()["id"]
    tid = client.post(f"/projects/{pid}/tasks", json={"name": "A", "duration": 2},
                      headers=h).json()["id"]
    gid = client.post(f"/projects/{pid}/groups",
                      json={"name": "Etapa", "task_ids": [tid]}, headers=h).json()["id"]

    assert _count("SELECT COUNT(*) AS c FROM task_groups WHERE id = ?", (gid,)) == 1

    r = client.post("/organization/delete", json={"confirm": "GdprGroupsOrg"}, headers=h)
    assert r.status_code in (200, 204), r.text

    assert _count("SELECT COUNT(*) AS c FROM task_groups WHERE id = ?", (gid,)) == 0,         "etapa prežila výmaz organizácie"
