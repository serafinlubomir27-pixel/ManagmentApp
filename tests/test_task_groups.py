"""Etapy — zoskupenie úloh pre prehľad.

Kľúčová vlastnosť, ktorú tieto testy strážia: skupina NEVSTUPUJE do výpočtu
kritickej cesty. Keby sa raz niekto rozhodol dať jej vlastné trvanie alebo
závislosti, výpočet by prestal zodpovedať metóde a práca by stratila základ.
"""
import pytest
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main
from repositories import group_repo

client = TestClient(main.app)


def _admin():
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _project_with_chain(h, name="Etapy"):
    """A → B → C, všetky kritické."""
    pid = client.post("/projects/", json={"name": name}, headers=h).json()["id"]
    ids = []
    for n, dur in (("A", 3), ("B", 4), ("C", 2)):
        ids.append(client.post(f"/projects/{pid}/tasks",
                               json={"name": n, "duration": dur}, headers=h).json()["id"])
    client.post(f"/tasks/{ids[1]}/dependencies", params={"depends_on": ids[0]}, headers=h)
    client.post(f"/tasks/{ids[2]}/dependencies", params={"depends_on": ids[1]}, headers=h)
    return pid, ids


def _tasks(h, pid):
    return {t["id"]: t for t in client.get(f"/projects/{pid}/tasks", headers=h).json()}


# ── Základ ──────────────────────────────────────────────────────────────────

def test_create_group_with_tasks():
    h = _admin()
    pid, ids = _project_with_chain(h)

    r = client.post(f"/projects/{pid}/groups",
                    json={"name": "Príprava", "task_ids": ids[:2]}, headers=h)
    assert r.status_code == 201, r.text
    gid = r.json()["id"]

    groups = client.get(f"/projects/{pid}/groups", headers=h).json()
    assert len(groups) == 1
    g = groups[0]
    assert g["id"] == gid and g["name"] == "Príprava"
    assert g["total_tasks"] == 2 and g["completed_tasks"] == 0
    assert g["done"] is False

    tasks = _tasks(h, pid)
    assert tasks[ids[0]]["group_id"] == gid
    assert tasks[ids[2]]["group_id"] is None, "tretia úloha do etapy nepatrí"


def test_group_name_is_required():
    h = _admin()
    pid, _ = _project_with_chain(h, "Bez názvu")
    r = client.post(f"/projects/{pid}/groups", json={"name": "   "}, headers=h)
    assert r.status_code == 400


# ── Kľúčové: CPM sa etáp nedotýka ───────────────────────────────────────────

def test_grouping_does_not_change_schedule():
    """Zaradenie do etapy nesmie pohnúť ani jedným termínom."""
    h = _admin()
    pid, ids = _project_with_chain(h, "Harmonogram nedotknutý")

    before = _tasks(h, pid)
    snapshot = {i: (before[i]["es"], before[i]["ef"], before[i]["ls"],
                    before[i]["lf"], before[i]["total_float"], before[i]["is_critical"])
                for i in ids}

    client.post(f"/projects/{pid}/groups", json={"name": "Etapa 1", "task_ids": ids}, headers=h)

    after = _tasks(h, pid)
    for i in ids:
        assert (after[i]["es"], after[i]["ef"], after[i]["ls"], after[i]["lf"],
                after[i]["total_float"], after[i]["is_critical"]) == snapshot[i], \
            f"úloha {i}: etapa zmenila harmonogram"


def test_deleting_group_keeps_tasks_and_schedule():
    h = _admin()
    pid, ids = _project_with_chain(h, "Zrušenie etapy")
    gid = client.post(f"/projects/{pid}/groups",
                      json={"name": "Dočasná", "task_ids": ids}, headers=h).json()["id"]

    assert client.delete(f"/groups/{gid}", headers=h).status_code == 204

    tasks = _tasks(h, pid)
    assert len(tasks) == 3, "zrušenie etapy nesmie mazať úlohy"
    assert all(t["group_id"] is None for t in tasks.values())
    assert tasks[ids[2]]["ef"] == 9, "harmonogram sa zmenil po zrušení etapy"
    assert client.get(f"/projects/{pid}/groups", headers=h).json() == []


# ── Odvodený postup ─────────────────────────────────────────────────────────

def test_group_progress_follows_tasks():
    h = _admin()
    pid, ids = _project_with_chain(h, "Postup")
    gid = client.post(f"/projects/{pid}/groups",
                      json={"name": "Etapa", "task_ids": ids}, headers=h).json()["id"]

    def g():
        return next(x for x in client.get(f"/projects/{pid}/groups", headers=h).json()
                    if x["id"] == gid)

    assert g()["progress"] == 0.0 and g()["done"] is False

    client.patch(f"/tasks/{ids[0]}", json={"status": "completed"}, headers=h)
    assert g()["completed_tasks"] == 1
    assert g()["progress"] == pytest.approx(0.333, abs=0.001)
    assert g()["done"] is False

    for i in ids[1:]:
        client.patch(f"/tasks/{i}", json={"status": "completed"}, headers=h)

    # Posledná úloha zavrela etapu — presne to si používateľ predstaví.
    assert g()["done"] is True and g()["progress"] == 1.0


