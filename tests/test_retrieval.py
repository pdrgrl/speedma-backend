import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_query_basic():
    resp = client.post("/query", json={"query": "What is the Tudor battery bank?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["sources"]) > 0
    assert len(data["follow_ups"]) <= 3


def test_query_with_focus():
    resp = client.post("/query", json={
        "query": "How does the marble control board switch the final 20 cells?",
        "focus_component": "marble_control_board",
        "scenario_id": "A",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"]


def test_retrieval_precision():
    """Heuristic: answer about Tudor cells should cite battery_manual source."""
    resp = client.post("/query", json={
        "query": "What is the electrolyte in the Tudor cells?",
        "focus_component": "tudor_battery_bank",
    })
    data = resp.json()
    source_types = [s["source_type"] for s in data["sources"]]
    # At least one retrieved chunk should be from the battery manual
    assert "battery_manual" in source_types, (
        f"Expected battery_manual in sources, got: {source_types}"
    )


def test_empty_query_rejected():
    resp = client.post("/query", json={"query": "  "})
    assert resp.status_code == 422