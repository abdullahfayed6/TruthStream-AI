# TruthStream AI

Real-time fake-news detection over Kafka + Spark + a Parquet data lake, with a fine-tuned DistilBERT classifier serving results into MongoDB.

This repo currently ships the **Big Data backbone**: ingestion producers, Spark Structured Streaming jobs (clean + score), medallion lake (bronze/silver/gold), Mongo sink, training script, tests, CI. The OpenAI explanation layer and Streamlit dashboard are tracked in `plan.md` and not yet implemented.

## Quick start

```bash
cp .env.example .env          # add your NewsAPI / GNews keys
docker compose up -d --build
bash scripts/create-topics.sh
bash scripts/bootstrap.sh
```

Then watch:

- Kafka UI: http://localhost:8080
- Mongo Express: http://localhost:8081
- Spark master UI: http://localhost:8090

## Architecture

```
NewsAPI / GNews  -->  Kafka (news.raw, 6 partitions)
                          |
                          v
                Spark Structured Streaming
                  ├── clean_job  ──>  Bronze + Silver Parquet
                  └── score_job  ──>  DistilBERT UDF
                                       ├── Gold Parquet
                                       └── Kafka (news.scored)
                                                   |
                                                   v
                                             Mongo sink
                                                   |
                                                   v
                                       MongoDB (articles_scored)
```

See `docs/architecture.md` and `docs/why-bigdata.md`.

## Layout

```
truthstream-ai/
├── docker-compose.yml
├── .env.example
├── docs/
├── ingestion/
├── streaming/
├── ml/
├── storage/lake/
├── tests/
├── scripts/
└── .github/workflows/
```

## Running individual pieces

```bash
# submit clean job
docker compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  /opt/app/streaming/clean_job.py

# submit score job
docker compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  /opt/app/streaming/score_job.py
```

## Training the classifier

```bash
python ml/train/finetune_distilbert.py --output ml/models/distilbert-fakenews
```

Until weights exist, `ml/inference.py` falls back to a deterministic dummy classifier so the pipeline still flows end-to-end.

## Tests

```bash
pytest -q
```

Load test (requires running stack):

```bash
locust -f tests/load/locust_producer.py --headless -u 100 -r 10 -t 5m
```
