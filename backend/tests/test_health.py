from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings

client = TestClient(app)
settings = get_settings()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RecoveryPilot AI"
    assert data["status"] == "running"

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "recoverypilot-backend"
    assert data["version"] == settings.APP_VERSION
    assert data["environment"] == settings.APP_ENV
