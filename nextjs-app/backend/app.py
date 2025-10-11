# backend/app.py
from __future__ import annotations

import os
import uuid
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from werkzeug.exceptions import HTTPException

from news_sources import fetch_articles
from sentiment import classify_sentiment
import facebook_client
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
import logging

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///amber.db")
POST_LIMIT = int(os.getenv("NEWS_POST_LIMIT", "6"))
FACEBOOK_GRAPH_ENABLED = os.getenv("FACEBOOK_GRAPH_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
FACEBOOK_GRAPH_LIMIT = int(os.getenv("FACEBOOK_GRAPH_LIMIT", "10"))
ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "amber-dev-secret")
ADMIN_JWT_TTL = int(os.getenv("ADMIN_JWT_TTL", "3600"))
ADMIN_BOOTSTRAP_SECRET = os.getenv("ADMIN_BOOTSTRAP_SECRET", ADMIN_JWT_SECRET)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})


from functools import wraps


def require_auth(allowed_roles: Optional[List[str]] = None):
    """
    Decorator to require authentication and optionally check roles.
    
    Args:
        allowed_roles: List of allowed roles (e.g., ["admin", "reviewer"]). 
                      If None, any authenticated user is allowed.
    
    Returns:
        The decorated function or an error response.
    """
    if allowed_roles is None:
        allowed_roles = ["admin", "reviewer"]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "unauthorized", "details": "Missing or invalid Authorization header"}), 401
            
            token = auth_header.split(" ", 1)[1].strip()
            payload = _verify_admin_token(token)
            if not payload:
                return jsonify({"error": "unauthorized", "details": "Invalid or expired token"}), 401
            
            # Check role if specific roles are required
            user_role = payload.get("role", "admin")
            if allowed_roles and user_role not in allowed_roles:
                return jsonify({"error": "forbidden", "details": f"Role '{user_role}' not authorized for this action"}), 403
            
            # Store payload in flask g for access in the view
            g.auth_payload = payload
            return func(*args, **kwargs)
        return wrapper
    return decorator


class Leader(db.Model):
    __tablename__ = "leaders"

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    handles = db.Column(db.JSON, nullable=False, default=dict)
    tracking_topics = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("Post", backref="leader", cascade="all, delete-orphan")

    def to_dict(self) -> Dict:
        avatar_url = _facebook_avatar(self.handles.get("facebook")) if self.handles else None
        return {
            "id": self.id,
            "name": self.name,
            "handles": self.handles,
            "trackingTopics": self.tracking_topics,
            "createdAt": self.created_at.isoformat(),
            "avatarUrl": avatar_url,
        }


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.String, primary_key=True)
    leader_id = db.Column(db.String, db.ForeignKey("leaders.id"), nullable=False)
    platform = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sentiment = db.Column(db.String, nullable=False, default="Neutral")
    metrics = db.Column(db.JSON, nullable=False, default=dict)
    verification_status = db.Column(db.String, nullable=False, default="Needs Review")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "leaderId": self.leader_id,
            "leaderName": self.leader.name if self.leader else None,
            "platform": self.platform,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "sentiment": self.sentiment,
            "metrics": self.metrics,
            "verificationStatus": self.verification_status,
        }


class ReviewItem(db.Model):
    __tablename__ = "review_items"

    id = db.Column(db.String, primary_key=True)
    post_id = db.Column(db.String, db.ForeignKey("posts.id"), nullable=False)
    state = db.Column(db.String, nullable=False, default="pending")
    notes = db.Column(db.Text, nullable=True)
    reviewer = db.Column(db.String, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)  # REV-002: Track when reviewed
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = db.relationship("Post")

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "postId": self.post_id,
            "state": self.state,
            "notes": self.notes,
            "reviewedBy": self.reviewer,  # REV-002: Return as reviewedBy for API
            "reviewedAt": self.reviewed_at.isoformat() if self.reviewed_at else None,  # REV-002
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "post": self.post.to_dict() if self.post else None,
        }


def _to_naive_datetime(value: Optional[str]) -> datetime:
    if not value:
        return datetime.utcnow()
    normalised = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalised)
    except ValueError:
        return datetime.utcnow()
    if dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _compose_content(source: str, title: str, summary: str | None) -> str:
    snippet = summary.strip() if summary else ""
    if snippet:
        return snippet
    return title


