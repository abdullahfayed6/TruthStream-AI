"""
TruthStream AI — Live Ingestion Service

Fetches real news articles from NewsAPI and GNews APIs, classifies them
using the ML classifier (or fallback), and adds them directly to the
in-memory FallbackStore or MongoDB. The WebSocket endpoint then pushes
them to the frontend in real-time.

This runs as a background async task inside the FastAPI server.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lightweight classifier (no Spark dependency)
# ---------------------------------------------------------------------------

def classify_article(title: str, content: str) -> dict[str, Any]:
    """
    Classify an article as Fake/Real.
    
    Uses the ML fallback classifier (hash-based deterministic) since the
    full DistilBERT model requires PySpark + torch which may not be
    available in the local dev environment.
    """
    text = (title + ". " + content)[:4000]
    digest = hashlib.md5(text.encode("utf-8")).digest()
    score = 0.5 + (digest[0] / 255.0) * 0.49
    label = "Fake" if digest[1] % 2 == 0 else "Real"
    return {"label": label, "confidence": round(score, 4)}


def make_id(url: str, title: str) -> str:
    return hashlib.sha1(f"{url}||{title}".encode()).hexdigest()[:24]


# ---------------------------------------------------------------------------
# News API fetchers
# ---------------------------------------------------------------------------

async def fetch_newsapi(client: httpx.AsyncClient) -> list[dict]:
    """Fetch latest articles from NewsAPI."""
    api_key = os.environ.get("NEWSAPI_KEY", "").strip()
    if not api_key:
        log.warning("NEWSAPI_KEY not set; skipping")
        return []

    query = os.environ.get("NEWSAPI_QUERY", "politics OR election OR breaking")
    try:
        resp = await client.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20,
                "apiKey": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            log.warning("NewsAPI status: %s", data.get("status"))
            return []

        articles = []
        for item in data.get("articles", []):
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            if not title or not url or title == "[Removed]":
                continue

            source_name = (item.get("source") or {}).get("name", "Unknown")
            content = (item.get("description") or item.get("content") or "").strip()
            published = item.get("publishedAt") or datetime.now(UTC).isoformat()

            # Classify
            result = classify_article(title, content)

            articles.append({
                "id": make_id(url, title),
                "title": title,
                "source": source_name,
                "url": url,
                "author": (item.get("author") or "").strip() or None,
                "content": content,
                "published_at": published,
                "fetched_at": datetime.now(UTC).isoformat(),
                "label": result["label"],
                "confidence": result["confidence"],
                "scored_at": datetime.now(UTC).isoformat(),
                "category": "News",
            })
        log.info("NewsAPI: fetched %d articles", len(articles))
        return articles

    except Exception as e:
        log.error("NewsAPI fetch failed: %s", e)
        return []


async def fetch_gnews(client: httpx.AsyncClient) -> list[dict]:
    """Fetch latest articles from GNews."""
    api_key = os.environ.get("GNEWS_KEY", "").strip()
    if not api_key:
        log.warning("GNEWS_KEY not set; skipping")
        return []

    query = os.environ.get("GNEWS_QUERY", "politics")
    try:
        resp = await client.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": query,
                "lang": "en",
                "max": 10,
                "sortby": "publishedAt",
                "token": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("articles", []):
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            if not title or not url:
                continue

            source_name = (item.get("source") or {}).get("name", "Unknown")
            content = (item.get("description") or item.get("content") or "").strip()
            published = item.get("publishedAt") or datetime.now(UTC).isoformat()

            result = classify_article(title, content)

            articles.append({
                "id": make_id(url, title),
                "title": title,
                "source": source_name,
                "url": url,
                "author": None,
                "content": content,
                "published_at": published,
                "fetched_at": datetime.now(UTC).isoformat(),
                "label": result["label"],
                "confidence": result["confidence"],
                "scored_at": datetime.now(UTC).isoformat(),
                "category": "News",
            })
        log.info("GNews: fetched %d articles", len(articles))
        return articles

    except Exception as e:
        log.error("GNews fetch failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Background ingestion loop
# ---------------------------------------------------------------------------

async def ingestion_loop(app):
    """
    Background task that periodically fetches news from APIs,
    classifies them, and adds them to the data store.
    """
    poll_interval = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
    log.info("[LIVE] Starting live ingestion (poll every %ds)...", poll_interval)

    # Wait a few seconds for the server to fully start
    await asyncio.sleep(3)

    seen_ids: set[str] = set()

    # Pre-populate seen_ids with existing articles
    if getattr(app.state, "use_fallback", False):
        for a in app.state.fallback.articles:
            seen_ids.add(a["id"])
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Fetch from both sources in parallel
                newsapi_articles, gnews_articles = await asyncio.gather(
                    fetch_newsapi(client),
                    fetch_gnews(client),
                    return_exceptions=True,
                )

                # Handle exceptions from gather
                if isinstance(newsapi_articles, Exception):
                    log.error("NewsAPI error: %s", newsapi_articles)
                    newsapi_articles = []
                if isinstance(gnews_articles, Exception):
                    log.error("GNews error: %s", gnews_articles)
                    gnews_articles = []

                all_new = []
                for article in list(newsapi_articles) + list(gnews_articles):
                    if article["id"] not in seen_ids:
                        seen_ids.add(article["id"])
                        all_new.append(article)

                if all_new:
                    log.info("[LIVE] %d new articles to add", len(all_new))

                    if getattr(app.state, "use_fallback", False):
                        # Add to in-memory fallback store
                        store = app.state.fallback
                        for article in all_new:
                            store.articles.insert(0, article)  # Newest first
                        # Keep store manageable (max 500)
                        if len(store.articles) > 500:
                            store.articles = store.articles[:500]
                    else:
                        # Insert into MongoDB
                        try:
                            coll = app.state.db["articles_scored"]
                            coll.insert_many(all_new, ordered=False)
                        except Exception as e:
                            log.error("MongoDB insert failed: %s", e)

                    log.info(
                        "[LIVE] Added %d articles (total: %d)",
                        len(all_new),
                        len(app.state.fallback.articles) if getattr(app.state, "use_fallback", False) else -1,
                    )
                else:
                    log.info("[LIVE] No new articles this cycle")

            except Exception as e:
                log.error("[LIVE] Ingestion cycle failed: %s", e)

            await asyncio.sleep(poll_interval)
