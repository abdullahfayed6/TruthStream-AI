from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class Article:
    id: str
    source: str
    title: str
    content: str
    url: str
    published_at: str
    fetched_at: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def stable_id(url: str, title: str) -> str:
    h = hashlib.sha1(f"{url}||{title}".encode()).hexdigest()
    return h[:24]


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def normalize_published(value: str | None) -> str:
    if not value:
        return now_iso()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat()
    except ValueError:
        return now_iso()


def build_article(
    *,
    source: str,
    title: str | None,
    content: str | None,
    url: str | None,
    published_at: str | None,
) -> Article | None:
    if not url or not title:
        return None
    body = (content or "").strip()
    return Article(
        id=stable_id(url, title),
        source=source,
        title=title.strip(),
        content=body,
        url=url,
        published_at=normalize_published(published_at),
        fetched_at=now_iso(),
    )
