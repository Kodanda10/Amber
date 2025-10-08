"""Utilities for retrieving real-world news articles about political leaders."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from urllib.parse import quote_plus, urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)

_USER_AGENT = os.getenv(
    "NEWS_SCRAPER_USER_AGENT",
    "AmberNewsBot/1.0 (+https://github.com/abhijita/amber)",
)
_GOOGLE_NEWS_BASE = "https://news.google.com/"
_DEFAULT_QUERY_SUFFIX = os.getenv("NEWS_SEARCH_WINDOW", "when:30d")
_NEWS_LANGUAGE = os.getenv("NEWS_LANGUAGE", "hi-IN")  # e.g., hi-IN, en-IN
# Derive CEID (country:lang) if not explicitly provided
_NEWS_CEID = os.getenv("NEWS_CEID", "IN:hi" if _NEWS_LANGUAGE.startswith("hi") else "IN:en")
_NEWS_GL = os.getenv("NEWS_GL", "IN")
_TIMEOUT_SECONDS = int(os.getenv("NEWS_REQUEST_TIMEOUT", "15"))


def _default_headers() -> Dict[str, str]:
    return {"User-Agent": _USER_AGENT}


def _normalise_iso(timestamp: str | None) -> str:
    if not timestamp:
        return datetime.now(timezone.utc).isoformat()
    if timestamp.endswith("Z"):
        return timestamp.replace("Z", "+00:00")
    return timestamp


def _scrape_google_news(query: str, limit: int) -> Tuple[List[Dict], str]:
    search_url = (
        f"{_GOOGLE_NEWS_BASE}search?q={quote_plus(query)}+{quote_plus(_DEFAULT_QUERY_SUFFIX)}"
        f"&hl={_NEWS_LANGUAGE}&gl={_NEWS_GL}&ceid={_NEWS_CEID}"
    )
    response = requests.get(search_url, headers=_default_headers(), timeout=_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles: List[Dict] = []

    for article in soup.select("article"):
        anchor = next((a for a in article.select("a") if a.get_text(strip=True)), None)
        if not anchor:
            continue
        raw_link = anchor.get("href")
        if not raw_link:
            continue
        href = urljoin(_GOOGLE_NEWS_BASE, raw_link.lstrip("./"))
        title = anchor.get_text(strip=True)

        text_lines = [
            line
            for line in article.get_text("\n", strip=True).split("\n")
            if line and line.lower() != "more"
        ]
        source = text_lines[0] if text_lines else "Unknown"
        summary = ""
        if len(text_lines) >= 3:
            summary = text_lines[2]
        elif len(text_lines) >= 2:
            summary = text_lines[1]

        time_tag = article.select_one("time")
        published_at = None
        if time_tag and time_tag.has_attr("datetime"):
            published_at = _normalise_iso(time_tag["datetime"])

        articles.append(
            {
                "title": title,
                "summary": summary,
                "url": href,
                "source": source,
                "published_at": published_at,
                "language": _NEWS_LANGUAGE,
            }
        )

        if len(articles) >= limit:
            break

    return articles, "scraper"


def _rss_google_news(query: str, limit: int) -> Tuple[List[Dict], str]:
    rss_url = (
        f"{_GOOGLE_NEWS_BASE}rss/search?q={quote_plus(query + ' ' + _DEFAULT_QUERY_SUFFIX)}"
        f"&hl={_NEWS_LANGUAGE}&gl={_NEWS_GL}&ceid={_NEWS_CEID}"
    )
    feed = feedparser.parse(rss_url)
    articles: List[Dict] = []

    for entry in feed.entries[:limit]:
        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = datetime(
                *entry.published_parsed[:6], tzinfo=timezone.utc
            ).isoformat()

        source_title = None
        if getattr(entry, "source", None):
            source_title = getattr(entry.source, "title", None)

        summary_html = getattr(entry, "summary", "")
        summary = BeautifulSoup(summary_html, "html.parser").get_text(" ", strip=True)

        articles.append(
            {
                "title": getattr(entry, "title", ""),
                "summary": summary,
                "url": getattr(entry, "link", ""),
                "source": source_title or "Unknown",
                "published_at": _normalise_iso(published_at),
                "language": _NEWS_LANGUAGE,
            }
        )

    return articles, "api"


def fetch_articles(query: str, limit: int = 8) -> Tuple[List[Dict], str]:
    """Fetch articles for the provided query, preferring HTML scraping."""
    try:
        articles, origin = _scrape_google_news(query, limit)
        if articles:
            return articles, origin
    except Exception as exc:  # noqa: BLE001 - we want to log and continue
        LOGGER.warning("HTML scraping failed for query '%s': %s", query, exc)

    articles, origin = _rss_google_news(query, limit)
    return articles, origin
