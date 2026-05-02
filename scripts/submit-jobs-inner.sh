#!/usr/bin/env bash
# Run this INSIDE the spark-master container:
#   docker compose exec -T spark-master bash /opt/app/scripts/submit-jobs-inner.sh
set -euo pipefail

PKG="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"
SUBMIT="/opt/spark/bin/spark-submit"
MASTER="spark://spark-master:7077"

mkdir -p /opt/app/logs

echo "==> Submitting clean_job.py (2 cores) ..."
nohup "$SUBMIT" \
    --master "$MASTER" \
    --deploy-mode client \
    --packages "$PKG" \
    --total-executor-cores 2 \
    --conf spark.sql.shuffle.partitions=6 \
    /opt/app/streaming/clean_job.py \
    > /opt/app/logs/clean.log 2>&1 &
echo "    clean_job pid=$!"

# Give it a head start so it builds the silver lake before score_job tries to read it
sleep 10

echo "==> Submitting score_job.py (2 cores) ..."
nohup "$SUBMIT" \
    --master "$MASTER" \
    --deploy-mode client \
    --packages "$PKG" \
    --total-executor-cores 2 \
    --conf spark.sql.shuffle.partitions=6 \
    /opt/app/streaming/score_job.py \
    > /opt/app/logs/score.log 2>&1 &
echo "    score_job pid=$!"

echo ""
echo "Both streaming jobs submitted."
echo "Logs:  /opt/app/logs/clean.log  |  /opt/app/logs/score.log"
echo "UI:    http://localhost:8090"
