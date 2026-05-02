#!/usr/bin/env bash
set -euo pipefail

BROKER="${KAFKA_BOOTSTRAP:-kafka:9092}"
RAW="${TOPIC_RAW:-news.raw}"
SCORED="${TOPIC_SCORED:-news.scored}"

echo "Creating topics on $BROKER..."

docker compose exec -T kafka kafka-topics \
  --bootstrap-server "$BROKER" \
  --create --if-not-exists \
  --topic "$RAW" \
  --partitions 6 --replication-factor 1

docker compose exec -T kafka kafka-topics \
  --bootstrap-server "$BROKER" \
  --create --if-not-exists \
  --topic "$SCORED" \
  --partitions 3 --replication-factor 1

echo "Topics:"
docker compose exec -T kafka kafka-topics --bootstrap-server "$BROKER" --list
