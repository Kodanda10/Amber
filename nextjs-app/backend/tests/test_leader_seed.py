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
