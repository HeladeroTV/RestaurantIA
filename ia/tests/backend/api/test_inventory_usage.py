from fastapi.testclient import TestClient
from datetime import date, timedelta
from backend.app.main import app

client = TestClient(app)


def test_inventory_usage_flow():
    # Seed data (small window)
    client.post('/seed', json={'days': 1, 'locations': ['InvLoc']})
    today = date.today().isoformat()
    r = client.get(f'/inventory/usage?start={today}&end={today}')
    assert r.status_code == 200
    data = r.json()
    # Should have usage for some ingredients
    if data:
        first = data[0]
        for k in ['ingredient','unit','used']:
            assert k in first