def _facebook_avatar(handle: Optional[str]) -> Optional[str]:
    if not handle:
        return None
    username = handle.lstrip("@")
    if not username:
        return None
    return f"https://graph.facebook.com/{username}/picture?type=large&width=200&height=200"


_INGEST_METRICS = {
    "totalIngests": 0,
    "lastIngestMs": 0,
    "lastError": None,
}


# --------------- Structured Logging ---------------
class JsonFormatter(logging.Formatter):
    def format(self, record):  # type: ignore[override]
        base = {
            "level": record.levelname,
            "message": record.getMessage(),
            "time": datetime.utcnow().isoformat(),
        }
        # attach request correlation if present
        req_id = getattr(g, "request_id", None)
        if req_id:
            base["requestId"] = req_id
        if record.exc_info:
            base["excInfo"] = self.formatException(record.exc_info)
        return json.dumps(base, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
app.logger.handlers = [handler]
app.logger.setLevel(logging.INFO)


@app.before_request
def _assign_request_id():
    g.request_id = uuid.uuid4().hex
    g._start_time = time.perf_counter()


@app.after_request
def _log_request(resp):
    duration_ms = None
    if hasattr(g, "_start_time"):
        duration_ms = int((time.perf_counter() - g._start_time) * 1000)
    log_payload = {
        "event": "request",
        "method": request.method,
        "path": request.path,
        "status": resp.status_code,
        "durationMs": duration_ms,
    }
    app.logger.info(json.dumps(log_payload))
    return resp


def _hash_article(article: Dict) -> str:
    base = f"{article.get('url','')}|{article.get('title','')}|{article.get('summary','')}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _sync_posts_for_leader(leader: Leader) -> Tuple[List[Dict], str]:
    """Upsert posts for a leader from Graph API or news sources.

    Prefers Facebook Graph data when enabled and gracefully falls back to
    existing news ingestion. If no upstream data is available, emits a
    localized sample post so the UI is not empty.
    """

    start = time.perf_counter()

    existing_posts: List[Post] = Post.query.filter_by(leader_id=leader.id).all()
    by_link: Dict[str, Post] = {}
    by_platform_id: Dict[str, Post] = {}
    for post in existing_posts:
        metrics = post.metrics or {}
        link = metrics.get("link") if isinstance(metrics, dict) else None
        if link:
            by_link[link] = post
        platform_post_id = metrics.get("platformPostId") if isinstance(metrics, dict) else None
        if platform_post_id:
            by_platform_id[platform_post_id] = post

    avatar_url = _facebook_avatar(leader.handles.get("facebook")) if leader.handles else None
    upserted_posts: List[Post] = []
    origin = "news"

    graph_handle = leader.handles.get("facebook") if leader.handles else None
    if FACEBOOK_GRAPH_ENABLED and graph_handle:
        try:
            graph_records = facebook_client.fetch_posts(graph_handle, FACEBOOK_GRAPH_LIMIT)
        except Exception as exc:  # noqa: BLE001 - log but continue with fallback
            app.logger.warning("graph_fetch_failed leader=%s error=%s", leader.name, exc)
        else:
            if graph_records:
                upserted_posts = _upsert_graph_posts(
                    leader,
                    graph_records,
                    by_link,
                    by_platform_id,
                    existing_posts,
                    avatar_url,
                )
                origin = "graph"

    if not upserted_posts:
        try:
            articles, origin = fetch_articles(leader.name, POST_LIMIT)
        except Exception as exc:  # noqa: BLE001 - log and surface empty list
            _INGEST_METRICS["lastError"] = str(exc)
            app.logger.exception("ingest_failure leader=%s error=%s", leader.name, exc)
            return [], "error"

        upserted_posts = _upsert_article_posts(
            leader,
            articles,
            origin,
            by_link,
            existing_posts,
            avatar_url,
        )

    if not upserted_posts:
        sample_post = _ensure_sample_post(leader, existing_posts, avatar_url)
        upserted_posts = [sample_post]
        origin = "sample"

    db.session.commit()
    payload = [post.to_dict() for post in upserted_posts]
    duration_ms = int((time.perf_counter() - start) * 1000)
    _INGEST_METRICS["totalIngests"] += 1
    _INGEST_METRICS["lastIngestMs"] = duration_ms
    _INGEST_METRICS["lastError"] = None
    app.logger.info(
        json.dumps(
            {
                "event": "ingest_success",
                "leader": leader.name,
                "origin": origin,
                "articles": len(payload),
                "durationMs": duration_ms,
            }
        )
    )
    return payload, origin


def _upsert_article_posts(
    leader: Leader,
    articles: List[Dict],
    origin: str,
    by_link: Dict[str, Post],
    existing_posts: List[Post],
    avatar_url: Optional[str],
) -> List[Post]:
    now = datetime.utcnow()
    upserted: List[Post] = []

    for article in articles:
        link = article.get("url")
        title = article.get("title", "")
        summary = article.get("summary")
        source = article.get("source", "Unknown")
        timestamp = _to_naive_datetime(article.get("published_at"))
        content = _compose_content(source, title, summary)
        combined_text = f"{title} {summary or ''}".strip()
        sentiment, score = classify_sentiment(combined_text, return_score=True)
        verification = "Verified" if source != "Unknown" else "Needs Review"
        language = article.get("language") or "unknown"
        article_hash = _hash_article(article)

        metrics_base = {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "source": source,
            "origin": origin,
            "title": title,
            "link": link,
            "avatarUrl": avatar_url,
            "language": language,
            "hash": article_hash,
        }

        if link and link in by_link:
            post = by_link[link]
            if timestamp > post.timestamp:
                post.timestamp = timestamp
            post.content = content
            post.sentiment = sentiment
            existing_metrics = post.metrics or {}
            first_seen = existing_metrics.get("firstSeenAt") or existing_metrics.get("first_seen_at")
            merged = {**metrics_base, **existing_metrics}
            if not first_seen:
                first_seen = post.created_at.isoformat() if post.created_at else now.isoformat()
            merged["firstSeenAt"] = first_seen
            merged["lastSeenAt"] = now.isoformat()
            merged["sentimentScore"] = score
            old_hash = existing_metrics.get("hash")
            revision = existing_metrics.get("revision", 1)
            if old_hash and old_hash != article_hash:
                revision += 1
            merged["revision"] = revision
            post.metrics = merged
            post.verification_status = verification
        else:
            metrics_new = {
                **metrics_base,
                "firstSeenAt": now.isoformat(),
                "lastSeenAt": now.isoformat(),
                "revision": 1,
                "sentimentScore": score,
            }
            post = Post(
                id=str(uuid.uuid4()),
                leader_id=leader.id,
                platform="News",
                content=content,
                timestamp=timestamp,
                sentiment=sentiment,
                metrics=metrics_new,
                verification_status=verification,
            )
            post.leader = leader
            db.session.add(post)
            db.session.flush()
            existing_posts.append(post)
            if link:
                by_link[link] = post
        upserted.append(post)

    return upserted


def _upsert_graph_posts(
    leader: Leader,
    graph_records: List[Dict],
    by_link: Dict[str, Post],
    by_platform_id: Dict[str, Post],
    existing_posts: List[Post],
    avatar_url: Optional[str],
) -> List[Post]:
    now = datetime.utcnow()
    upserted: List[Post] = []

    for record in graph_records:
        platform_post_id = record.get("id")
        message = record.get("message") or ""
        permalink = record.get("permalink_url")
        timestamp = _to_naive_datetime(record.get("created_time"))
        sentiment, score = classify_sentiment(message, return_score=True)
        media_url = record.get("full_picture") or _extract_graph_media_url(record)
        author_avatar = (
            (((record.get("from") or {}).get("picture") or {}).get("data") or {}).get("url")
            or avatar_url
        )
        article_hash = _hash_article({
            "url": permalink or platform_post_id or "",
            "title": message,
            "summary": message,
        })

        metrics_base = {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "origin": "graph",
            "link": permalink,
            "avatarUrl": author_avatar,
            "mediaUrl": media_url,
            "platformPostId": platform_post_id,
            "language": "unknown",
            "hash": article_hash,
        }

        post: Optional[Post] = None
        if platform_post_id and platform_post_id in by_platform_id:
            post = by_platform_id[platform_post_id]
        elif permalink and permalink in by_link:
            post = by_link[permalink]

        if post:
            if timestamp > post.timestamp:
                post.timestamp = timestamp
            post.content = message or post.content
            post.sentiment = sentiment
            post.platform = "Facebook"
            existing_metrics = post.metrics or {}
            first_seen = existing_metrics.get("firstSeenAt") or existing_metrics.get("first_seen_at")
            merged = {**metrics_base, **existing_metrics}
            if not first_seen:
                first_seen = post.created_at.isoformat() if post.created_at else now.isoformat()
            merged["firstSeenAt"] = first_seen
            merged["lastSeenAt"] = now.isoformat()
            merged["sentimentScore"] = score
            old_hash = existing_metrics.get("hash")
            revision = existing_metrics.get("revision", 1)
            if old_hash and old_hash != article_hash:
                revision += 1
            merged["revision"] = revision
            post.metrics = merged
            if platform_post_id:
                by_platform_id[platform_post_id] = post
            if permalink:
                by_link[permalink] = post
        else:
            metrics_new = {
                **metrics_base,
                "firstSeenAt": now.isoformat(),
                "lastSeenAt": now.isoformat(),
                "revision": 1,
                "sentimentScore": score,
            }
            post = Post(
                id=str(uuid.uuid4()),
                leader_id=leader.id,
                platform="Facebook",
                content=message or "",
                timestamp=timestamp,
                sentiment=sentiment,
                metrics=metrics_new,
                verification_status="Needs Review",
            )
            post.leader = leader
            db.session.add(post)
            db.session.flush()
            existing_posts.append(post)
            if platform_post_id:
                by_platform_id[platform_post_id] = post
            if permalink:
                by_link[permalink] = post

        upserted.append(post)

    return upserted


def _ensure_sample_post(
    leader: Leader,
    existing_posts: List[Post],
    avatar_url: Optional[str],
) -> Post:
    for post in existing_posts:
        metrics = post.metrics or {}
        if metrics.get("origin") == "sample":
            return post

    now = datetime.utcnow()
    sample_content = f"आईए {leader.name} की हालिया जनसभाओं और अभियानों पर नज़र रखें — वास्तविक पोस्ट उपलब्ध होते ही यहाँ दिखाई देंगे।"
    metrics = {
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "source": "Sample",
        "origin": "sample",
        "language": "hi",
        "avatarUrl": avatar_url,
        "firstSeenAt": now.isoformat(),
        "lastSeenAt": now.isoformat(),
        "revision": 1,
    }

    post = Post(
        id=str(uuid.uuid4()),
        leader_id=leader.id,
        platform="Facebook",
        content=sample_content,
        timestamp=now,
        sentiment="Neutral",
        metrics=metrics,
        verification_status="Needs Review",
    )
    post.leader = leader
    db.session.add(post)
    db.session.flush()
    existing_posts.append(post)
    return post


def _extract_graph_media_url(record: Dict) -> Optional[str]:
    attachments = ((record.get("attachments") or {}).get("data") or [])
    for attachment in attachments:
        media = attachment.get("media") or {}
        image = media.get("image") or {}
        for key in ("src", "url"):
            if key in image:
                return image[key]
        if "source" in media:
            return media["source"]
        if attachment.get("url"):
            return attachment["url"]
    return None


def _admin_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(ADMIN_JWT_SECRET, salt="amber-admin-token")


def generate_admin_token(admin_id: str, role: str = "admin") -> str:
    return _admin_serializer().dumps({"admin": admin_id, "role": role})


def _verify_admin_token(token: str) -> Optional[Dict]:
    serializer = _admin_serializer()
    try:
        payload = serializer.loads(token, max_age=ADMIN_JWT_TTL)
    except (SignatureExpired, BadSignature):
        return None
    if not isinstance(payload, dict) or "admin" not in payload:
        return None
    # Ensure role is present, default to "admin" for backward compatibility
    if "role" not in payload:
        payload["role"] = "admin"
    return payload


def seed_data() -> None:
    if Leader.query.count() > 0:
        return

    leaders_payload = [
        {
            "name": "Vishnu Deo Sai",
            "handles": {"facebook": "@vishnudeosai1"},
            "tracking_topics": ["tribal welfare", "state development", "governance"],
        },
        {
            "name": "Laxmi Rajwade",
            "handles": {"facebook": "@laxmirajwadebjp"},
            "tracking_topics": ["women empowerment", "public health", "local issues"],
        },
        {
            "name": "Ramvichar Netam",
            "handles": {"facebook": "@RamvicharNetamB.J.P"},
            "tracking_topics": ["agriculture", "rural development", "policy making"],
        },
        {
            "name": "O. P. Choudhary",
            "handles": {"facebook": "@OPChoudhary.India"},
            "tracking_topics": ["education reform", "finance", "urban development"],
        },
        {
            "name": "Lakhan Lal Dewangan",
            "handles": {"facebook": "@lakhanlal.dewangan"},
            "tracking_topics": ["industrial policy", "infrastructure", "skill development"],
        },
        {
            "name": "S. B. Jaiswal",
            "handles": {"facebook": "@sbjaiswalbjp"},
            "tracking_topics": ["youth outreach", "party organisation", "campaign strategy"],
        },
        {
            "name": "Arun Sao",
            "handles": {"facebook": "@arunsaobjp"},
            "tracking_topics": ["organisation building", "governance", "public welfare"],
        },
        {
            "name": "Tank Ram Verma",
            "handles": {"facebook": "@tankramvermaofficial"},
            "tracking_topics": ["rural development", "tribal welfare", "healthcare"],
        },
        {
            "name": "Dayal Das Baghel",
            "handles": {"facebook": "@Dayaldasbaghel70"},
            "tracking_topics": ["cultural heritage", "tourism", "community programs"],
        },
        {
            "name": "Vijay Ratan",
            "handles": {"facebook": "@vijayratancg"},
            "tracking_topics": ["grassroots mobilisation", "education", "rural infrastructure"],
        },
        {
            "name": "Kedar Kashyap",
            "handles": {"facebook": "@kedarkashyapofficial"},
            "tracking_topics": ["tribal affairs", "education", "public health"],
        },
    ]

    for payload in leaders_payload:
        leader = Leader(
            id=str(uuid.uuid4()),
            name=payload["name"],
            handles=payload["handles"],
            tracking_topics=payload["tracking_topics"],
        )
        db.session.add(leader)
    db.session.commit()

    for leader in Leader.query.all():
        _sync_posts_for_leader(leader)


def serialize_dashboard() -> Dict:
    if Post.query.count() == 0:
        for leader in Leader.query.all():
            _sync_posts_for_leader(leader)
    leaders = [leader.to_dict() for leader in Leader.query.order_by(Leader.created_at.desc()).all()]
    posts = [post.to_dict() for post in Post.query.order_by(Post.timestamp.desc()).all()]
    return {"leaders": leaders, "posts": posts}


BUILD_INFO = {
    "commit": os.getenv("GIT_COMMIT", "unknown"),
    "version": os.getenv("APP_VERSION", "0.1.0"),
    "buildTime": os.getenv("BUILD_TIME", "unknown"),
}


@app.route("/api/admin/ping", methods=["GET"])
def admin_ping():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "unauthorized"}), 401
    token = auth_header.split(" ", 1)[1].strip()
    payload = _verify_admin_token(token)
    if not payload:
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"status": "ok", "admin": payload["admin"]})


