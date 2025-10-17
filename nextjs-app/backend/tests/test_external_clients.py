import os
from types import SimpleNamespace

import pytest
import requests

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import facebook_client  # noqa: E402
import news_sources  # noqa: E402
import twitter_client  # noqa: E402


def test_facebook_fetch_posts_uses_graph_api(monkeypatch):
    monkeypatch.setenv("FACEBOOK_GRAPH_TOKEN", "test-token")
    captured = {}

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return DummyResponse({"posts": {"data": [{"id": "post-1"}]}})

    monkeypatch.setattr("facebook_client.requests.get", fake_get)

    posts = facebook_client.fetch_posts("@leader", limit=7)

    assert posts == [{"id": "post-1"}]
    assert "leader" in captured["url"]
    assert "posts.limit(7)" in captured["params"]["fields"]
    assert captured["timeout"] == facebook_client.GRAPH_TIMEOUT


def test_facebook_fetch_posts_without_token(monkeypatch):
    monkeypatch.delenv("FACEBOOK_GRAPH_TOKEN", raising=False)
    with pytest.raises(facebook_client.FacebookGraphError):
        facebook_client.fetch_posts("@leader")


def test_twitter_fetch_posts_enriches_media_and_user(monkeypatch):
    monkeypatch.setenv("TWITTER_BEARER_TOKEN", "bearer-token")
    captured_urls = []

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, headers=None, params=None, timeout=None):
        captured_urls.append((url, params))
        if url.endswith("/users/by/username/revleader"):
            return DummyResponse({"data": {"id": "user-123"}})
        assert url.endswith("/users/user-123/tweets")
        payload = {
            "data": [
                {
                    "id": "tweet-1",
                    "text": "Hello",
                    "attachments": {"media_keys": ["media1"]},
                    "author_id": "user-123",
                }
            ],
            "includes": {
                "media": [{"media_key": "media1", "url": "https://example.com/media.jpg"}],
                "users": [{"id": "user-123", "username": "revleader", "profile_image_url": "https://example.com/avatar.jpg"}],
            },
        }
        return DummyResponse(payload)

    monkeypatch.setattr("twitter_client.requests.get", fake_get)

    posts = twitter_client.fetch_posts("@revleader", limit=5)

    assert len(posts) == 1
    enriched = posts[0]
    assert enriched["author"]["username"] == "revleader"
    assert enriched["media"][0]["url"] == "https://example.com/media.jpg"
    assert captured_urls[0][0].endswith("/users/by/username/revleader")
    assert captured_urls[1][0].endswith("/users/user-123/tweets")
    assert captured_urls[1][1]["max_results"] == 5


def test_twitter_fetch_posts_without_token(monkeypatch):
    monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)
    with pytest.raises(twitter_client.TwitterAPIError):
        twitter_client.fetch_posts("@anyone")


def test_fetch_articles_prefers_scraper(monkeypatch):
    html = """
    <html>
      <body>
        <article>
          <div class="source">Example Source</div>
          <a href="./articles/test-story">Example Title</a>
          <div>Lead paragraph</div>
          <time datetime="2025-10-14T10:00:00Z"></time>
        </article>
      </body>
    </html>
    """

    class DummyResponse:
        text = html

        def raise_for_status(self):
            return None

    monkeypatch.setattr("news_sources.requests.get", lambda *args, **kwargs: DummyResponse())

    articles, origin = news_sources.fetch_articles("Leader Name", limit=1)

    assert origin == "scraper"
    assert len(articles) == 1
    article = articles[0]
    assert article["title"] == "Example Title"
    assert article["source"] == "Example Source"
    assert article["url"].startswith("https://news.google.com/")
    assert article["language"] == os.getenv("NEWS_LANGUAGE", "hi-IN")


def test_fetch_articles_falls_back_to_rss(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr("news_sources.requests.get", fake_get)

    entries = [
        SimpleNamespace(
            title="RSS Story",
            link="https://example.com/rss-story",
            summary="<p>Summary text</p>",
            published_parsed=(2025, 10, 14, 12, 0, 0, 0, 0, 0),
            source=SimpleNamespace(title="RSS Source"),
        )
    ]

    monkeypatch.setattr("news_sources.feedparser.parse", lambda *_: SimpleNamespace(entries=entries))

    articles, origin = news_sources.fetch_articles("Leader Name", limit=1)

    assert origin == "api"
    assert len(articles) == 1
    article = articles[0]
    assert article["title"] == "RSS Story"
    assert article["source"] == "RSS Source"
    assert article["summary"] == "Summary text"
