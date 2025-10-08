import os, sys, importlib, uuid, json, logging
from pathlib import Path
from datetime import datetime
import re
import pytest

# Ensure in-memory DB before importing app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app
Leader = app_module.Leader
_sync_posts_for_leader = app_module._sync_posts_for_leader


@pytest.fixture(autouse=True)
def _app_context():
    with app.app_context():
        yield

def _fake_article(name: str):
    return {
        "url": f"http://example.com/{uuid.uuid4().hex}",
        "title": f"Development progress for {name}",
        "summary": "Significant positive momentum and improvement recorded",
        "source": "Example News",
        "published_at": datetime.utcnow().isoformat(),
        "language": "en",
    }

# --------------------- 1. Request Log Capture ---------------------

def test_request_logging_emits_json(caplog):
    caplog.set_level(logging.INFO, logger=app.logger.name)
    client = app.test_client()
    resp = client.get('/api/health')
    assert resp.status_code == 200
    # Find a log with event=request and path=/api/health
    found = False
    for rec in caplog.records:
        try:
            payload = json.loads(rec.getMessage())
        except Exception:
            continue
        if payload.get('event') == 'request' and payload.get('path') == '/api/health' and payload.get('status') == 200:
            found = True
            assert payload.get('method') == 'GET'
            assert isinstance(payload.get('durationMs'), (int, type(None)))
            break
    assert found, "Did not capture structured request log for /api/health"

# --------------------- 2. Ingest Success Log ----------------------

def test_ingest_success_log_emitted(caplog):
    caplog.set_level(logging.INFO, logger=app.logger.name)
    # Monkeypatch fetch_articles
    original = getattr(app_module, 'fetch_articles')
    def fake_fetch_articles(name: str, limit: int):
        return ([_fake_article(name)], 'test')
    setattr(app_module, 'fetch_articles', fake_fetch_articles)
    try:
        # Create leader and run ingest
        leader = Leader(id=str(uuid.uuid4()), name="LogTest Leader", handles={}, tracking_topics=[])
        app_module.db.session.add(leader)
        app_module.db.session.commit()
        _sync_posts_for_leader(leader)
    finally:
        setattr(app_module, 'fetch_articles', original)
    # Scan logs
    for rec in caplog.records:
        try:
            payload = json.loads(rec.getMessage())
        except Exception:
            continue
        if payload.get('event') == 'ingest_success' and payload.get('leader') == 'LogTest Leader':
            assert payload.get('articles') >= 1
            assert 'durationMs' in payload
            return
    assert False, 'ingest_success log record not found'

# --------------------- 3. SQLAlchemy Lookup Path ------------------

def test_sqlalchemy_lookup_via_endpoints(caplog):
    client = app.test_client()
    # Create leader via API (triggers ingest)
    resp = client.post('/api/leaders', json={'name': 'Lookup Leader', 'handles': {}, 'trackingTopics': []})
    assert resp.status_code == 201
    leader_id = resp.get_json()['id']
    # Refresh should succeed (200)
    resp2 = client.post(f'/api/leaders/{leader_id}/refresh')
    assert resp2.status_code == 200
    # Delete
    del_resp = client.delete(f'/api/leaders/{leader_id}')
    assert del_resp.status_code == 200
    # Refresh again should now 404
    resp3 = client.post(f'/api/leaders/{leader_id}/refresh')
    assert resp3.status_code == 404

# --------------------- 4. Extended Sentiment Batch ----------------

def test_batch_sentiment_score_ordering():
    client = app.test_client()
    texts = [
        "horrible catastrophic failure",  # negative
        "this is a statement",            # neutral-ish
        "excellent remarkable success"    # positive
    ]
    resp = client.post('/api/sentiment/batch', json={'texts': texts})
    assert resp.status_code == 200
    data = resp.get_json()['results']
    # Map input -> score
    score_map = {r['text']: r['score'] for r in data}
    neg, neu, pos = score_map[texts[0]], score_map[texts[1]], score_map[texts[2]]
    assert neg < neu < pos, f"Expected ordering neg < neu < pos, got {neg} < {neu} < {pos}"

# --------------------- 5. Metrics Increment After Ingest ----------

def test_metrics_ingest_increment(monkeypatch):
    client = app.test_client()
    first = client.get('/api/metrics').get_json()
    start_ingests = first['ingest']['totalIngests']
    # Monkeypatch fetch_articles to ensure ingest is quick & deterministic
    original = getattr(app_module, 'fetch_articles')
    def fake_fetch_articles(name: str, limit: int):
        return ([_fake_article(name)], 'test')
    setattr(app_module, 'fetch_articles', fake_fetch_articles)
    try:
        # Trigger new ingest by creating a leader (API path calls _sync_posts_for_leader)
        resp = client.post('/api/leaders', json={'name': 'Metrics Leader', 'handles': {}, 'trackingTopics': []})
        assert resp.status_code == 201
    finally:
        setattr(app_module, 'fetch_articles', original)
    second = client.get('/api/metrics').get_json()
    assert second['ingest']['totalIngests'] >= start_ingests + 1, 'Ingest counter did not increase'


def test_error_log_shape_on_exception(monkeypatch, caplog):
    caplog.set_level(logging.ERROR, logger=app.logger.name)

    def boom():
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(app_module, 'serialize_dashboard', boom)

    client = app.test_client()
    response = client.get('/api/dashboard')
    assert response.status_code == 500
    body = response.get_json()
    assert body['error'] == 'internal_server_error'
    assert body['status'] == 500
    assert body['requestId']

    for record in caplog.records:
        try:
            payload = json.loads(record.getMessage())
        except Exception:
            continue
        if payload.get('event') == 'error' and payload.get('path') == '/api/dashboard':
            assert payload.get('status') == 500
            assert payload.get('method') == 'GET'
            assert 'simulated failure' in payload.get('error', '')
            assert payload.get('requestId') == body['requestId']
            break
    else:
        assert False, 'No structured error log captured'