@app.route("/api/admin/token", methods=["POST"])
def admin_token():
    payload = request.get_json(silent=True) or {}
    admin_id = payload.get("adminId")
    secret = payload.get("secret")

    if not admin_id:
        return jsonify({"error": "invalid_request", "details": "adminId is required"}), 400
    if not secret:
        return jsonify({"error": "invalid_request", "details": "secret is required"}), 400
    if secret != ADMIN_BOOTSTRAP_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    token = generate_admin_token(admin_id)
    return jsonify({"token": token, "expiresIn": ADMIN_JWT_TTL})


@app.errorhandler(Exception)
def handle_uncaught_exception(exc: Exception):
    status = 500
    if isinstance(exc, HTTPException):
        status = exc.code or 500

    request_id = getattr(g, "request_id", None)
    log_payload = {
        "event": "error",
        "method": request.method,
        "path": request.path,
        "status": status,
        "error": str(exc),
        "requestId": request_id,
        "exceptionType": exc.__class__.__name__,
    }
    app.logger.error(json.dumps(log_payload), exc_info=exc)

    if isinstance(exc, HTTPException):
        response = exc.get_response()
        response.data = json.dumps(
            {
                "error": (exc.name or "http_error").lower().replace(" ", "_"),
                "status": status,
                "message": exc.description,
                "requestId": request_id,
            }
        )
        response.content_type = "application/json"
        return response

    return (
        jsonify(
            {
                "error": "internal_server_error",
                "status": status,
                "requestId": request_id,
            }
        ),
        status,
    )


