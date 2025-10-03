import json
from datetime import datetime
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_forecast_endpoint_basic():
    # Force train first (idempotent)
    r_train = client.post("/forecast/train?horizon_hours=6")
    assert r_train.status_code == 200, r_train.text
    resp = client.get("/forecast?horizon_hours=6")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["horizon_hours"] == 6
    assert len(data["points"]) == 6
    timestamps = [datetime.fromisoformat(p["ts"].replace("Z", "")) for p in data["points"]]
    assert timestamps == sorted(timestamps)
    for p in data["points"]:
        assert p["covers_pred"] >= 0
