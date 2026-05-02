#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Creating Kafka topics..."
bash "$(dirname "$0")/create-topics.sh"

echo "[2/3] Creating MongoDB indexes..."
docker compose exec -T mongo mongosh --quiet --eval '
  const db = db.getSiblingDB("truthstream");
  db.articles_scored.createIndex({ id: 1 }, { unique: true });
  db.articles_scored.createIndex({ published_at: -1 });
  db.articles_scored.createIndex({ label: 1, published_at: -1 });
  db.articles_scored.createIndex({ source: 1, published_at: -1 });
  print("indexes:", JSON.stringify(db.articles_scored.getIndexes()));
'

echo "[3/3] Lake directories..."
mkdir -p storage/lake/bronze storage/lake/silver storage/lake/gold storage/checkpoints

echo "Bootstrap complete."
