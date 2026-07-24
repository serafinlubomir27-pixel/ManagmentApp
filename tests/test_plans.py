"""M3 — testy vynútenia limitov cenového plánu.

Free plán: 2 projekty, 5 používateľov. Prekročenie → 402 (Payment Required).

Spustenie:
    py -m pytest tests/test_plans.py -v
"""
import pytest
from fastapi.testclient import TestClient

import backend.main as main
from logic import plans

client = TestClient(main.app)


def _signup(email: str, org: str):
    r = client.post("/auth/signup", json={
        "email": email, "password": "superheslo1", "full_name": "Owner", "organization_name": org,
    })
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_plan_limits_config():
    assert plans.project_limit("free") == 2
    assert plans.project_limit("team") is None
    assert plans.can_add_project("free", 1) is True
    assert plans.can_add_project("free", 2) is False
    assert plans.can_add_project("team", 999) is True


def test_free_plan_blocks_third_project():
    h = _signup("plan1@acme.sk", "PlanOrg1")
    assert client.post("/projects/", json={"name": "P1"}, headers=h).status_code == 201
    assert client.post("/projects/", json={"name": "P2"}, headers=h).status_code == 201
    # tretí projekt prekročí free limit
    r = client.post("/projects/", json={"name": "P3"}, headers=h)
    assert r.status_code == 402, r.text


def test_upgrade_lifts_project_limit():
    h = _signup("plan2@acme.sk", "PlanOrg2")
    client.post("/projects/", json={"name": "P1"}, headers=h)
    client.post("/projects/", json={"name": "P2"}, headers=h)
    assert client.post("/projects/", json={"name": "P3"}, headers=h).status_code == 402

    # upgrade na team → limit zmizne
    assert client.patch("/organization/plan", json={"plan": "team"}, headers=h).status_code == 200
    assert client.post("/projects/", json={"name": "P3"}, headers=h).status_code == 201


def test_organization_usage_endpoint():
    h = _signup("plan3@acme.sk", "PlanOrg3")
    client.post("/projects/", json={"name": "P1"}, headers=h)
    data = client.get("/organization", headers=h).json()
    assert data["plan"] == "free"
    assert data["limits"]["max_projects"] == 2
    assert data["usage"]["projects"] == 1
    assert data["usage"]["users"] == 1  # len owner


def test_free_plan_blocks_sixth_user():
    h = _signup("plan4@acme.sk", "PlanOrg4")
    # org už má 1 používateľa (owner); pridaj 4 → spolu 5 (limit), 5. pridanie zlyhá
    for i in range(4):
        r = client.post("/auth/register",
            json={"username": f"u{i}_p4", "password": "pw123456", "full_name": f"U{i}", "role": "employee"},
            headers=h)
        assert r.status_code == 201, r.text
    r = client.post("/auth/register",
        json={"username": "u5_p4", "password": "pw123456", "full_name": "U5", "role": "employee"},
        headers=h)
    assert r.status_code == 402
