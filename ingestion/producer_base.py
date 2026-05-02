from __future__ import annotations

import json
import logging
import os
import signal
import time
from collections import deque
from collections.abc import Callable, Iterable

from kafka import KafkaProducer
from kafka.errors import KafkaError

from .schema import Article

log = logging.getLogger(__name__)


class BaseProducer:
    """Polls a fetch function on an interval and publishes Articles to Kafka.

    Dedupe is best-effort within a sliding window of recent IDs to avoid
    re-publishing the same article every poll cycle. Spark also dedupes
    downstream by `id`, so this is purely a bandwidth optimization.
    """

    def __init__(
        self,
        *,
        name: str,
        topic: str,
        fetch: Callable[[], Iterable[Article]],
        bootstrap: str | None = None,
        poll_seconds: int | None = None,
        dedupe_window: int = 5000,
    ) -> None:
        self.name = name
        self.topic = topic
        self.fetch = fetch
        self.bootstrap = bootstrap or os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
        self.poll_seconds = poll_seconds or int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
        self._seen: deque[str] = deque(maxlen=dedupe_window)
        self._seen_set: set[str] = set()
        self._stop = False
        self._producer: KafkaProducer | None = None

    def _connect(self) -> KafkaProducer:
        for attempt in range(1, 11):
            try:
                return KafkaProducer(
                    bootstrap_servers=self.bootstrap,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: k.encode("utf-8") if k else None,
                    acks="all",
                    linger_ms=200,
                    retries=5,
                )
            except KafkaError as exc:
                log.warning("Kafka not ready (attempt %d): %s", attempt, exc)
                time.sleep(min(30, attempt * 2))
        raise RuntimeError("Could not connect to Kafka")

    def _remember(self, article_id: str) -> bool:
        if article_id in self._seen_set:
            return False
        if len(self._seen) == self._seen.maxlen:
            evicted = self._seen[0]
            self._seen_set.discard(evicted)
        self._seen.append(article_id)
        self._seen_set.add(article_id)
        return True

    def _shutdown(self, *_: object) -> None:
        log.info("[%s] shutdown requested", self.name)
        self._stop = True

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        self._producer = self._connect()
        log.info("[%s] connected to %s, topic=%s, interval=%ds",
                 self.name, self.bootstrap, self.topic, self.poll_seconds)

        while not self._stop:
            published = 0
            try:
                for article in self.fetch():
                    if not self._remember(article.id):
                        continue
                    self._producer.send(
                        self.topic,
                        key=article.source,
                        value=article.to_json(),
                    )
                    published += 1
                self._producer.flush(timeout=10)
                log.info("[%s] published %d new articles", self.name, published)
            except Exception as exc:  # noqa: BLE001
                log.exception("[%s] poll cycle failed: %s", self.name, exc)

            for _ in range(self.poll_seconds):
                if self._stop:
                    break
                time.sleep(1)

        if self._producer is not None:
            self._producer.flush(timeout=10)
            self._producer.close(timeout=10)
        log.info("[%s] stopped", self.name)


def configure_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
