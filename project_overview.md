# TruthStream AI — Project Overview & Health Report

## What Is This Project?

**TruthStream AI** is a real-time fake-news detection platform built as a graduation project to demonstrate Big Data architecture. It detects fake news using a DistilBERT classifier running inside Spark, with a full medallion data lake backed by Kafka, MongoDB, and Parquet.

---

## Architecture

```
NewsAPI / GNews  →  Kafka (news.raw, 6 partitions)
                          │
                          ▼
                Spark Structured Streaming
                  ├── clean_job   → Bronze Parquet (raw) + Silver Parquet (cleaned)
                  └── score_job   → DistilBERT UDF
                                       ├── Gold Parquet
                                       └── Kafka (news.scored)
                                                   │
                                                   ▼
                                             mongo-sink consumer
                                                   │
                                                   ▼
                                         MongoDB articles_scored
```

---

## Services (Docker Compose)

| Service | Image | Port | Status |
|---|---|---|---|
| zookeeper | confluentinc/cp-zookeeper:7.5.0 | 2181 | ✅ healthy |
| kafka | confluentinc/cp-kafka:7.5.0 | 9092, 29092 | ✅ healthy |
| kafka-ui | provectuslabs/kafka-ui | 8080 | ✅ up |
| mongo | mongo:7 | 27017 | ✅ healthy |
| mongo-express | mongo-express:1.0.2 | 8081 | ✅ up |
| spark-master | truthstream-spark:3.5.3 | 8090, 7077 | ✅ up |
| spark-worker-1 | truthstream-spark:3.5.3 | — | ✅ up |
| spark-worker-2 | truthstream-spark:3.5.3 | — | ✅ up |
| newsapi-producer | custom | — | ✅ up, publishing articles |
| gnews-producer | custom | — | ✅ up |
| mongo-sink | custom | — | ✅ up, consuming news.scored |

---

## Pipeline Status (as of test run)

| Stage | Evidence | Status |
|---|---|---|
| **Kafka topics** | `news.raw` (6 partitions), `news.scored` (3 partitions) | ✅ exist |
| **news.raw messages** | 153 total messages across 6 partitions | ✅ flowing |
| **news.scored messages** | 0 messages (score_job running, waiting for Silver data) | ⚠️ pending (expected — score job registered at 08:40) |
| **Bronze/Silver Parquet** | 165+ Parquet files under `/opt/lake/silver/date=2026-05-01/` | ✅ writing |
| **Producers** | newsapi-producer publishing batches (e.g., 18 articles at 09:02) | ✅ active |
| **MongoDB** | articles_scored: 0 docs (waiting for scored Kafka messages) | ⚠️ pending |
| **Spark apps** | `truthstream-clean` and `truthstream-score` both registered | ✅ running |

> **Why is `news.scored` empty?** The `score_job` was started ~7 minutes after clean_job and reads the Silver parquet stream. It uses the fallback dummy DistilBERT classifier (no trained model weights exist yet). Scored articles will appear in MongoDB once the next 30-second trigger fires on Silver files.

---

## Unit Tests — ✅ All 10 PASSED

```
tests/unit/test_inference_fallback.py   ..   (2 tests)
tests/unit/test_mongo_sink_idempotency.py  .   (1 test)
tests/unit/test_normalize_text.py       ...  (3 tests)
tests/unit/test_schema.py               ....  (4 tests)

10 passed in 5.73s
```

### What each test validates
| Test file | What it checks |
|---|---|
| `test_schema.py` | `stable_id()` is deterministic & 24 chars; `build_article()` rejects missing URL/title; `published_at` normalization |
| `test_normalize_text.py` | Whitespace collapse, `None`/empty handling, punctuation preservation |
| `test_inference_fallback.py` | Fallback classifier returns correct columns, valid label set, confidence range [0.5–0.99], determinism |
| `test_mongo_sink_idempotency.py` | `UpdateOne` ops are keyed on `id`, use `$set`, have `upsert=True` |

---

## Module Breakdown

| Module | Files | Purpose |
|---|---|---|
| `ingestion/` | `newsapi_producer.py`, `gnews_producer.py`, `producer_base.py`, `schema.py` | Poll APIs every 60s, publish JSON to `news.raw` |
| `streaming/` | `clean_job.py`, `score_job.py`, `common.py`, `text_utils.py` | Spark Structured Streaming: clean → Bronze/Silver; score → Gold + Kafka |
| `ml/` | `inference.py`, `fallback.py`, `train/` | DistilBERT Pandas UDF + deterministic fallback (no weights yet) |
| `sink/` | `mongo_sink.py` | Kafka consumer → MongoDB bulk upsert (idempotent on `id`) |
| `tests/unit/` | 4 test files | Fast, PySpark-free unit tests |
| `tests/integration/` | `test_pipeline_smoke.py` | Requires running stack (Kafka + Mongo) |
| `scripts/` | `create-topics.sh`, `bootstrap.sh`, `submit-jobs.sh` | Operational scripts |

---

## What's NOT Yet Implemented (Tracked in plan.md)

| Feature | Status |
|---|---|
| DistilBERT fine-tuned weights | ❌ `ml/models/` is empty; fallback classifier used |
| OpenAI explanation layer | ❌ `openai_layer/` directory doesn't exist yet |
| Streamlit dashboard | ❌ `dashboard/` directory doesn't exist yet |
| Gold Parquet + MongoDB documents | ⚠️ Will flow once `score_job` trigger fires |
| Integration tests (requires live stack) | ⚠️ Not run (need `kafka-python` + live Kafka for integration) |

---

## Quick-Access URLs (while stack is running)

| UI | URL |
|---|---|
| Kafka UI | http://localhost:8080 |
| Mongo Express | http://localhost:8081 |
| Spark Master UI | http://localhost:8090 |

