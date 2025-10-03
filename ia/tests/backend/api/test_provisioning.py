from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import SessionLocal
from backend.app.db import models

client = TestClient(app)

def test_basic_provision_flow():
    # Create tenant
    r_tenant = client.post('/tenants', json={'name':'ProvTenant','timezone':'UTC','currency':'USD'})
    assert r_tenant.status_code == 200
    tenant_id = r_tenant.json()['id']

    # Run provisioning with templates
    payload = {
        "menu_template": "menu_italian_modern_v1",
        "floorplan_template": "floorplan_small_60_seats",
        "governance": {"retention_days": {"orders": 730, "reviews": 365, "customers": 1095}}
    }
    r_prov = client.post(f'/provision/{tenant_id}', json=payload, headers={'X-Tenant-ID': str(tenant_id)})
    assert r_prov.status_code == 200, r_prov.text
    data = r_prov.json()
    assert data['status'] == 'completed'

    # Validate tables created
    db = SessionLocal()
    try:
        tables = db.query(models.DiningTable).filter(models.DiningTable.tenant_id == tenant_id).all()
        assert len(tables) > 0
    finally:
        db.close()
