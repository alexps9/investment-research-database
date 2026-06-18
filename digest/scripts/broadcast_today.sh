#!/bin/bash
# At 09:30, read state file and send today's digest card to enterprise group.
# Per user spec: if today's digest didn't succeed, silently skip (no group send).
# The user has already been notified by health_check.sh / run_daily_pipeline.sh
# if there was a failure.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

export TZ="Asia/Shanghai"
DATE=$(date +%Y-%m-%d)

# Load .env (webhook URL + secret + SMTP)
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . .env
    set +a
fi
export LARK_CLI_NO_PROXY=1

LOG_DIR="data/logs/cron"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/broadcast_${DATE}.log"

STATE="data/state/last_digest.json"

{
    echo "================================================================"
    echo "[broadcast_today] $(date -Iseconds) checking state..."
} >> "$LOG"

if [ ! -f "$STATE" ]; then
    echo "[broadcast_today] no state file — skip broadcast." >> "$LOG"
    exit 0
fi

# Parse state JSON (lightweight, no jq required)
STATE_DATE=$(.venv/bin/python -c "import json; print(json.load(open('$STATE'))['date'])" 2>/dev/null)
STATE_URL=$(.venv/bin/python -c "import json; print(json.load(open('$STATE'))['url'])" 2>/dev/null)
STATE_STATUS=$(.venv/bin/python -c "import json; print(json.load(open('$STATE'))['status'])" 2>/dev/null)
STATE_DIGEST_PATH=$(.venv/bin/python -c "import json; print(json.load(open('$STATE')).get('digest_local_path', ''))" 2>/dev/null)

echo "[broadcast_today] state: date=$STATE_DATE status=$STATE_STATUS url=$STATE_URL" >> "$LOG"

if [ "$STATE_DATE" != "$DATE" ]; then
    echo "[broadcast_today] state date ($STATE_DATE) != today ($DATE) — skip." >> "$LOG"
    exit 0
fi

if [ "$STATE_STATUS" != "success" ]; then
    echo "[broadcast_today] state status=$STATE_STATUS != success — skip." >> "$LOG"
    exit 0
fi

# Send the card. The send_digest_to_enterprise.py script reads
# HH_LARK_ENTERPRISE_WEBHOOK_URL and HH_LARK_ENTERPRISE_WEBHOOK_SECRET from env.
if [ -n "$STATE_DIGEST_PATH" ] && [ -f "$STATE_DIGEST_PATH" ]; then
    .venv/bin/python scripts/send_digest_to_enterprise.py \
        --xml "$STATE_DIGEST_PATH" \
        --digest-url "$STATE_URL" \
        --title "HH Research Daily · ${STATE_DATE}" \
        --send \
        >> "$LOG" 2>&1
else
    .venv/bin/python scripts/send_digest_to_enterprise.py "$DATE" \
        --digest-url "$STATE_URL" \
        --title "HH Research Daily · ${STATE_DATE}" \
        --send \
        >> "$LOG" 2>&1
fi
RC=$?

if [ $RC -ne 0 ]; then
    # Broadcast failed — notify user
    .venv/bin/python scripts/notify_failure.py \
        "broadcast_failed" \
        "企业群广播在 ${DATE} 09:30 失败 (rc=$RC)。日志: $LOG" \
        >> "$LOG" 2>&1
else
    # Broadcast succeeded — send success ping to user's personal Feishu IM
    NOTIFY_OPEN_ID="${NOTIFY_USER_OPEN_ID:-ou_69c034f8f67053dca0cfaf9c6e9f3262}"
    SUCCESS_TEXT="✅ HH Research Daily ${DATE} 已成功发送至企业群"$'\n'"时间: $(date '+%Y-%m-%d %H:%M:%S') 北京"$'\n'"链接: ${STATE_URL}"
    lark-cli --profile personal im +messages-send \
        --user-id "$NOTIFY_OPEN_ID" \
        --text "$SUCCESS_TEXT" \
        >> "$LOG" 2>&1 || echo "[broadcast_today] WARN: success-ping IM failed" >> "$LOG"

    # Feishu 1-on-1 bot push (HRes' aha moment) — gated on credentials; non-blocking
    if [ -n "${FEISHU_BOT_APP_ID:-}" ] && [ -n "${FEISHU_BOT_RECIPIENT_OPENIDS:-}" ]; then
        echo "[broadcast_today] Feishu bot push starting" >> "$LOG"
        .venv/bin/python scripts/send_digest_to_feishu_bot.py \
            --xml "$STATE_DIGEST_PATH" \
            --digest-url "$STATE_URL" \
            --title "HH Research Daily · ${STATE_DATE}" \
            --send \
            >> "$LOG" 2>&1 \
            || echo "[broadcast_today] WARN: Feishu bot push failed (non-blocking)" >> "$LOG"
    else
        echo "[broadcast_today] Feishu bot not configured (FEISHU_BOT_APP_ID empty) — skip" >> "$LOG"
    fi

    # H Link 1-on-1 push — gated on credentials; failure is non-blocking.
    # Skips silently if H_LINK_APP_ID or H_LINK_RECIPIENT_OPENIDS are empty
    # (credentials not yet provided by IT).
    if [ -n "${H_LINK_APP_ID:-}" ] && [ -n "${H_LINK_RECIPIENT_OPENIDS:-}" ]; then
        echo "[broadcast_today] H Link push starting (recipients=${H_LINK_RECIPIENT_OPENIDS})" >> "$LOG"
        .venv/bin/python scripts/send_digest_to_hlink.py \
            --xml "$STATE_DIGEST_PATH" \
            --digest-url "$STATE_URL" \
            --title "HH Research Daily · ${STATE_DATE}" \
            --send \
            >> "$LOG" 2>&1 \
            || echo "[broadcast_today] WARN: H Link push failed (non-blocking)" >> "$LOG"
    else
        echo "[broadcast_today] H Link not configured (H_LINK_APP_ID empty) — skip" >> "$LOG"
    fi

    # NOTE: email notification path (notify_success.py) prepared but disabled —
    # SMTP unreachable in current network. Re-enable when email channel is fixed.
fi

echo "[broadcast_today] done rc=$RC" >> "$LOG"
exit $RC
