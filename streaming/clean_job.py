"""Stage: news.raw -> Bronze Parquet (raw) -> Silver Parquet (cleaned).

Reads JSON from Kafka, parses against RAW_SCHEMA, writes a verbatim
Bronze copy and a cleaned/deduped Silver copy partitioned by date/source.
"""
from __future__ import annotations

import os

from pyspark.sql import functions as F

from streaming.common import (
    RAW_SCHEMA,
    checkpoint_path,
    get_spark,
    lake_path,
)


def main() -> None:
    spark = get_spark("truthstream-clean")

    bootstrap = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
    topic = os.environ.get("TOPIC_RAW", "news.raw")
    trigger_seconds = os.environ.get("TRIGGER_SECONDS", "30")

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed = (
        raw_stream.select(
            F.col("key").cast("string").alias("kafka_key"),
            F.from_json(F.col("value").cast("string"), RAW_SCHEMA).alias("a"),
            F.col("timestamp").alias("kafka_ts"),
        )
        .select("a.*", "kafka_key", "kafka_ts")
        .where(F.col("id").isNotNull())
        .withColumn("date", F.to_date(F.col("published_at")))
    )

    bronze_query = (
        parsed.writeStream.format("parquet")
        .option("path", lake_path("bronze"))
        .option("checkpointLocation", checkpoint_path("bronze"))
        .partitionBy("date", "source")
        .outputMode("append")
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .start()
    )

    silver = (
        parsed.where(F.col("title").isNotNull() & (F.length(F.col("title")) > 0))
        .withColumn("title", F.trim(F.col("title")))
        .withColumn("content", F.coalesce(F.trim(F.col("content")), F.lit("")))
        .withColumn(
            "lang_guess",
            F.when(F.col("title").rlike("(?i)[a-z]"), F.lit("en")).otherwise(F.lit("other")),
        )
        .where(F.col("lang_guess") == "en")
        .dropDuplicates(["id"])
    )

    silver_query = (
        silver.writeStream.format("parquet")
        .option("path", lake_path("silver"))
        .option("checkpointLocation", checkpoint_path("silver"))
        .partitionBy("date", "source")
        .outputMode("append")
        .trigger(processingTime=f"{trigger_seconds} seconds")
        .start()
    )

    spark.streams.awaitAnyTermination()
    bronze_query.stop()
    silver_query.stop()


if __name__ == "__main__":
    main()
