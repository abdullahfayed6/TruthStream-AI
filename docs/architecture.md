# TruthStream AI — Architecture

## Stages

```
[NewsAPI / GNews]
        │  REST poll every 60s
        ▼
[Producer containers]   --->   Kafka topic: news.raw  (6 partitions, key=source)
                                          │
                                          ▼
                              [Spark Structured Streaming]
                              clean_job.py
                              ├──> Bronze Parquet  (raw, partitioned by date/source)
                              └──> Silver Parquet  (cleaned, deduped, en-only)
                                          │
                                          ▼
                              score_job.py
                              ├── DistilBERT Pandas UDF
                              ├──> Gold Parquet (scored, partitioned by date/label)
                              └──> Kafka topic: news.scored (3 partitions)
                                                          │
                                                          ▼
                                              [Mongo sink consumer]
                                              upsert by id (idempotent)
                                                          │
                                                          ▼
                                              MongoDB.articles_scored
                                                          │
                                                          ▼
                                              [Streamlit dashboard]  (planned)
                                                          │
                                                          ▼
                                              OpenAI explain/summarize/rewrite (planned)
```

## Layer responsibilities

| Layer        | Where                       | Output                                  |
|--------------|-----------------------------|------------------------------------------|
| Ingestion    | `ingestion/`                | JSON to `news.raw`                       |
| Streaming    | `streaming/clean_job.py`    | Bronze + Silver Parquet                  |
| ML inference | `ml/inference.py` (UDF)     | label + confidence                       |
| Streaming    | `streaming/score_job.py`    | Gold Parquet + `news.scored`             |
| Serving      | `sink/mongo_sink.py`        | Upserts in `articles_scored`             |
| Presentation | `dashboard/` (planned)      | Live feed, stats, OpenAI on demand       |

## Why this shape

- **Kafka, not direct API → DB**: replayable log, smooths upstream API spikes, lets Spark consume at its own pace, lets us add new consumers without changing producers.
- **Spark Structured Streaming, not Pandas**: parallel partitions, windowed aggregations, exactly-once with checkpoints, can scale horizontally by adding workers.
- **Parquet medallion (bronze/silver/gold)**: raw is preserved for replay/audit; silver is the canonical clean layer; gold is the scored, presentation-ready layer.
- **MongoDB for serving**: low-latency document reads, JSON-shaped, easy to index by `published_at` / `label` / `source`.

## Scalability story

- `news.raw` has 6 partitions keyed by `source`, so traffic spreads across consumers.
- `spark.sql.shuffle.partitions=6` matches partition count.
- Adding workers (`spark-worker-3`, ...) increases throughput linearly until a partition becomes the bottleneck — at which point we increase Kafka partitions and `shuffle.partitions` together.
- Load test (`tests/load/locust_producer.py`) drives ~1000 msg/s and verifies consumer lag stays < 5k.

## Exactly-once semantics

Each Spark streaming sink has a dedicated checkpoint directory under `storage/checkpoints/`. On restart, Spark resumes from the last committed offset, so Bronze, Silver, Gold, and the Kafka `news.scored` write are not duplicated.

The Mongo sink upserts on `id`, so even if Kafka delivers a `news.scored` record twice, the document is written exactly once.

## End-to-end timing example

| T+   | Event                                                            |
|------|------------------------------------------------------------------|
| 0s   | NewsAPI returns headline X                                        |
| 1s   | Producer publishes to `news.raw`                                  |
| ~10s | Spark micro-batch picks it up, writes Bronze + Silver             |
| ~12s | Score job classifies (DistilBERT, conf 0.91), writes Gold + Kafka |
| ~13s | Mongo sink upserts into `articles_scored`                         |
| ~30s | Dashboard auto-refresh shows it (planned)                         |
| ~32s | User clicks "Explain", OpenAI returns rationale (planned)         |
