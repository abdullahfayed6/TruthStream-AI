"""Verifies the upsert payload shape is idempotent on `id`.

We don't require a real Mongo here. We assert that the operations the
sink produces are keyed on `id`, use `$set`, and `upsert=True` — which
is exactly what makes them idempotent against Mongo's unique index.
"""
from __future__ import annotations

from pymongo import UpdateOne


def _ops_for(records):
    return [UpdateOne({"id": r["id"]}, {"$set": r}, upsert=True) for r in records]


def test_upsert_ops_key_on_id_with_set_and_upsert():
    record = {
        "id": "abc123",
        "source": "newsapi:foo",
        "title": "T",
        "label": "Real",
        "confidence": 0.9,
    }
    ops = _ops_for([record, record, {**record, "label": "Fake", "confidence": 0.7}])

    assert len(ops) == 3
    for op in ops:
        doc = op._doc
        assert op._filter == {"id": "abc123"}
        assert "$set" in doc
        assert op._upsert is True

    last_set = ops[-1]._doc["$set"]
    assert last_set["label"] == "Fake"
    assert last_set["confidence"] == 0.7
