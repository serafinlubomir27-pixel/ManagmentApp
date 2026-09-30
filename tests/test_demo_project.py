"""Ukážkový projekt pre uvedenie do nástroja.

Sieť sa zakladá jedným volaním zámerne — z prehliadača to bolo trinásť volaní
za sebou a každé spúšťalo vlastný CPM prepočet.
"""
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main

client = TestClient(main.app)


def _admin():
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_demo_project_has_computed_critical_path():
    h = _admin()
    r = client.post("/projects/demo", headers=h)
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    tasks = {t["name"]: t for t in client.get(f"/projects/{pid}/tasks", headers=h).json()}
    assert len(tasks) == 6

    # Kritická cesta: Zber (4) → Návrh (6) → Implementácia (9) → Odovzdanie (2) = 21 dní
    assert tasks["Zber požiadaviek"]["ef"] == 4
    assert tasks["Implementácia"]["ef"] == 19
    assert tasks["Odovzdanie"]["ef"] == 21

    kriticke = {n for n, t in tasks.items() if t["is_critical"]}
    assert kriticke == {"Zber požiadaviek", "Návrh riešenia", "Implementácia", "Odovzdanie"}

    # Kratšia vetva musí mať rezervu, inak by ukážka nemala čo ukázať.
    assert tasks["Nákup vybavenia"]["total_float"] > 0
    assert tasks["Zaškolenie používateľov"]["total_float"] > 0


def test_demo_project_is_pert_ready():
    """Zmysel ukážky je, že hneď vidno aj PERT — nie prázdnu záložku."""
    h = _admin()
    pid = client.post("/projects/demo", headers=h).json()["id"]

    for t in client.get(f"/projects/{pid}/tasks", headers=h).json():
        assert t["duration_optimistic"] is not None, f"{t['name']} nemá odhad a"
        assert t["duration_pessimistic"] is not None, f"{t['name']} nemá odhad b"

    pert = client.get(f"/projects/{pid}/pert", headers=h).json()
    assert pert["project_expected_duration"] > 0
    assert pert["project_std_dev"] > 0


def test_demo_project_counts_towards_plan_limit():
    """Ukážka je bežný projekt — nesmie obchádzať limit plánu (free = 2)."""
    r = client.post("/auth/signup", json={
        "email": "demo.limit@acme.sk", "password": "superheslo1",
        "full_name": "Owner", "organization_name": "DemoLimitOrg",
    })
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}

    assert client.post("/projects/demo", headers=h).status_code == 201
    assert client.post("/projects/", json={"name": "P2"}, headers=h).status_code == 201

    # tretí prekročí free limit — aj keď je to ukážka
    assert client.post("/projects/demo", headers=h).status_code == 402


def test_demo_project_requires_manager_or_admin():
    r = client.post("/auth/signup", json={
        "email": "demo.role@acme.sk", "password": "superheslo1",
        "full_name": "Owner", "organization_name": "DemoRoleOrg",
    })
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    # zakladateľ organizácie je admin → smie
    assert client.post("/projects/demo", headers=h).status_code == 201
