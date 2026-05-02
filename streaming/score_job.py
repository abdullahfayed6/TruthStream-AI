"""Stage: Silver Parquet -> DistilBERT scoring -> Gold Parquet + news.scored Kafka.

Reads the silver parquet stream, applies a pandas_udf-backed classifier
once per executor, writes Gold and publishes the same record to Kafka so
the Mongo sink can pick it up.
"""
from __future__ import annotations

import os

from pyspark.sql import functions as F

# `ml.inference` exposes a Pandas UDF; keeping import lazy avoids loading
# transformers in the driver before the executors fan out.
from ml.inference import score_udf
from streaming.common import checkpoint_path, get_spark, lake_path


def main() -> None:
    spark = get_spark("truthstream-score")

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
    topic_scored = os.environ.get("TOPIC_SCORED", "news.scored")
    trigger_seconds = os.environ.get("TRIGGER_SECONDS", "30")

    silver_stream = (
        spark.readStream.format("parquet")
        .schema(spark.read.parquet(lake_path("silver")).schema if _silver_exists() else _fallback_schema())
        .option("path", lake_path("silver"))
        .option("maxFilesPerTrigger", "16")
        .load()
    )

    scored = silver_stream.withColumn(
        "prediction",
        score_udf(F.col("title"), F.col("content")),
    ).select(
        "id",
        "source",
        "title",
        "content",
        "url",
        "published_at",
        "fetched_at",
        "date",
        F.col("prediction.label").alias("label"),
        F.col("prediction.confidence").alias("confidence"),
        F.current_timestamp().alias("scored_at"),
    )

    gold_query = (
        scored.writeStream.format("parquet")
        .option("path", lake_path("gold"))
        .option("checkpointLocation", checkpoint_path("gold"))
        .partitionBy("date", "label")
        .outputMode("append")
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .start()
    )

    kafka_payload = scored.select(
        F.col("id").alias("key"),
        F.to_json(F.struct(*scored.columns)).alias("value"),
    )

    kafka_query = (
        kafka_payload.writeStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap)
        .option("topic", topic_scored)
        .option("checkpointLocation", checkpoint_path("kafka_scored"))
        .outputMode("append")
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .start()
    )

    spark.streams.awaitAnyTermination()
    gold_query.stop()
    kafka_query.stop()


def _silver_exists() -> bool:
    path = lake_path("silver")
    return os.path.isdir(path) and any(os.scandir(path))


def _fallback_schema():
    from pyspark.sql.types import DateType, StringType, StructField, StructType, TimestampType

    return StructType(
        [
            StructField("id", StringType(), False),
            StructField("source", StringType(), True),
            StructField("title", StringType(), True),
            StructField("content", StringType(), True),
            StructField("url", StringType(), True),
            StructField("published_at", StringType(), True),
            StructField("fetched_at", StringType(), True),
            StructField("kafka_key", StringType(), True),
            StructField("kafka_ts", TimestampType(), True),
            StructField("lang_guess", StringType(), True),
            StructField("date", DateType(), True),
        ]
    )


if __name__ == "__main__":
    main()
