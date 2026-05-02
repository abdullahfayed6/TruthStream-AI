from __future__ import annotations

import os

from pyspark.sql import SparkSession
from pyspark.sql.types import StringType, StructField, StructType

from streaming.text_utils import normalize_text  # noqa: F401  (re-export)

RAW_SCHEMA = StructType(
    [
        StructField("id", StringType(), nullable=False),
        StructField("source", StringType(), nullable=True),
        StructField("title", StringType(), nullable=True),
        StructField("content", StringType(), nullable=True),
        StructField("url", StringType(), nullable=True),
        StructField("published_at", StringType(), nullable=True),
        StructField("fetched_at", StringType(), nullable=True),
    ]
)


def get_spark(app_name: str) -> SparkSession:
    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", os.environ.get("SHUFFLE_PARTITIONS", "6"))
        .config("spark.sql.streaming.schemaInference", "true")
    )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def lake_path(layer: str) -> str:
    base = os.environ.get("LAKE_PATH", "/opt/lake")
    return f"{base}/{layer}"


def checkpoint_path(name: str) -> str:
    base = os.environ.get("CHECKPOINT_PATH", "/opt/checkpoints")
    return f"{base}/{name}"


