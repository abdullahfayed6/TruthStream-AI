#!/usr/bin/env bash
# Submit ONLY score_job (clean_job already running).
# Run inside spark-master: docker compose exec -T spark-master bash /opt/app/scripts/submit-score-only.sh

PKG="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"
SUBMIT="/opt/spark/bin/spark-submit"
MASTER="spark://spark-master:7077"

mkdir -p /opt/app/logs

# Kill any existing score_job
pkill -f score_job.py 2>/dev/null && echo "Stopped old score_job" || echo "No old score_job running"
sleep 2

echo "==> Submitting score_job.py (2 cores, fresh) ..."
nohup "$SUBMIT" \
    --master "$MASTER" \
    --deploy-mode client \
    --packages "$PKG" \
    --total-executor-cores 2 \
    --conf spark.sql.shuffle.partitions=6 \
    /opt/app/streaming/score_job.py \
    > /opt/app/logs/score.log 2>&1 &
echo "    score_job pid=$!"
echo "Log: /opt/app/logs/score.log"
