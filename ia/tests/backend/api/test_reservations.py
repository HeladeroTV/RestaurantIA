from fastapi.testclient import TestClient
from backend.app.main import app
from datetime import datetime, timedelta

client = TestClient(app)


def test_availability_and_reservation_flow():
    when = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0).isoformat()
    # Check availability
    r_av = client.get(f"/availability?when={when}&party_size=4")
    assert r_av.status_code == 200
    av_data = r_av.json()
    assert "available" in av_data and "table_id" in av_data

    # Create reservation
    r_res = client.post("/reservations", json={
        "when": when,
        "party_size": 4,
        "customer_name": "Test User",
        "phone": "+123456789"
    })
    assert r_res.status_code == 200
    res_data = r_res.json()
    assert res_data["id"].startswith("r_")
    rid = res_data["id"]

    # Retrieve reservation
    r_get = client.get(f"/reservations/{rid}")
    assert r_get.status_code == 200
    get_data = r_get.json()
    assert get_data["party_size"] == 4
