# ============================================================
# TruthStream AI - Clean State & Restart Script (PowerShell)
# ============================================================
# Run this from the project root:
#   .\scripts\cleanup-and-restart.ps1
#
# What it does:
#   1. Stops frozen Spark jobs
#   2. Clears corrupted checkpoints and stale gold-lake data
#   3. Recreates clean directory structure
#   4. Resubmits Spark jobs (2 cores each, no starvation)
#   5. Reports Docker stack health
# ============================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  TruthStream AI - Checkpoint Cleanup & Restart" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# Step 1 - Kill running Spark streaming jobs (release file locks)
# ---------------------------------------------------------------------------
Write-Host "[1/5] Stopping running Spark jobs..." -ForegroundColor Yellow
try {
    & docker compose exec -T spark-master bash -c "pkill -f 'clean_job|score_job' 2>/dev/null || true"
    Start-Sleep -Seconds 3
    Write-Host "      Spark jobs stopped." -ForegroundColor Green
} catch {
    Write-Host "      No active Spark jobs (or Docker not running). Continuing..." -ForegroundColor DarkYellow
}

# ---------------------------------------------------------------------------
# Step 2 - Wipe corrupted checkpoints and stale gold-tier lake data
# ---------------------------------------------------------------------------
Write-Host "[2/5] Clearing corrupted checkpoints and gold lake data..." -ForegroundColor Yellow

$CheckpointDir = Join-Path $ProjectRoot "storage\checkpoints"
$GoldDir       = Join-Path $ProjectRoot "storage\lake\gold"

if (Test-Path $CheckpointDir) {
    Remove-Item -Recurse -Force $CheckpointDir
    Write-Host "      Removed: $CheckpointDir" -ForegroundColor Green
} else {
    Write-Host "      Checkpoint dir not found - nothing to remove." -ForegroundColor DarkGray
}

if (Test-Path $GoldDir) {
    Remove-Item -Recurse -Force $GoldDir
    Write-Host "      Removed gold tier: $GoldDir" -ForegroundColor Green
} else {
    Write-Host "      Gold tier dir not found - nothing to remove." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# Step 3 - Recreate clean directory structure
# ---------------------------------------------------------------------------
Write-Host "[3/5] Recreating clean directory structure..." -ForegroundColor Yellow

$Dirs = @(
    "storage\checkpoints",
    "storage\lake\bronze",
    "storage\lake\silver",
    "storage\lake\gold",
    "logs"
)

foreach ($Dir in $Dirs) {
    $FullPath = Join-Path $ProjectRoot $Dir
    if (-not (Test-Path $FullPath)) {
        New-Item -ItemType Directory -Path $FullPath -Force | Out-Null
        Write-Host "      Created: $FullPath" -ForegroundColor Green
    } else {
        Write-Host "      Exists:  $FullPath" -ForegroundColor DarkGray
    }
}

# Keep .gitkeep files so Git tracks the empty dirs
foreach ($Dir in @("storage\checkpoints", "storage\lake\bronze", "storage\lake\silver", "storage\lake\gold")) {
    $GitKeep = Join-Path $ProjectRoot "$Dir\.gitkeep"
    if (-not (Test-Path $GitKeep)) {
        "" | Out-File -FilePath $GitKeep -Encoding utf8
    }
}

Write-Host "      Directory structure ready." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 4 - Resubmit Spark streaming jobs (2 cores each, no resource starvation)
# ---------------------------------------------------------------------------
Write-Host "[4/5] Submitting Spark streaming jobs (2 cores each)..." -ForegroundColor Yellow

$InlineScript = @'
set -e
PKG="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"
SUBMIT=/opt/spark/bin/spark-submit
MASTER=spark://spark-master:7077
mkdir -p /opt/app/logs

echo "Starting clean_job..."
nohup $SUBMIT \
    --master $MASTER \
    --deploy-mode client \
    --packages $PKG \
    --total-executor-cores 2 \
    --conf spark.sql.shuffle.partitions=6 \
    /opt/app/streaming/clean_job.py \
    > /opt/app/logs/clean.log 2>&1 &
echo "  clean_job pid=$!"

sleep 5

echo "Starting score_job..."
nohup $SUBMIT \
    --master $MASTER \
    --deploy-mode client \
    --packages $PKG \
    --total-executor-cores 2 \
    --conf spark.sql.shuffle.partitions=6 \
    /opt/app/streaming/score_job.py \
    > /opt/app/logs/score.log 2>&1 &
echo "  score_job pid=$!"
'@

try {
    & docker compose exec -T spark-master bash -c $InlineScript
    Write-Host "      Spark jobs submitted." -ForegroundColor Green
} catch {
    Write-Host "      Docker not running. Start the stack first:" -ForegroundColor DarkYellow
    Write-Host "        docker compose up -d" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Step 5 - Health check
# ---------------------------------------------------------------------------
Write-Host "[5/5] Docker stack health..." -ForegroundColor Yellow
try {
    & docker compose ps
} catch {
    Write-Host "      Cannot reach Docker. Run: docker compose up -d" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Done! Next steps:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  1. Wait ~60 s for Spark jobs to build fresh checkpoints"
Write-Host "  2. Run tests:  python tests/test_all.py"
Write-Host "  3. Spark UI:   http://localhost:8090"
Write-Host "  4. Kafka UI:   http://localhost:8080"
Write-Host "  5. Mongo UI:   http://localhost:8081"
Write-Host ""
