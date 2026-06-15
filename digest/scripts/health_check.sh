#!/bin/bash
# Health check at 00:30. If pipeline didn't even START today (no marker file),
# the laptop was likely asleep / launchd didn't fire. Notify user.
#
# This does NOT check completion — pipeline may still be running at 00:30
# (typical runtime 30-50 min). Completion failures are caught by
# run_daily_pipeline.sh's own error handler.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

export TZ="Asia/Shanghai"
DATE=$(date +%Y-%m-%d)

# Load .env for SMTP/notify env
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . .env
    set +a
fi
export LARK_CLI_NO_PROXY=1

MARKER="data/state/pipeline_started_${DATE}.marker"
LOG_DIR="data/logs/cron"
mkdir -p "$LOG_DIR"

if [ ! -f "$MARKER" ]; then
    # Pipeline never started — notify
    .venv/bin/python scripts/notify_failure.py \
        "pipeline_not_started" \
        "Daily pipeline 在 ${DATE} 00:00 没有启动（00:30 检查时没有找到 started marker）。可能原因：笔记本休眠 / 断电 / launchd 没触发。今日 09:30 推送将自动跳过。请手动跑：bash scripts/run_daily_pipeline.sh" \
        >> "${LOG_DIR}/health_${DATE}.log" 2>&1
    exit 0  # Don't fail launchd; we've notified.
fi

# Started marker present → pipeline at least fired. Log and exit.
echo "[health_check] $(date -Iseconds) ${DATE} pipeline started OK (marker present)" \
    >> "${LOG_DIR}/health_${DATE}.log"
