#!/bin/bash
# Runs the daily HH Research pipeline. Called by launchd at 00:00 Beijing time.
#
# On start: touches data/state/pipeline_started_<DATE>.marker
# On success: writes data/state/last_digest.json with URL extracted from publisher log
# On failure: calls notify_failure.py
#
# All output captured to data/logs/cron/daily_<DATE>.log

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

# Make timezone explicit (launchd inherits a sparse env)
export TZ="Asia/Shanghai"
DATE=$(date +%Y-%m-%d)

mkdir -p data/state data/logs/cron
STATE_DIR="data/state"
LOG="data/logs/cron/daily_${DATE}.log"

# Load .env if present
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . .env
    set +a
fi
export LARK_CLI_NO_PROXY=1

# Mark "pipeline started" — health_check.sh at 00:30 looks for this
touch "${STATE_DIR}/pipeline_started_${DATE}.marker"

{
    echo "================================================================"
    echo "[run_daily_pipeline] START at $(date -Iseconds)"
    echo "================================================================"
} >> "$LOG"

# Run the pipeline
# V3.2 (5.21): --arxiv-mode category 必须显式，否则默认 author mode 撞 429
.venv/bin/python -m hh_research.pipeline.daily \
    --arxiv-mode category \
    --publish \
    --notify-user ou_69c034f8f67053dca0cfaf9c6e9f3262 \
    >> "$LOG" 2>&1
RC=$?

{
    echo "================================================================"
    echo "[run_daily_pipeline] END at $(date -Iseconds) rc=$RC"
    echo "================================================================"
} >> "$LOG"

if [ $RC -eq 0 ]; then
    # Extract the latest published URL from the publisher log (most recent line for today)
    URL=$(grep "published: https://" data/logs/lark_doc_publisher.log 2>/dev/null \
        | grep "^${DATE}" \
        | tail -1 \
        | awk '{print $NF}')

    # Fallback: also accept any URL in today's cron log
    if [ -z "$URL" ]; then
        URL=$(grep -oE 'published: https://[^ ]+' "$LOG" 2>/dev/null | tail -1 | awk '{print $NF}')
    fi

    if [ -z "$URL" ]; then
        # Pipeline returned 0 but we couldn't find a URL — treat as failure for broadcast
        .venv/bin/python scripts/notify_failure.py \
            "pipeline_no_url" \
            "Daily pipeline rc=0 但找不到发布 URL（grep publisher log 失败）。 09:30 推送将跳过。日志: $LOG"
        exit 1
    fi

    # Write state file for broadcast_today.sh to consume
    cat > "${STATE_DIR}/last_digest.json" <<EOF
{
  "date": "${DATE}",
  "url": "${URL}",
  "status": "success",
  "completed_at": "$(date -Iseconds)"
}
EOF
    touch "${STATE_DIR}/pipeline_success_${DATE}.marker"
    echo "[run_daily_pipeline] state written: ${STATE_DIR}/last_digest.json (URL=$URL)" >> "$LOG"
else
    # Failure: notify immediately
    .venv/bin/python scripts/notify_failure.py \
        "pipeline_run_failed" \
        "Daily pipeline 启动了但 rc=$RC 失败。请查看日志: $LOG (tail -100 看末尾)"
    exit $RC
fi
