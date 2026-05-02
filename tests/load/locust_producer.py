"""Locust load test that drives synthetic articles directly into Kafka.

Run against a running stack:
    locust -f tests/load/locust_producer.py --headless -u 100 -r 10 -t 5m

Each "user" sends one article per `wait_time`. With 100 users at ~0.1s
that's ~1000 msg/s into news.raw. Verify Kafka lag stays < 5k via Kafka UI.
"""
from __future__ import annotations

import json
import os
import random
import time
import uuid

from kafka import KafkaProducer
from locust import User, between, events, task

_producer: KafkaProducer | None = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        bootstrap = os.environ.get("KAFKA_BOOTSTRAP_EXTERNAL", "localhost:29092")
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="1",
            linger_ms=50,
            compression_type="lz4",
        )
    return _producer


HEADLINES = [
    "Breaking news in politics shakes voters",
    "Scientists discover new species in deep ocean",
    "Tech giant announces major layoffs amid restructure",
    "Local team wins championship after 30 years",
    "Investigation reveals corruption in city hall",
]


class KafkaUser(User):
    wait_time = between(0.05, 0.15)

    @task
    def send(self):
        topic = os.environ.get("TOPIC_RAW", "news.raw")
        article_id = uuid.uuid4().hex[:24]
        payload = {
            "id": article_id,
            "source": f"loadtest:user{random.randint(1, 9)}",
            "title": random.choice(HEADLINES),
            "content": "Synthetic content for load test " * 10,
            "url": f"https://loadtest.example/{article_id}",
            "published_at": "2026-05-02T00:00:00+00:00",
            "fetched_at": "2026-05-02T00:00:00+00:00",
        }
        start = time.time()
        try:
            future = get_producer().send(topic, key=payload["source"], value=payload)
            future.get(timeout=10)
            events.request.fire(
                request_type="kafka",
                name="produce",
                response_time=(time.time() - start) * 1000,
                response_length=len(json.dumps(payload)),
                exception=None,
                context={},
            )
        except Exception as exc:  # noqa: BLE001
            events.request.fire(
                request_type="kafka",
                name="produce",
                response_time=(time.time() - start) * 1000,
                response_length=0,
                exception=exc,
                context={},
            )
