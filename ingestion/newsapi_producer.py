from __future__ import annotations

import logging
import os
from collections.abc import Iterable

import requests

from .producer_base import BaseProducer, configure_logging
from .schema import Article, build_article

log = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_newsapi() -> Iterable[Article]:
    api_key = os.environ.get("NEWSAPI_KEY", "").strip()
    if not api_key:
        log.warning("NEWSAPI_KEY not set; skipping fetch")
        return []

    query = os.environ.get("NEWSAPI_QUERY", "politics OR election OR breaking")
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "apiKey": api_key,
    }
    resp = requests.get(NEWSAPI_URL, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        log.warning("NewsAPI returned %s", payload)
        return []

    out: list[Article] = []
    for item in payload.get("articles", []):
        article = build_article(
            source=f"newsapi:{(item.get('source') or {}).get('name', 'unknown')}",
            title=item.get("title"),
            content=item.get("description") or item.get("content"),
            url=item.get("url"),
            published_at=item.get("publishedAt"),
        )
        if article is not None:
            out.append(article)
    return out


def main() -> None:
    configure_logging()
    BaseProducer(
        name="newsapi",
        topic=os.environ.get("TOPIC_RAW", "news.raw"),
        fetch=fetch_newsapi,
    ).run()


if __name__ == "__main__":
    main()
