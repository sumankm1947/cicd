"""API tests using Flask's built-in test client (no running server needed)."""
import pytest

from app.api import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_calculate_add(client):
    resp = client.post("/calculate", json={"op": "add", "a": 2, "b": 3})
    assert resp.status_code == 200
    assert resp.get_json()["result"] == 5


def test_calculate_divide_by_zero(client):
    resp = client.post("/calculate", json={"op": "divide", "a": 1, "b": 0})
    assert resp.status_code == 400
    assert "zero" in resp.get_json()["error"].lower()


def test_calculate_bad_op(client):
    resp = client.post("/calculate", json={"op": "power", "a": 2, "b": 3})
    assert resp.status_code == 400
