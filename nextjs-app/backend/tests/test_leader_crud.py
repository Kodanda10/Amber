import os
import sys
import importlib
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app


def test_leader_crud():
    client = app.test_client()
    # Create
    payload = {"name": "Sample Leader", "handles": {"facebook": "@sample"}, "trackingTopics": ["topic"]}
    resp = client.post("/api/leaders", json=payload)
    assert resp.status_code == 201
    leader = resp.get_json()
    lid = leader["id"]
    assert leader["name"] == "Sample Leader"

    # List
    list_resp = client.get("/api/leaders")
    assert list_resp.status_code == 200
    leaders = list_resp.get_json()
    assert any(leader["id"] == lid for leader in leaders)

    # Delete
    del_resp = client.delete(f"/api/leaders/{lid}")
    assert del_resp.status_code == 200
    assert del_resp.get_json()["success"] is True

    # Verify deletion
    list_after = client.get("/api/leaders").get_json()
    assert not any(leader["id"] == lid for leader in list_after)
