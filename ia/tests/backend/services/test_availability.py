from fastapi.testclient import TestClient
from backend.app.main import app
from datetime import datetime, timedelta

client = TestClient(app)


def test_availability_basic():
    when = (datetime.utcnow() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0).isoformat()
    r = client.get(f"/availability?when={when}&party_size=2")
    assert r.status_code == 200
    data = r.json()
    assert "available" in data


def test_availability_high_party_size():
    when = (datetime.utcnow() + timedelta(days=3)).replace(minute=0, second=0, microsecond=0).isoformat()
    r = client.get(f"/availability?when={when}&party_size=20")
    # Expect available false because no table has capacity 20
    assert r.status_code == 200
    data = r.json()
    assert data["available"] is False
