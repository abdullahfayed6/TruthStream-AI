"""Pure-Python text helpers, importable without PySpark on the path.

Spark jobs re-export from here via ``streaming.common`` so unit tests can
exercise the cleanup logic without booting a Spark session.
"""
from __future__ import annotations

import re

_NON_TEXT_RE = re.compile(r"[\r\n\t]+")
_MULTI_SPACE_RE = re.compile(r"\s{2,}")


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _NON_TEXT_RE.sub(" ", value)
    cleaned = _MULTI_SPACE_RE.sub(" ", cleaned).strip()
    return cleaned or None
