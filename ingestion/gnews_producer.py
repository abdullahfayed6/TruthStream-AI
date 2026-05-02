from __future__ import annotations

import logging
import os
from collections.abc import Iterable

import requests

from .producer_base import BaseProducer, configure_logging
from .schema import Article, build_article

log = logging.getLogger(__name__)

GNEWS_URL = "https://gnews.io/api/v4/search"


def fetch_gnews() -> Iterable[Article]:
    api_key = os.environ.get("GNEWS_KEY", "").strip()
    if not api_key:
        log.warning("GNEWS_KEY not set; skipping fetch")
        return []

    query = os.environ.get("GNEWS_QUERY", "politics")
    params = {
        "q": query,
        "lang": "en",
        "max": 50,
        "sortby": "publishedAt",
        "token": api_key,
    }
    resp = requests.get(GNEWS_URL, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    out: list[Article] = []
    for item in payload.get("articles", []):
        source_name = ((item.get("source") or {}).get("name")) or "unknown"
        article = build_article(
            source=f"gnews:{source_name}",
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
        name="gnews",
        topic=os.environ.get("TOPIC_RAW", "news.raw"),
        fetch=fetch_gnews,
    ).run()


if __name__ == "__main__":
    main()
