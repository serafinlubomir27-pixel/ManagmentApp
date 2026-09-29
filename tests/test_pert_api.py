"""PERT cez API — odhady zadané pri VYTVORENÍ úlohy sa musia uložiť.

`TaskCreate` prijímal duration_optimistic/duration_pessimistic, ale `create_task`
ich nezapisoval do `update_task_fields`, takže sa ticho zahodili. Formulár na
vytvorenie úlohy ich pritom posiela — používateľ ich vyplnil, uložil a záložka
PERT potom hlásila, že žiadna úloha odhady nemá.
"""
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main

client = TestClient(main.app)


def _admin():
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_pert_estimates_persist_on_create():
    h = _admin()
    pid = client.post("/projects/", json={"name": "PERT create"}, headers=h).json()["id"]

    tid = client.post(f"/projects/{pid}/tasks", json={
        "name": "A", "duration": 5,
        "duration_optimistic": 3, "duration_pessimistic": 9,
    }, headers=h).json()["id"]

    task = next(t for t in client.get(f"/projects/{pid}/tasks", headers=h).json()
                if t["id"] == tid)
    assert task["duration_optimistic"] == 3, "optimistický odhad sa zahodil"
    assert task["duration_pessimistic"] == 9, "pesimistický odhad sa zahodil"


def test_pert_analysis_uses_estimates_from_create():
    """Bez uloženia odhadov vracal /pert expected_duration = None."""
    h = _admin()
    pid = client.post("/projects/", json={"name": "PERT analýza"}, headers=h).json()["id"]

    a = client.post(f"/projects/{pid}/tasks", json={
        "name": "A", "duration": 4, "duration_optimistic": 2, "duration_pessimistic": 12,
    }, headers=h).json()["id"]
    b = client.post(f"/projects/{pid}/tasks", json={
        "name": "B", "duration": 6, "duration_optimistic": 4, "duration_pessimistic": 14,
    }, headers=h).json()["id"]
    client.post(f"/tasks/{b}/dependencies", params={"depends_on": a}, headers=h)

    body = client.get(f"/projects/{pid}/pert", headers=h).json()

    # E = (a + 4m + b) / 6  →  A: (2+16+12)/6 = 5,0 ; B: (4+24+14)/6 = 7,0
    by_id = {t["task_id"]: t for t in body["pert_tasks"]}
    assert by_id[a]["pert_expected"] == 5.0
    assert by_id[b]["pert_expected"] == 7.0

    # A → B je jediná cesta, takže očakávané trvanie projektu je 12,0
    assert body["project_expected_duration"] == 12.0

    # σ = (b − a) / 6 → A aj B: 10/6 ; rozptyl sa sčítava po kritickej ceste
    assert body["project_std_dev"] > 0, "σ ostalo nulové — odhady sa nepoužili"


def test_task_without_estimates_stays_none():
    """Úloha bez odhadov ich nesmie dostať vymyslené."""
    h = _admin()
    pid = client.post("/projects/", json={"name": "Bez odhadov"}, headers=h).json()["id"]
    tid = client.post(f"/projects/{pid}/tasks", json={"name": "A", "duration": 5},
                      headers=h).json()["id"]

    task = next(t for t in client.get(f"/projects/{pid}/tasks", headers=h).json()
                if t["id"] == tid)
    assert task["duration_optimistic"] is None
    assert task["duration_pessimistic"] is None
