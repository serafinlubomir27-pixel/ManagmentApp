"""Fáza 1 — testy dokončenia/korektnosti.

Najdôležitejší: test_cpm_actually_recalculates_via_api dokazuje, že CPM sa po
zmene úloh cez API reálne prepočíta (predtým `cpm_manager.recalculate` neexistovala
a AttributeError prehltlo tiché `except: pass`, takže es/ef/is_critical ostávali 0).
"""
import pytest
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main
from backend.routers.calendar_router import _build_ical

client = TestClient(main.app)


def _admin():
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── Kľúčové: CPM sa reálne prepočíta cez API ─────────────────────────────────

def test_cpm_actually_recalculates_via_api():
    h = _admin()
    pid = client.post("/projects/", json={"name": "CPM proj"}, headers=h).json()["id"]
    a = client.post(f"/projects/{pid}/tasks", json={"name": "A", "duration": 3}, headers=h).json()["id"]
    b = client.post(f"/projects/{pid}/tasks", json={"name": "B", "duration": 4}, headers=h).json()["id"]

    r = client.post(f"/tasks/{b}/dependencies", params={"depends_on": a}, headers=h)
    assert r.status_code == 201, r.text

    tasks = client.get(f"/projects/{pid}/tasks", headers=h).json()
    by_id = {t["id"]: t for t in tasks}

    # A: es=0 ef=3 ; B (závisí od A): es=3 ef=7 ; obe na kritickej ceste
    assert by_id[a]["ef"] == 3, f"A.ef={by_id[a]['ef']} (CPM sa neprepočítal!)"
    assert by_id[b]["es"] == 3 and by_id[b]["ef"] == 7, f"B es/ef={by_id[b]['es']}/{by_id[b]['ef']}"
    assert by_id[b]["is_critical"]


# ── update_project — name/description už nie sú ignorované ────────────────────

def test_update_project_name_and_description():
    h = _admin()
    pid = client.post("/projects/", json={"name": "Staré", "description": "starý popis"}, headers=h).json()["id"]

    r = client.patch(f"/projects/{pid}", json={"name": "Nové meno", "description": "nový popis"}, headers=h)
    assert r.status_code == 200

    p = client.get(f"/projects/{pid}", headers=h).json()
    assert p["name"] == "Nové meno"
    assert p["description"] == "nový popis"


# ── check-deadlines je obmedzené na manager/admin ────────────────────────────

def test_check_deadlines_requires_manager():
    h = _admin()
    client.post("/auth/register",
        json={"username": "emp_cd", "password": "pw123456", "full_name": "E", "role": "employee"},
        headers=h)
    er = client.post("/auth/login", data={"username": "emp_cd", "password": "pw123456"})
    emp = {"Authorization": f"Bearer {er.json()['access_token']}"}

    assert client.post("/notifications/check-deadlines", headers=emp).status_code == 403
    assert client.post("/notifications/check-deadlines", headers=h).status_code == 200


# ── DELETE /projects — zmaže projekt aj jeho úlohy (cascade) ─────────────────

def test_delete_project_cascades():
    h = _admin()
    pid = client.post("/projects/", json={"name": "Na zmazanie"}, headers=h).json()["id"]
    tid = client.post(f"/projects/{pid}/tasks", json={"name": "T", "duration": 2}, headers=h).json()["id"]
    client.post(f"/tasks/{tid}/comments", json={"content": "ahoj"}, headers=h)

    r = client.delete(f"/projects/{pid}", headers=h)
    assert r.status_code == 204

    assert client.get(f"/projects/{pid}", headers=h).status_code == 404   # projekt preč
    assert client.get(f"/tasks/{tid}", headers=h).status_code == 404      # úloha tiež (cascade)


# ── Manuálny prepočet CPM ────────────────────────────────────────────────────

def test_recalculate_cpm_endpoint():
    h = _admin()
    pid = client.post("/projects/", json={"name": "Recalc proj"}, headers=h).json()["id"]
    a = client.post(f"/projects/{pid}/tasks", json={"name": "A", "duration": 3}, headers=h).json()["id"]
    b = client.post(f"/projects/{pid}/tasks", json={"name": "B", "duration": 4}, headers=h).json()["id"]
    client.post(f"/tasks/{b}/dependencies", params={"depends_on": a}, headers=h)

    r = client.post(f"/projects/{pid}/recalculate-cpm", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["project_duration"] == 7   # A(3) → B(4)
    assert body["critical_tasks"] >= 1


# ── iCal DTEND — +1 deň aj cez koniec mesiaca (predtým bugnuté pre deň ≥ 28) ──

def test_ical_dtend_next_day_month_end():
    ics = _build_ical([{
        "id": 1, "due_date": "2026-05-28", "name": "X",
        "status": "pending", "priority": "medium", "project_name": "P",
    }])
    assert "DTSTART;VALUE=DATE:20260528" in ics
    assert "DTEND;VALUE=DATE:20260529" in ics   # +1 deň (starý kód dával 20260601)
