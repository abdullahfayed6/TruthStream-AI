#!/usr/bin/env bash
set -euo pipefail

# Git Bash on Windows otherwise rewrites /opt/... to C:/Program Files/Git/opt/...
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL='*'

PKG="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"
SUBMIT=/opt/spark/bin/spark-submit
MASTER=spark://spark-master:7077

submit() {
  local job=$1
  local logname=$2
  echo "Submitting $job..."
  docker compose exec -T spark-master bash -lc "
    mkdir -p /opt/app/logs
    nohup $SUBMIT \
      --master $MASTER \
      --deploy-mode client \
      --packages $PKG \
      --total-executor-cores 2 \
      --conf spark.sql.shuffle.partitions=6 \
      /opt/app/streaming/$job \
      > /opt/app/logs/$logname.log 2>&1 &
    echo started pid=\$!
  "
}

submit clean_job.py clean
submit score_job.py score

echo "Submitted. Watch http://localhost:8090"
echo "Driver logs: storage/../logs/clean.log and logs/score.log (mounted at ./logs/)"