@app.route("/api/health", methods=["GET"])
def health_check():
    leader_count = Leader.query.count()
    post_count = Post.query.count()
    review_count = ReviewItem.query.count()
    latest_post = (
        Post.query.order_by(Post.timestamp.desc()).first()
        if post_count > 0
        else None
    )
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "stats": {
            "leaders": leader_count,
            "posts": post_count,
            "reviewItems": review_count,
            "latestPostTimestamp": latest_post.timestamp.isoformat() if latest_post else None,
            "totalIngests": _INGEST_METRICS["totalIngests"],
            "lastIngestMs": _INGEST_METRICS["lastIngestMs"],
        },
        "build": BUILD_INFO,
    }


@app.route("/api/metrics", methods=["GET"])
def metrics():  # simple in-memory metrics exposition
    return jsonify({
        "ingest": _INGEST_METRICS,
        "uptimeSeconds": int((datetime.utcnow() - START_TIME).total_seconds()),
    })


@app.route("/api/sentiment/batch", methods=["POST"])
def sentiment_batch():
    payload = request.get_json(force=True)
    texts = payload.get("texts", [])
    if not isinstance(texts, list):
        return jsonify({"error": "texts must be a list"}), 400
    results = []
    for t in texts:
        label, score = classify_sentiment(t or "", return_score=True)
        results.append({"text": t, "sentiment": label, "score": score})
    return jsonify({"results": results})


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    return jsonify(serialize_dashboard())


