"""
API smoke tests using httpx + pytest-asyncio.
These tests require a running PostgreSQL instance. See AGENTS.md for how to run.
"""
import pytest
import pytest_asyncio
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as c:
        yield c


def test_health(client: httpx.Client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_stats(client: httpx.Client):
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_sources" in data
    assert "total_signals" in data
    assert "total_entities" in data
    assert "total_relations" in data


def test_sources_list(client: httpx.Client):
    r = client.get("/api/sources")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_source_create_and_delete(client: httpx.Client):
    payload = {"name": "Test Source CI", "source_type": "person", "activity_status": "unknown"}
    r = client.post("/api/sources", json=payload)
    assert r.status_code == 201
    sid = r.json()["id"]

    r2 = client.get(f"/api/sources/{sid}")
    assert r2.status_code == 200
    assert r2.json()["name"] == "Test Source CI"

    r3 = client.delete(f"/api/sources/{sid}")
    assert r3.status_code == 204


def test_signals_list(client: httpx.Client):
    r = client.get("/api/signals")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_signal_create(client: httpx.Client):
    payload = {"title": "Test Signal", "url": "https://example.com/test-signal-ci", "signal_type": "blog"}
    r = client.post("/api/signals", json=payload)
    assert r.status_code == 201
    assert r.json()["title"] == "Test Signal"


def test_entities_list(client: httpx.Client):
    r = client.get("/api/entities")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_entity_create(client: httpx.Client):
    payload = {"name": "TestEntityCI", "canonical_name": "TestEntityCI", "entity_type": "topic", "metadata": {}}
    r = client.post("/api/entities", json=payload)
    assert r.status_code == 201
    eid = r.json()["id"]

    r2 = client.get(f"/api/wiki/entities/{eid}")
    assert r2.status_code == 200
    assert r2.json()["entity"]["name"] == "TestEntityCI"


def test_search(client: httpx.Client):
    r = client.get("/api/search?q=xAI")
    assert r.status_code == 200
    data = r.json()
    assert "entities" in data
    assert "signals" in data
    assert "sources" in data


def test_pipeline_runs(client: httpx.Client):
    r = client.get("/api/runs")
    assert r.status_code == 200

    mock_payload = {"run_type": "collect", "status": "success", "total_items": 10, "success_items": 10, "metadata": {}}
    r2 = client.post("/api/runs/mock", json=mock_payload)
    assert r2.status_code == 201


def test_entity_relation_invalid_type(client: httpx.Client):
    payload = {
        "name": "RelTestEntity", "canonical_name": "RelTestEntityCI",
        "entity_type": "topic", "metadata": {},
    }
    r = client.post("/api/entities", json=payload)
    assert r.status_code == 201
    eid = r.json()["id"]

    rel_payload = {
        "subject_entity_id": eid,
        "relation_type": "INVALID_TYPE_XYZ",
        "object_entity_id": eid,
    }
    r2 = client.post(f"/api/entities/{eid}/relations", json=rel_payload)
    assert r2.status_code == 422
