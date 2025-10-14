import os
import importlib
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Ensure the backend directory is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app


def test_health():
    client = app.test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    # Updated to check new response format with checks
    assert "checks" in data
    assert "stats" in data["checks"]
    assert "leaders" in data["checks"]["stats"]
    assert "build" in data and "version" in data["build"]