@app.route("/api/leaders", methods=["GET"])
def list_leaders():
    leaders = [leader.to_dict() for leader in Leader.query.order_by(Leader.created_at.desc()).all()]
    return jsonify(leaders)


@app.route("/api/leaders", methods=["POST"])
def create_leader():
    payload = request.get_json(force=True)
    name = payload.get("name")
    handles = payload.get("handles", {})
    tracking_topics = payload.get("trackingTopics", [])

    if not name:
        return jsonify({"error": "name is required"}), 400

    leader = Leader(
        id=str(uuid.uuid4()),
        name=name,
        handles=handles,
        tracking_topics=tracking_topics,
    )
    db.session.add(leader)
    db.session.commit()

    _sync_posts_for_leader(leader)

    return jsonify(leader.to_dict()), 201


@app.route("/api/leaders/<leader_id>", methods=["DELETE"])
def delete_leader(leader_id: str):
    leader = db.session.get(Leader, leader_id)
    if not leader:
        return jsonify({"error": "Leader not found"}), 404

    db.session.delete(leader)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/leaders/<leader_id>/refresh", methods=["POST"])
def refresh_leader(leader_id: str):
    leader = db.session.get(Leader, leader_id)
    if not leader:
        return jsonify({"error": "Leader not found"}), 404

    posts, origin = _sync_posts_for_leader(leader)
    return jsonify({"posts": posts, "origin": origin})


