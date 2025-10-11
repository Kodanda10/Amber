import os
import importlib
import sys
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app


@pytest.fixture(autouse=True)
def _reset_db():
    with app.app_context():
        app_module.db.drop_all()
        app_module.db.create_all()
        yield
        app_module.db.session.remove()


def test_seed_data_populates_expected_leaders(monkeypatch):
    expected_handles = {
        "@vishnudeosai1",
        "@laxmirajwadebjp",
        "@RamvicharNetamB.J.P",
        "@OPChoudhary.India",
        "@lakhanlal.dewangan",
        "@sbjaiswalbjp",
        "@arunsaobjp",
        "@tankramvermaofficial",
        "@Dayaldasbaghel70",
        "@vijayratancg",
        "@kedarkashyapofficial",
    }

    def no_articles(name: str, limit: int):
        return [], "news"

    monkeypatch.setattr(app_module, "fetch_articles", no_articles)

    with app.app_context():
        app_module.seed_data()
        leaders = app_module.Leader.query.all()
        handles = {leader.handles.get("facebook") for leader in leaders}

    assert handles == expected_handles
    assert len(leaders) == len(expected_handles)


def test_leader_has_x_handle(monkeypatch):
    """Test that seeded leaders have X handles (ING-011)."""
    def no_articles(name: str, limit: int):
        return [], "news"

    monkeypatch.setattr(app_module, "fetch_articles", no_articles)

    with app.app_context():
        app_module.seed_data()
        leaders = app_module.Leader.query.all()
        
        # All leaders should have X handles
        for leader in leaders:
            assert "x" in leader.handles, f"Leader {leader.name} missing X handle"
            assert leader.handles["x"], f"Leader {leader.name} has empty X handle"
            # X handles should not have @ prefix (username only)
            assert not leader.handles["x"].startswith("@"), f"X handle should not have @ prefix"


def test_api_returns_x_handles(monkeypatch):
    """Test that API endpoint returns X handles in response (ING-011)."""
    def no_articles(name: str, limit: int):
        return [], "news"

    monkeypatch.setattr(app_module, "fetch_articles", no_articles)

    client = app.test_client()
    
    with app.app_context():
        app_module.seed_data()
    
    response = client.get("/api/leaders")
    assert response.status_code == 200
    
    leaders = response.get_json()
    assert len(leaders) > 0
    
    # Check that handles dict is returned with both facebook and x
    for leader in leaders:
        assert "handles" in leader
        assert "facebook" in leader["handles"]
        assert "x" in leader["handles"]
