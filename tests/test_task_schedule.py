"""Úprava trvania úlohy — prepočet a validácia.

Trvanie sa dalo nastaviť len pri vytvorení úlohy; detail úlohy ho ukazoval
len na čítanie. Pre CPM nástroj to znamenalo, že sa nedalo vyskúšať to hlavné
— čo urobí s termínom, keď sa úloha natiahne.
"""
import hashlib

import pytest
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main
from repositories import user_repo, org_repo


def _sha(pwd: str) -> str:
    """Legacy SHA-256 tvar — login ho pri prvom použití prehashuje na bcrypt."""
    return hashlib.sha256(pwd.encode()).hexdigest()

client = TestClient(main.app)


def _admin():
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _chain(h, name="Harmonogram"):
    """Projekt s A → B, obe na kritickej ceste."""
    pid = client.post("/projects/", json={"name": name}, headers=h).json()["id"]
    a = client.post(f"/projects/{pid}/tasks", json={"name": "A", "duration": 3},
                    headers=h).json()["id"]
    b = client.post(f"/projects/{pid}/tasks", json={"name": "B", "duration": 4},
                    headers=h).json()["id"]
    client.post(f"/tasks/{b}/dependencies", params={"depends_on": a}, headers=h)
    return pid, a, b


def _tasks(h, pid):
    return {t["id"]: t for t in client.get(f"/projects/{pid}/tasks", headers=h).json()}


# ── Prepočet ────────────────────────────────────────────────────────────────

def test_duration_change_recalculates_cpm():
    h = _admin()
    pid, a, b = _chain(h)

    before = _tasks(h, pid)
    assert before[b]["es"] == 3 and before[b]["ef"] == 7

    r = client.patch(f"/tasks/{a}", json={"duration": 10}, headers=h)
    assert r.status_code == 200, r.text

    after = _tasks(h, pid)
    assert after[a]["ef"] == 10, "trvanie sa zmenilo, ale EF ostalo staré"
    assert after[b]["es"] == 10 and after[b]["ef"] == 14, "nadväzujúca úloha sa neposunula"


def test_duration_change_shifts_critical_path():
    """Predĺženie paralelnej vetvy musí prehodiť, ktoré úlohy sú kritické."""
    h = _admin()
    pid = client.post("/projects/", json={"name": "Dve vetvy"}, headers=h).json()["id"]
    start = client.post(f"/projects/{pid}/tasks", json={"name": "Štart", "duration": 1},
                        headers=h).json()["id"]
    dlha = client.post(f"/projects/{pid}/tasks", json={"name": "Dlhá", "duration": 10},
                       headers=h).json()["id"]
    kratka = client.post(f"/projects/{pid}/tasks", json={"name": "Krátka", "duration": 2},
                         headers=h).json()["id"]
    for t in (dlha, kratka):
        client.post(f"/tasks/{t}/dependencies", params={"depends_on": start}, headers=h)

    before = _tasks(h, pid)
    assert before[dlha]["is_critical"]
    assert not before[kratka]["is_critical"]

    # Krátka vetva sa natiahne nad dlhú → kritická cesta sa musí prehodiť.
    client.patch(f"/tasks/{kratka}", json={"duration": 20}, headers=h)

    after = _tasks(h, pid)
    assert after[kratka]["is_critical"], "predĺžená vetva sa nestala kritickou"
    assert not after[dlha]["is_critical"], "pôvodná vetva ostala kritická"
    assert after[dlha]["total_float"] == 10, f"rezerva sa neprepočítala: {after[dlha]['total_float']}"


def test_duration_change_updates_pert():
    """PERT sa počíta pri čítaní, takže musí odrážať nové trvanie okamžite."""
    h = _admin()
    pid = client.post("/projects/", json={"name": "PERT po zmene"}, headers=h).json()["id"]
    tid = client.post(f"/projects/{pid}/tasks", json={
        "name": "A", "duration": 4, "duration_optimistic": 2, "duration_pessimistic": 12,
    }, headers=h).json()["id"]

    # E = (2 + 16 + 12) / 6 = 5,0
    assert client.get(f"/projects/{pid}/pert", headers=h).json()["project_expected_duration"] == 5.0

    client.patch(f"/tasks/{tid}", json={"duration": 6}, headers=h)

    # E = (2 + 24 + 12) / 6 = 6,33
    assert client.get(f"/projects/{pid}/pert", headers=h).json()["project_expected_duration"] == 6.33


