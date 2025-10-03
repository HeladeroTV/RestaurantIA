from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# This assumes /seed has been called in another context. For isolation, we trigger a small seed here.

def _ensure_seed():
    client.post('/seed', json={'days': 2, 'locations': ['TestLocA']})


def test_cooccurrence_anchor():
    _ensure_seed()
    # Find a popular item via /recs/popular
    pop = client.get('/recs/popular?top_k=1').json()
    if not pop:
        # no data; skip
        return
    anchor_id = pop[0]['item_id']
    r = client.get(f'/recs/cooccurrence?anchor_item_id={anchor_id}&top_k=5')
    assert r.status_code == 200
    data = r.json()
    # structure expectations
    if data:
        row = data[0]
        for k in ['item_id','name','co_orders','attach_rate','base_orders']:
            assert k in row
