#!/bin/bash
# Wrapper for launchd to keep the subscribe listener daemon alive.
#
# Pipes `lark-cli event consume im.message.receive_v1 --as bot` into
# `subscribe_listener.py`. Tricks:
#   1. `< <(tail -f /dev/null)` keeps stdin open forever so event consume
#      does not see EOF and exit immediately (see lark-event subprocess contract).
#   2. KeepAlive=true in plist auto-restarts on crash.
#
# Called by launchd via com.hh-research.subscribe-listener.plist.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

export TZ="Asia/Shanghai"
export LARK_CLI_NO_PROXY=1

# Load .env (lark-cli credentials etc.)
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . .env
    set +a
fi

mkdir -p data/logs/cron
LOG="data/logs/cron/subscribe_listener.log"

{
    echo "================================================================"
    echo "[$(date -Iseconds)] subscribe_listener wrapper START"
    echo "  REPO=$REPO"
    echo "================================================================"
} >> "$LOG"

# pipe: event consume → python listener
# stderr of event consume + listener both go to LOG
#
# IMPORTANT: --profile hres-bot uses cli_aa84636e237d5bd1 (HRes' aha moment app)
# — the SAME app that send_digest_to_feishu_bot.py pushes from. This is the
# app users find in 飞书 search as "HRes' aha moment". Using --profile personal
# (郭昊霖's individual dev app cli_a9605...) would listen on the wrong app and
# never receive user messages.
exec lark-cli --profile hres-bot event consume im.message.receive_v1 --as bot \
    < <(tail -f /dev/null) \
    2>> "$LOG" \
    | .venv/bin/python scripts/subscribe_listener.py >> "$LOG" 2>&1
