#!/bin/bash
# 主线 broadcast (BJT 12:00 触发) — 5.21 产品会议路线图决策 #2
#
# 读 data/state/last_digest_main.json（由 run_daily_pipeline_main.sh 写入），
# 推送 HH Research Daily · YYYY-MM-DD · 主线 到 3 个渠道:
#   1. 飞书企业群 (webhook · 已上线)
#   2. 飞书 1-on-1 bot (HRes' aha moment, 凭证存在则推)
#   3. H Link 1-on-1 (凭证存在则推)
#
# 若主线 state 文件状态非 success 或日期不匹配，silent skip。
# Called by launchd at BJT 12:00.

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
LOG="${LOG_DIR}/broadcast_main_${DATE}.log"

STATE="data/state/last_digest_main.json"

{
    echo "================================================================"
    echo "[broadcast_today_main] $(date -Iseconds) checking main state..."
} >> "$LOG"

if [ ! -f "$STATE" ]; then
    echo "[broadcast_today_main] no main state file — skip broadcast." >> "$LOG"
    exit 0
fi

# Parse state JSON (lightweight, no jq required)
STATE_DATE=$(.venv/bin/python -c "import json; print(json.load(open('$STATE'))['date'])" 2>/dev/null)
STATE_URL=$(.venv/bin/python -c "import json; print(json.load(open('$STATE'))['url'])" 2>/dev/null)
STATE_STATUS=$(.venv/bin/python -c "import json; print(json.load(open('$STATE'))['status'])" 2>/dev/null)
STATE_DIGEST_PATH=$(.venv/bin/python -c "import json; print(json.load(open('$STATE')).get('digest_local_path', ''))" 2>/dev/null)

echo "[broadcast_today_main] state: date=$STATE_DATE status=$STATE_STATUS url=$STATE_URL" >> "$LOG"

if [ "$STATE_DATE" != "$DATE" ]; then
    echo "[broadcast_today_main] state date ($STATE_DATE) != today ($DATE) — skip." >> "$LOG"
    exit 0
fi

if [ "$STATE_STATUS" != "success" ]; then
    echo "[broadcast_today_main] state status=$STATE_STATUS != success — skip." >> "$LOG"
    exit 0
fi

# Card title (user 5-30: drop the "· 主线" suffix from broadcast cards)
CARD_TITLE="HH Research Daily · ${STATE_DATE}"

# Send to enterprise group
if [ -n "$STATE_DIGEST_PATH" ] && [ -f "$STATE_DIGEST_PATH" ]; then
    .venv/bin/python scripts/send_digest_to_enterprise.py \
        --xml "$STATE_DIGEST_PATH" \
        --digest-url "$STATE_URL" \
        --title "$CARD_TITLE" \
        --send \
        >> "$LOG" 2>&1
else
    .venv/bin/python scripts/send_digest_to_enterprise.py "$DATE" \
        --digest-url "$STATE_URL" \
        --title "$CARD_TITLE" \
        --send \
        >> "$LOG" 2>&1
fi
RC=$?

if [ $RC -ne 0 ]; then
    .venv/bin/python scripts/notify_failure.py \
        "broadcast_main_failed" \
        "主线企业群广播在 ${DATE} 12:00 失败 (rc=$RC)。日志: $LOG" \
        >> "$LOG" 2>&1
else
    # Success ping to user
    NOTIFY_OPEN_ID="${NOTIFY_USER_OPEN_ID:-ou_69c034f8f67053dca0cfaf9c6e9f3262}"
    SUCCESS_TEXT="✅ ${CARD_TITLE} 已成功发送至企业群"$'\n'"时间: $(date '+%Y-%m-%d %H:%M:%S') 北京"$'\n'"链接: ${STATE_URL}"
    lark-cli --profile personal im +messages-send \
        --user-id "$NOTIFY_OPEN_ID" \
        --text "$SUCCESS_TEXT" \
        >> "$LOG" 2>&1 || echo "[broadcast_today_main] WARN: success-ping IM failed" >> "$LOG"

    # Feishu 1-on-1 bot push — non-blocking
    if [ -n "${FEISHU_BOT_APP_ID:-}" ] && [ -n "${FEISHU_BOT_RECIPIENT_OPENIDS:-}" ]; then
        echo "[broadcast_today_main] Feishu bot push starting" >> "$LOG"
        .venv/bin/python scripts/send_digest_to_feishu_bot.py \
            --xml "$STATE_DIGEST_PATH" \
            --digest-url "$STATE_URL" \
            --title "$CARD_TITLE" \
            --send \
            >> "$LOG" 2>&1 \
            || echo "[broadcast_today_main] WARN: Feishu bot push failed (non-blocking)" >> "$LOG"
    else
        echo "[broadcast_today_main] Feishu bot not configured (FEISHU_BOT_APP_ID empty) — skip" >> "$LOG"
    fi

    # H Link 1-on-1 push — non-blocking
    if [ -n "${H_LINK_APP_ID:-}" ] && [ -n "${H_LINK_RECIPIENT_OPENIDS:-}" ]; then
        echo "[broadcast_today_main] H Link push starting (recipients=${H_LINK_RECIPIENT_OPENIDS})" >> "$LOG"
        .venv/bin/python scripts/send_digest_to_hlink.py \
            --xml "$STATE_DIGEST_PATH" \
            --digest-url "$STATE_URL" \
            --title "$CARD_TITLE" \
            --send \
            >> "$LOG" 2>&1 \
            || echo "[broadcast_today_main] WARN: H Link push failed (non-blocking)" >> "$LOG"
    else
        echo "[broadcast_today_main] H Link not configured (H_LINK_APP_ID empty) — skip" >> "$LOG"
    fi
fi

echo "[broadcast_today_main] done rc=$RC" >> "$LOG"
exit $RC
