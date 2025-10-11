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


def test_metrics_endpoint():
    client = app.test_client()
    resp = client.get('/api/metrics')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'ingest' in data
    assert 'uptimeSeconds' in data


def test_sentiment_batch():
    client = app.test_client()
    payload = {"texts": ["Great work", "Terrible failure"]}
    resp = client.post('/api/sentiment/batch', json=payload)
    assert resp.status_code == 200
    out = resp.get_json()
    assert 'results' in out and len(out['results']) == 2
    labels = {r['sentiment'] for r in out['results']}
    assert labels.issubset({"Positive", "Negative", "Neutral"})
    # Each result should include numeric score
    assert all('score' in r and isinstance(r['score'], (int, float)) for r in out['results'])
