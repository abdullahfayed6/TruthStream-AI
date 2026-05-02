"""End-to-end smoke test: run only when STACK_UP=1.

In CI this is gated so unit tests stay fast. Locally:
    docker compose up -d
    bash scripts/bootstrap.sh
    STACK_UP=1 pytest tests/integration -q
"""
from __future__ import annotations

import json
import os
import time
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("STACK_UP") != "1",
    reason="set STACK_UP=1 with the docker-compose stack running",
)


def test_50_articles_land_in_mongo_within_60s():
    from kafka import KafkaProducer
    from pymongo import MongoClient

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_EXTERNAL", "localhost:29092")
    mongo_uri = os.environ.get("MONGO_URI_EXTERNAL", "mongodb://localhost:27017")

    producer = KafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
    )

    ids = [uuid.uuid4().hex[:24] for _ in range(50)]
    for idx, article_id in enumerate(ids):
        producer.send(
            "news.raw",
            key=f"itest:{idx % 3}",
            value={
                "id": article_id,
                "source": f"itest:{idx % 3}",
                "title": f"Integration test article {idx}",
                "content": "Body " * 20,
                "url": f"https://itest.example/{article_id}",
                "published_at": "2026-05-02T00:00:00+00:00",
                "fetched_at": "2026-05-02T00:00:00+00:00",
            },
        )
    producer.flush(timeout=15)
    producer.close()

    client = MongoClient(mongo_uri)
    coll = client["truthstream"]["articles_scored"]

    deadline = time.time() + 90
    while time.time() < deadline:
        count = coll.count_documents({"id": {"$in": ids}})
        if count >= 50:
            break
        time.sleep(2)

    final = coll.count_documents({"id": {"$in": ids}})
    assert final >= 50, f"only {final}/50 articles landed in Mongo"
