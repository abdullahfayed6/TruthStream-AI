# Why Big Data tooling, not just Pandas

A common critique of student NLP projects is "this is just an ML notebook in a trench coat." This document is the rebuttal: each tool does work that Pandas-on-one-machine cannot.

## Velocity — Kafka

- `news.raw` is a **replayable log**. If we deploy a new model or a fixed cleaning rule, we replay from offset 0 and rebuild Silver/Gold without re-fetching from NewsAPI.
- Producers and consumers are decoupled. NewsAPI has rate limits; Spark may stall briefly during a code reload. The Kafka log absorbs both sides' jitter.
- Multiple downstream consumers (Spark + Mongo sink + dashboard) each track their own offset. Adding a new consumer doesn't change producers.

A direct `requests → Mongo.insertOne()` pipeline has none of these properties.

## Volume — Parquet data lake

- Articles accumulate indefinitely. At ~10k/day a year is ~3.6M rows — fine for Pandas, but Bronze also stores the raw payload, so total bytes get into hundreds of GB territory across history.
- Parquet is **columnar + compressed + schema-on-read**. Queries that touch only `published_at` and `label` skip 80% of the file.
- Partitioning by `date=…/source=…` means a query for "yesterday, NewsAPI" reads exactly one partition.

Pandas reading a yearly CSV is `O(file size)` regardless of which columns you want.

## Variety — multi-source ingestion

- NewsAPI and GNews ship different JSON shapes (`source.name` vs `source: {...}`, `description` vs `content`). The producer normalizes to a single schema (`ingestion/schema.py`) before publishing.
- Adding Reddit, Twitter, or RSS later means writing one more producer that emits the same schema — no changes to Spark or Mongo.
- Schema-on-write at the ingestion edge + schema-on-read in the lake gives us forward compatibility (a new optional field doesn't break old readers).

## Distributed processing — Spark

- `pandas_udf` runs the DistilBERT model **once per executor**, batches rows of 32, and parallelizes across the cluster. With 2 workers × 2 cores we get 4× the inference throughput of a single Pandas loop, and adding workers is a config change.
- Stateful streaming (windowed aggregates, watermarks) is supported natively. A "fake-news rate per source over the last hour" query is one line; in Pandas you'd hand-roll buffer management.
- Exactly-once via checkpoints is built in. Pandas pipelines have no notion of checkpoints — a crash mid-write means dedupe-by-hand on restart.

## Common big-data anti-patterns this project deliberately avoids

- ❌ Loading the model per row → ✅ module-level singleton inside the UDF.
- ❌ `.toPandas()` on the whole stream → ✅ `pandas_udf` so partitions stay distributed.
- ❌ Single-partition Kafka topic → ✅ 6 partitions keyed by `source`.
- ❌ One Parquet file per micro-batch (small-files problem) → ✅ `trigger(processingTime='30 seconds')` plus partition layout.
- ❌ Calling OpenAI inside the Spark UDF → ✅ OpenAI is dashboard-on-demand only, never on the hot path.
- ❌ No dedupe → ✅ stable hash IDs at ingestion + `dropDuplicates(["id"])` in Silver + Mongo unique index on `id`.
- ❌ No checkpoint dir → ✅ each sink has its own under `/opt/checkpoints/`.
