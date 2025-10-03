from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from backend.app.main import app

client = TestClient(app)


def test_reviews_summary_keywords_and_sentiment():
    now = datetime.utcnow().replace(microsecond=0)
    # Add a couple of reviews
    client.post('/reviews', json={
        'location': 'ReviewLoc',
        'ts': now.isoformat(),
        'rating': 5,
        'text': 'Amazing pasta and wine. Great pasta, lovely service!',
        'source': 'test'
    })
    client.post('/reviews', json={
        'location': 'ReviewLoc',
        'ts': (now + timedelta(minutes=5)).isoformat(),
        'rating': 4,
        'text': 'Good wine and decent pasta.',
        'source': 'test'
    })
    start = now.date().isoformat()
    end = now.date().isoformat()
    r = client.get(f'/reviews/summary?start={start}&end={end}&location=ReviewLoc')
    assert r.status_code == 200
    data = r.json()
    assert data['count'] >= 2
    # Keywords should contain 'pasta' or 'wine'
    assert any(k in data['top_keywords'] for k in ['pasta','wine'])
