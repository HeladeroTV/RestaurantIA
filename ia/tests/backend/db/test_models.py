from fastapi.testclient import TestClient
from backend.app.main import app, SessionLocal, Location, Order
from datetime import datetime

client = TestClient(app)


def test_db_order_model_flow():
    db = SessionLocal()
    try:
        loc = db.query(Location).filter(Location.name == "TestLoc").first()
        if not loc:
            loc = Location(name="TestLoc")
            db.add(loc)
            db.flush()
        order = Order(location_id=loc.id, covers=3, ts=datetime.utcnow())
        db.add(order)
        db.commit()
        assert order.id is not None
        fetched = db.query(Order).filter(Order.id == order.id).first()
        assert fetched is not None
        assert fetched.covers == 3
    finally:
        db.close()
