"""CRM rozšírenie klientskeho modulu — história interakcií a úlohy ku klientovi.

Overuje, že sa interakcie zapisujú a radia od najnovšej, že úlohy ku klientovi
majú vlastný životný cyklus oddelený od projektových úloh a že posun obchodu
medzi fázami zanechá stopu.

Spustenie:
    py -m pytest tests/test_client_crm.py -v
"""
import pytest
from fastapi.testclient import TestClient

# DB + JWT kľúč pripraví conftest.py.
import backend.main as main

client = TestClient(main.app)


def _admin() -> dict:
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def klient():
    h = _admin()
    r = client.post("/clients/", json={"name": "Testovací klient", "email": "k@test.sk"}, headers=h)
    assert r.status_code == 201, r.text
    return r.json()["id"], h


# ── História interakcií ──────────────────────────────────────────────────────

def test_activity_is_recorded_and_listed(klient):
    cid, h = klient
    r = client.post(f"/clients/{cid}/activities",
                    json={"activity_type": "call", "subject": "Úvodný hovor",
                          "body": "Dohodnuté stretnutie"}, headers=h)
    assert r.status_code == 201, r.text

    items = client.get(f"/clients/{cid}/activities", headers=h).json()
    assert len(items) == 1
    assert items[0]["activity_type"] == "call"
    assert items[0]["subject"] == "Úvodný hovor"
    # Meno autora sa pripája joinom, aby sa v rozhraní nemuselo dopytovať zvlášť.
    assert items[0]["username"] == "admin"


def test_activities_are_ordered_newest_first(klient):
    cid, h = klient
    for subj, when in [("staršia", "2026-01-01 10:00:00"),
                       ("novšia", "2026-06-01 10:00:00")]:
        client.post(f"/clients/{cid}/activities",
                    json={"subject": subj, "occurred_at": when}, headers=h)

    items = client.get(f"/clients/{cid}/activities", headers=h).json()
    assert [i["subject"] for i in items] == ["novšia", "staršia"]


def test_unknown_activity_type_is_rejected(klient):
    cid, h = klient
    r = client.post(f"/clients/{cid}/activities",
                    json={"activity_type": "vymyslene"}, headers=h)
    assert r.status_code == 400


def test_activity_can_be_deleted(klient):
    cid, h = klient
    aid = client.post(f"/clients/{cid}/activities",
                      json={"subject": "na zmazanie"}, headers=h).json()["id"]
    assert client.delete(f"/clients/{cid}/activities/{aid}", headers=h).status_code == 204
    assert client.get(f"/clients/{cid}/activities", headers=h).json() == []


# ── Úlohy ku klientovi ───────────────────────────────────────────────────────

def test_client_task_lifecycle(klient):
    cid, h = klient
    tid = client.post(f"/clients/{cid}/tasks",
                      json={"title": "Zavolať klientovi", "due_date": "2026-12-01",
                            "priority": "high"}, headers=h).json()["id"]

    tasks = client.get(f"/clients/{cid}/tasks", headers=h).json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Zavolať klientovi"
    assert not tasks[0]["done"]

    assert client.patch(f"/clients/{cid}/tasks/{tid}", json={"done": True},
                        headers=h).status_code == 200
    assert client.get(f"/clients/{cid}/tasks", headers=h).json()[0]["done"]

    # Označenie späť na nesplnené musí vyčistiť aj čas dokončenia.
    client.patch(f"/clients/{cid}/tasks/{tid}", json={"done": False}, headers=h)
    back = client.get(f"/clients/{cid}/tasks", headers=h).json()[0]
    assert not back["done"] and back["done_at"] is None

    assert client.delete(f"/clients/{cid}/tasks/{tid}", headers=h).status_code == 204
    assert client.get(f"/clients/{cid}/tasks", headers=h).json() == []


def test_empty_task_title_is_rejected(klient):
    cid, h = klient
    assert client.post(f"/clients/{cid}/tasks", json={"title": "   "}, headers=h).status_code == 400


def test_upcoming_tasks_skip_completed_ones(klient):
    cid, h = klient
    done = client.post(f"/clients/{cid}/tasks", json={"title": "hotová"}, headers=h).json()["id"]
    client.post(f"/clients/{cid}/tasks", json={"title": "otvorená"}, headers=h)
    client.patch(f"/clients/{cid}/tasks/{done}", json={"done": True}, headers=h)

    upcoming = client.get("/clients/tasks/upcoming", headers=h).json()
    titles = [t["title"] for t in upcoming if t["client_id"] == cid]
    assert titles == ["otvorená"]
    assert upcoming[0]["client_name"] == "Testovací klient"


# ── História posunov obchodu ─────────────────────────────────────────────────

def test_stage_change_is_recorded(klient):
    cid, h = klient
    client.patch(f"/clients/{cid}/pipeline", json={"stage": "contact"}, headers=h)
    client.patch(f"/clients/{cid}/pipeline", json={"stage": "proposal"}, headers=h)

    history = client.get(f"/clients/{cid}/stage-history", headers=h).json()
    assert len(history) == 2
    assert history[0]["to_stage"] == "proposal"
    assert history[0]["from_stage"] == "contact"

    # Posun sa má objaviť aj na časovej osi, nech je všetko na jednom mieste.
    subjects = [a["subject"] for a in client.get(f"/clients/{cid}/activities", headers=h).json()]
    assert subjects.count("Zmena fázy obchodu") == 2


def test_same_stage_twice_does_not_duplicate_history(klient):
    cid, h = klient
    client.patch(f"/clients/{cid}/pipeline", json={"stage": "contact"}, headers=h)
    client.patch(f"/clients/{cid}/pipeline", json={"stage": "contact", "deal_value": 500},
                 headers=h)

    assert len(client.get(f"/clients/{cid}/stage-history", headers=h).json()) == 1


# ── Prístupové práva ─────────────────────────────────────────────────────────

def test_crm_endpoints_require_authentication(klient):
    cid, _ = klient
    assert client.get(f"/clients/{cid}/activities").status_code == 401
    assert client.get(f"/clients/{cid}/tasks").status_code == 401
    assert client.get(f"/clients/{cid}/stage-history").status_code == 401