@app.route("/api/posts", methods=["GET"])
def list_posts():
    leader_id = request.args.get("leaderId")
    query = Post.query
    if leader_id:
        query = query.filter_by(leader_id=leader_id)
    posts = [post.to_dict() for post in query.order_by(Post.timestamp.desc()).all()]
    return jsonify(posts)


@app.route("/api/posts/paginated", methods=["GET"])
def list_posts_paginated():
    """Cursor-based paginated posts list.

    Query params:
        leaderId (optional) - filter by leader
        limit (optional, int) - max items (default 25, max 100)
        before (optional ISO timestamp) - return posts with timestamp strictly before this
    Response:
        {"items": [...], "nextCursor": <iso or null>, "hasMore": bool}
    """
    leader_id = request.args.get("leaderId")
    limit_raw = request.args.get("limit", "25")
    before_raw = request.args.get("before")

    try:
        limit = min(max(int(limit_raw), 1), 100)
    except ValueError:
        limit = 25

    query = Post.query
    if leader_id:
        query = query.filter_by(leader_id=leader_id)
    if before_raw:
        try:
            before_dt = _to_naive_datetime(before_raw)
            query = query.filter(Post.timestamp < before_dt)
        except Exception:  # noqa: BLE001
            pass

    ordered = query.order_by(Post.timestamp.desc()).limit(limit + 1).all()
    has_more = len(ordered) > limit
    items = ordered[:limit]
    next_cursor = items[-1].timestamp.isoformat() if has_more and items else None
    payload = {
        "items": [p.to_dict() for p in items],
        "nextCursor": next_cursor,
        "hasMore": has_more,
    }
    return jsonify(payload)