def test_empty_group_is_not_done():
    """Inak by sa etapa vyhlásila za hotovú hneď po založení."""
    h = _admin()
    pid, _ = _project_with_chain(h, "Prázdna etapa")
    gid = client.post(f"/projects/{pid}/groups", json={"name": "Prázdna"}, headers=h).json()["id"]
    g = next(x for x in client.get(f"/projects/{pid}/groups", headers=h).json() if x["id"] == gid)
    assert g["total_tasks"] == 0 and g["done"] is False


def test_group_span_comes_from_children():
    h = _admin()
    pid, ids = _project_with_chain(h, "Rozsah")
    gid = client.post(f"/projects/{pid}/groups",
                      json={"name": "Celá", "task_ids": ids}, headers=h).json()["id"]
    g = next(x for x in client.get(f"/projects/{pid}/groups", headers=h).json() if x["id"] == gid)
    # A: 0–3, B: 3–7, C: 7–9
    assert g["start_day"] == 0 and g["end_day"] == 9


# ── Presuny medzi etapami ───────────────────────────────────────────────────

def test_task_moves_between_groups():
    h = _admin()
    pid, ids = _project_with_chain(h, "Presun")
    g1 = client.post(f"/projects/{pid}/groups", json={"name": "Prvá", "task_ids": ids[:2]},
                     headers=h).json()["id"]
    g2 = client.post(f"/projects/{pid}/groups", json={"name": "Druhá"}, headers=h).json()["id"]

    client.post(f"/groups/{g2}/tasks", json={"task_ids": [ids[1]]}, headers=h)

    groups = {x["id"]: x for x in client.get(f"/projects/{pid}/groups", headers=h).json()}
    assert groups[g1]["total_tasks"] == 1
    assert groups[g2]["total_tasks"] == 1
    assert _tasks(h, pid)[ids[1]]["group_id"] == g2


def test_ungroup_tasks():
    h = _admin()
    pid, ids = _project_with_chain(h, "Vyradenie")
    gid = client.post(f"/projects/{pid}/groups", json={"name": "Etapa", "task_ids": ids},
                      headers=h).json()["id"]

    r = client.post(f"/projects/{pid}/groups/ungroup", json={"task_ids": ids[:2]}, headers=h)
    assert r.status_code == 200, r.text

    groups = client.get(f"/projects/{pid}/groups", headers=h).json()
    assert next(x for x in groups if x["id"] == gid)["total_tasks"] == 1


def test_cannot_pull_task_from_another_project():
    """Podstrčené ID z cudzieho projektu sa nesmie dostať do etapy."""
    h = _admin()
    pid_a, ids_a = _project_with_chain(h, "Projekt A")
    pid_b, ids_b = _project_with_chain(h, "Projekt B")

    gid = client.post(f"/projects/{pid_a}/groups", json={"name": "Etapa A"}, headers=h).json()["id"]
    client.post(f"/groups/{gid}/tasks", json={"task_ids": ids_b}, headers=h)

    assert _tasks(h, pid_b)[ids_b[0]]["group_id"] is None
    g = next(x for x in client.get(f"/projects/{pid_a}/groups", headers=h).json() if x["id"] == gid)
    assert g["total_tasks"] == 0


# ── Premenovanie a farba ────────────────────────────────────────────────────

def test_rename_and_recolor():
    h = _admin()
    pid, ids = _project_with_chain(h, "Premenovanie")
    gid = client.post(f"/projects/{pid}/groups", json={"name": "Stará"}, headers=h).json()["id"]

    assert client.patch(f"/groups/{gid}", json={"name": "Nová"}, headers=h).status_code == 200
    assert client.patch(f"/groups/{gid}", json={"color": "emerald"}, headers=h).status_code == 200
    assert client.patch(f"/groups/{gid}", json={"color": "duhova"}, headers=h).status_code == 400

    g = next(x for x in client.get(f"/projects/{pid}/groups", headers=h).json() if x["id"] == gid)
    assert g["name"] == "Nová" and g["color"] == "emerald"


def test_groups_get_distinct_colors():
    """Dve etapy v jednom projekte musia byť rozlíšiteľné."""
    h = _admin()
    pid, _ = _project_with_chain(h, "Farby")
    colors = []
    for n in ("Prvá", "Druhá", "Tretia"):
        client.post(f"/projects/{pid}/groups", json={"name": n}, headers=h)
    colors = [g["color"] for g in client.get(f"/projects/{pid}/groups", headers=h).json()]
    assert len(set(colors)) == 3, f"etapy dostali rovnakú farbu: {colors}"
    assert all(c in group_repo.PALETTE for c in colors)
