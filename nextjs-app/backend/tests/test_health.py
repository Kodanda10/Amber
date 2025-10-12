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
    # Accept both 200 and 503 (if Redis is down, service is degraded)
    assert resp.status_code in (200, 503)
    data = resp.get_json()
    assert data["status"] in ("ok", "degraded")
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "ok"
    assert "build" in data and "version" in data["build"]