@app.route("/api/posts", methods=["POST"])
def create_post():
    payload = request.get_json(force=True)
    leader_id = payload.get("leaderId")
    leader = db.session.get(Leader, leader_id)
    if not leader:
        return jsonify({"error": "Leader not found"}), 404

    post = Post(
        id=str(uuid.uuid4()),
        leader_id=leader_id,
        platform=payload.get("platform", "News"),
        content=payload.get("content", ""),
        timestamp=_to_naive_datetime(payload.get("timestamp")),
        sentiment=payload.get("sentiment", "Neutral"),
        metrics=payload.get("metrics", {"likes": 0, "comments": 0, "shares": 0}),
        verification_status=payload.get("verificationStatus", "Needs Review"),
    )
    db.session.add(post)

    if payload.get("requiresReview"):
        review_item = ReviewItem(id=str(uuid.uuid4()), post=post, state="pending", notes=payload.get("reviewNotes"))
        db.session.add(review_item)

    db.session.commit()
    return jsonify(post.to_dict()), 201


@app.route("/api/posts/<post_id>", methods=["PUT"])
def update_post(post_id: str):
    payload = request.get_json(force=True)
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    post.content = payload.get("content", post.content)
    post.sentiment = payload.get("sentiment", post.sentiment)
    post.metrics = payload.get("metrics", post.metrics)
    post.verification_status = payload.get("verificationStatus", post.verification_status)
    db.session.commit()

    return jsonify(post.to_dict())


@app.route("/api/posts/<post_id>", methods=["DELETE"])
def delete_post(post_id: str):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    ReviewItem.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/review", methods=["GET"])
def list_review_items():
    items = [item.to_dict() for item in ReviewItem.query.order_by(ReviewItem.updated_at.desc()).all()]
    return jsonify(items)


def _update_review_state(review_id: str, state: str, notes: Optional[str] = None, reviewer: Optional[str] = None) -> Optional[ReviewItem]:
    item = db.session.get(ReviewItem, review_id)
    if not item:
        return None
    item.state = state
    if notes is not None:
        item.notes = notes
    # REV-002: Capture reviewer identity and timestamp
    if reviewer is not None:
        item.reviewer = reviewer
        item.reviewed_at = datetime.utcnow()
    db.session.commit()
    return item


@app.route("/api/review/<review_id>/approve", methods=["POST"])
@require_auth(allowed_roles=["admin", "reviewer"])
def approve_review(review_id: str):
    # REV-002: Extract reviewer identity from auth payload
    reviewer_id = g.auth_payload.get("admin") if hasattr(g, "auth_payload") else None
    item = _update_review_state(review_id, "approved", reviewer=reviewer_id)
    if not item:
        return jsonify({"error": "Review item not found"}), 404
    return jsonify(item.to_dict())


@app.route("/api/review/<review_id>/reject", methods=["POST"])
@require_auth(allowed_roles=["admin", "reviewer"])
def reject_review(review_id: str):
    payload = request.get_json(silent=True) or {}
    # REV-002: Extract reviewer identity from auth payload
    reviewer_id = g.auth_payload.get("admin") if hasattr(g, "auth_payload") else None
    item = _update_review_state(review_id, "rejected", payload.get("notes"), reviewer=reviewer_id)
    if not item:
        return jsonify({"error": "Review item not found"}), 404
    return jsonify(item.to_dict())


def init_db() -> None:
    db.create_all()
    seed_data()


START_TIME = datetime.utcnow()
with app.app_context():
    init_db()


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
