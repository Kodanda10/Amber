import os
import importlib
import sys
from pathlib import Path
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Ensure the backend directory is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_admin_ping_unauthorized(client):
    """
    Tests that a request to a protected endpoint without a token returns 401.
    """
    response = client.get('/api/admin/ping')
    assert response.status_code == 401


def test_admin_ping_authorized(client, monkeypatch):
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    token = app_module.generate_admin_token("tester")
    response = client.get('/api/admin/ping', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'ok'
    assert payload['admin'] == 'tester'


def test_admin_token_issue_requires_valid_secret(client, monkeypatch):
    monkeypatch.setattr(app_module, "ADMIN_BOOTSTRAP_SECRET", "expected-secret")
    payload = {"adminId": "tester", "secret": "wrong"}
    response = client.post('/api/admin/token', json=payload)
    assert response.status_code == 401
    body = response.get_json()
    assert body["error"] == "unauthorized"


def test_admin_token_issue_returns_token(client, monkeypatch):
    monkeypatch.setattr(app_module, "ADMIN_BOOTSTRAP_SECRET", "expected-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "issue-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 900)

    payload = {"adminId": "tester", "secret": "expected-secret"}
    response = client.post('/api/admin/token', json=payload)
    assert response.status_code == 200
    body = response.get_json()
    assert "token" in body and body["token"]
    assert body["expiresIn"] == 900

    ping = client.get('/api/admin/ping', headers={'Authorization': f"Bearer {body['token']}"})
    assert ping.status_code == 200
