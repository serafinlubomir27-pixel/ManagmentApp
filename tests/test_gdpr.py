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
