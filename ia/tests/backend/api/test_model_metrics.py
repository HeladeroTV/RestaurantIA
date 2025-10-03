from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_model_metrics_list():
    # Ensure a training run happens so metrics can appear
    client.post("/forecast/train?horizon_hours=4")
    r = client.get('/models/metrics')
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    # If metrics exist, structure check
    if data:
        row = data[0]
        for k in ["model_name", "version", "metric_name", "value", "created_at"]:
            assert k in row