# ── Validácia ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("payload,fragment", [
    ({"duration": 0}, "aspoň 1"),
    ({"duration": -3}, "aspoň 1"),
    ({"duration_optimistic": 0}, "aspoň 1"),
    ({"duration_optimistic": 9, "duration_pessimistic": 2}, "väčší než pesimistický"),
])
def test_invalid_schedule_rejected(payload, fragment):
    h = _admin()
    pid, a, _ = _chain(h, "Validácia")
    r = client.patch(f"/tasks/{a}", json=payload, headers=h)
    assert r.status_code == 400, r.text
    assert fragment in r.json()["detail"]


def test_partial_update_validated_against_stored_values():
    """Poslať len pesimistický odhad sa musí porovnať s už uloženým trvaním."""
    h = _admin()
    pid = client.post("/projects/", json={"name": "Čiastočná zmena"}, headers=h).json()["id"]
    tid = client.post(f"/projects/{pid}/tasks", json={"name": "A", "duration": 8},
                      headers=h).json()["id"]

    # 5 < trvanie 8 → pesimistický odhad nemôže byť kratší než najpravdepodobnejší
    r = client.patch(f"/tasks/{tid}", json={"duration_pessimistic": 5}, headers=h)
    assert r.status_code == 400, r.text
    assert "menší než najpravdepodobnejšie" in r.json()["detail"]

    assert client.patch(f"/tasks/{tid}", json={"duration_pessimistic": 15},
                        headers=h).status_code == 200


def test_rejected_change_leaves_task_untouched():
    h = _admin()
    pid, a, _ = _chain(h, "Nezmenené po odmietnutí")
    client.patch(f"/tasks/{a}", json={"duration": 0}, headers=h)
    assert _tasks(h, pid)[a]["duration"] == 3


# ── Mazanie odhadov ─────────────────────────────────────────────────────────

def test_estimates_can_be_cleared():
    """`update_task_fields` zahadzuje None, takže bez clear_task_fields by sa
    odhad dal zapísať len raz a už nikdy odstrániť."""
    h = _admin()
    pid = client.post("/projects/", json={"name": "Mazanie odhadov"}, headers=h).json()["id"]
    tid = client.post(f"/projects/{pid}/tasks", json={
        "name": "A", "duration": 5, "duration_optimistic": 3, "duration_pessimistic": 9,
    }, headers=h).json()["id"]

    r = client.patch(f"/tasks/{tid}", json={"duration_optimistic": None}, headers=h)
    assert r.status_code == 200, r.text

    task = _tasks(h, pid)[tid]
    assert task["duration_optimistic"] is None, "odhad sa nedal zmazať"
    assert task["duration_pessimistic"] == 9, "zmazal sa aj druhý odhad"


# ── Oprávnenia ──────────────────────────────────────────────────────────────

def test_employee_cannot_change_duration():
    """Trvanie prepisuje harmonogram celého projektu, nielen vlastnú úlohu."""
    h = _admin()
    pid, a, _ = _chain(h, "Práva")

    org_id = org_repo.get_organization_by_slug("default")["id"]
    user_repo.create_user("dodo", _sha("pw"), "Dodo Zamestnanec", "employee", None, org_id)
    emp_id = {u["username"]: u["id"] for u in user_repo.get_all_users(org_id)}["dodo"]

    # Priradenie úlohy mu dá prístup k projektu — 403 nižšie teda príde
    # z kontroly roly, nie z prístupových práv.
    client.patch(f"/tasks/{a}", json={"assigned_to": emp_id}, headers=h)

    emp = client.post("/auth/login", data={"username": "dodo", "password": "pw"})
    assert emp.status_code == 200, emp.text
    eh = {"Authorization": f"Bearer {emp.json()['access_token']}"}

    r = client.patch(f"/tasks/{a}", json={"duration": 99}, headers=eh)
    assert r.status_code == 403, r.text
    assert _tasks(h, pid)[a]["duration"] == 3

    # Vlastný stav si meniť smie aj naďalej.
    assert client.patch(f"/tasks/{a}", json={"status": "in_progress"},
                        headers=eh).status_code == 200
