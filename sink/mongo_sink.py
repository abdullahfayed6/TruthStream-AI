"""Reads news.scored from Kafka and upserts records into Mongo.

Idempotency: each upsert keys on `id`, so replays from Kafka are safe.
Indexes are created at startup if missing.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import time

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from pymongo import ASCENDING, DESCENDING, MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

log = logging.getLogger(__name__)

BATCH_SIZE = 64
FLUSH_SECONDS = 5


def configure_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def ensure_indexes(coll) -> None:
    coll.create_index([("id", ASCENDING)], unique=True)
    coll.create_index([("published_at", DESCENDING)])
    coll.create_index([("label", ASCENDING), ("published_at", DESCENDING)])
    coll.create_index([("source", ASCENDING), ("published_at", DESCENDING)])


def connect_consumer() -> KafkaConsumer:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
    topic = os.environ.get("TOPIC_SCORED", "news.scored")
    for attempt in range(1, 11):
        try:
            return KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap,
                group_id="mongo-sink",
                enable_auto_commit=True,
                auto_offset_reset="earliest",
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )
        except KafkaError as exc:
            log.warning("Kafka not ready (attempt %d): %s", attempt, exc)
            time.sleep(min(30, attempt * 2))
    raise RuntimeError("Could not connect to Kafka")


_stop = False


def _shutdown(*_: object) -> None:
    global _stop
    log.info("shutdown requested")
    _stop = True


def flush(coll, buffer: list[dict]) -> None:
    if not buffer:
        return
    ops = [UpdateOne({"id": rec["id"]}, {"$set": rec}, upsert=True) for rec in buffer]
    try:
        result = coll.bulk_write(ops, ordered=False)
        log.info(
            "upserted matched=%d modified=%d upserted=%d",
            result.matched_count,
            result.modified_count,
            len(result.upserted_ids),
        )
    except BulkWriteError as exc:
        log.error("bulk write error: %s", exc.details)


def main() -> None:
    configure_logging()
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    mongo_uri = os.environ.get("MONGO_URI", "mongodb://mongo:27017")
    db_name = os.environ.get("MONGO_DB", "truthstream")
    coll_name = os.environ.get("MONGO_COLLECTION", "articles_scored")

    client = MongoClient(mongo_uri)
    coll = client[db_name][coll_name]
    ensure_indexes(coll)
    log.info("connected to %s/%s.%s", mongo_uri, db_name, coll_name)

    consumer = connect_consumer()
    log.info("consuming topic=%s", consumer.subscription())

    buffer: list[dict] = []
    last_flush = time.time()

    while not _stop:
        msgs = consumer.poll(timeout_ms=1000, max_records=BATCH_SIZE)
        for _, records in msgs.items():
            for rec in records:
                value = rec.value
                if not isinstance(value, dict) or "id" not in value:
                    continue
                buffer.append(value)

        now = time.time()
        if len(buffer) >= BATCH_SIZE or (buffer and now - last_flush >= FLUSH_SECONDS):
            flush(coll, buffer)
            buffer.clear()
            last_flush = now

    flush(coll, buffer)
    consumer.close()
    client.close()
    log.info("stopped")


if __name__ == "__main__":
    main()
