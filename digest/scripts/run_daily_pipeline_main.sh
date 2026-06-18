#!/bin/bash
# 主线 pipeline (BJT 08:30 起跑) — user directive 2026-06-03: 正式采用 08:30 起跑/窗口，尽早出报。
#
# 数据窗口: BJT 昨天 08:30 → BJT 今天 08:30 (= UTC 昨天 00:30 → UTC 今天 00:30)
# 起跑时点: BJT 08:30 (= UTC 00:30)，正好与窗口结束边沿对齐
#
# 历史背景:
#   - 5.21 产品会议初定 BJT 8:30 起跑 + 窗口 8:30→8:30
#   - 5.23 实测 8:30 跑 arxiv 0 candidates(镜像未建好), 9:30 跑 236 candidates
#   - 5.26 一度折中定 9:00
#   - 6-03 用户正式改回 08:30(尽早出报)；8:30 arxiv 可能未就绪 → 依赖下方 arxiv=0 retry 兜底(保留)
#   - 12:00 自动 broadcast 已按用户要求停用(broadcast-main plist 已 disabled，本脚本不再触发广播)
#
# 隔离设计 (与支线 00:00 跑的 run_daily_pipeline.sh 并行):
#   - dedup db: data/dedup_main.sqlite (支线用 dedup.sqlite)
#   - state file: data/state/last_digest_main.json (支线用 last_digest.json)
#   - log: data/logs/cron/daily_main_<DATE>.log
#   - 日报标题加后缀 "· 主线"
#
# Called by launchd at BJT 08:30.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

# Timezone explicit (launchd inherits a sparse env)
export TZ="Asia/Shanghai"
DATE=$(date +%Y-%m-%d)  # BJT today, e.g. 2026-05-22

# Prevent system / idle sleep for next ~5h (08:30 → 13:30 BJT).
# Covers: pipeline run + arxiv=0 retry(截止 BJT 11:00)。caffeinate self-exits after timeout.
nohup caffeinate -is -t 18000 > /dev/null 2>&1 &
disown

# Compute window from BJT semantics: BJT yesterday 08:30 → BJT today 08:30.
# We use Python for robust BJT→UTC conversion (avoids macOS `date -j` BJT/UTC mix-ups).
REPO_VENV_PY="${REPO}/.venv/bin/python"
SINCE_UTC=$("$REPO_VENV_PY" -c "
from datetime import datetime, timezone, timedelta
bjt = timezone(timedelta(hours=8))
now_bjt = datetime.now(bjt)
# Anchor: BJT today 08:30; go back 1 day for window start
end = now_bjt.replace(hour=8, minute=30, second=0, microsecond=0)
start = end - timedelta(days=1)
print(start.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
")
UNTIL_UTC=$("$REPO_VENV_PY" -c "
from datetime import datetime, timezone, timedelta
bjt = timezone(timedelta(hours=8))
now_bjt = datetime.now(bjt)
end = now_bjt.replace(hour=8, minute=30, second=0, microsecond=0)
print(end.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
")

mkdir -p data/state data/logs/cron
STATE_DIR="data/state"
LOG="data/logs/cron/daily_main_${DATE}.log"

# Load .env if present
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . .env
    set +a
fi
export LARK_CLI_NO_PROXY=1

# Mark "main pipeline started"
touch "${STATE_DIR}/pipeline_main_started_${DATE}.marker"

{
    echo "================================================================"
    echo "[run_daily_pipeline_main] START at $(date -Iseconds)"
    echo "  DATE (BJT):  $DATE"
    echo "  SINCE (UTC): $SINCE_UTC"
    echo "  UNTIL (UTC): $UNTIL_UTC"
    echo "  Window means: BJT $(date -j -v-1d +%Y-%m-%d) 08:30 → BJT $DATE 08:30"
    echo "================================================================"
} >> "$LOG"

# Run the main-line pipeline
.venv/bin/python -m hh_research.pipeline.daily \
    --since "$SINCE_UTC" \
    --until "$UNTIL_UTC" \
    --dedup-db "data/dedup_main.sqlite" \
    --title-override "HH Research Daily · ${DATE} · 主线" \
    --arxiv-mode category \
    --publish \
    --notify-user ou_69c034f8f67053dca0cfaf9c6e9f3262 \
    >> "$LOG" 2>&1
RC=$?

{
    echo "================================================================"
    echo "[run_daily_pipeline_main] END at $(date -Iseconds) rc=$RC"
    echo "================================================================"
} >> "$LOG"

if [ $RC -eq 0 ]; then
    # Extract the latest published URL from the publisher log
    URL=$(grep "published: https://" data/logs/lark_doc_publisher.log 2>/dev/null \
        | grep "^${DATE}" \
        | tail -1 \
        | awk '{print $NF}')

    # Fallback: also accept any URL in today's main cron log
    if [ -z "$URL" ]; then
        URL=$(grep -oE 'published: https://[^ ]+' "$LOG" 2>/dev/null | tail -1 | awk '{print $NF}')
    fi

    if [ -z "$URL" ]; then
        .venv/bin/python scripts/notify_failure.py \
            "main_pipeline_no_url" \
            "Main pipeline rc=0 但找不到发布 URL。12:00 主线 broadcast 将跳过。日志: $LOG"
        exit 1
    fi

    # Find the local digest for broadcast (.xml preferred, .md fallback).
    # 5-29 fix: daily.py now emits .md; old code only looked for .xml and wrote
    # an empty digest_local_path into the state file.
    DIGEST_LOCAL_PATH="data/digests/digest_${DATE}.xml"
    if [ ! -f "$DIGEST_LOCAL_PATH" ]; then
        DIGEST_LOCAL_PATH=$(ls -t data/digests/digest_${DATE}*.xml 2>/dev/null | head -1)
    fi
    if [ -z "$DIGEST_LOCAL_PATH" ] || [ ! -f "$DIGEST_LOCAL_PATH" ]; then
        DIGEST_LOCAL_PATH="data/digests/digest_${DATE}.md"
    fi
    if [ ! -f "$DIGEST_LOCAL_PATH" ]; then
        DIGEST_LOCAL_PATH=$(ls -t data/digests/digest_${DATE}*.md 2>/dev/null | head -1)
    fi

    # Fail loud: publish URL exists but no local digest file → don't write a
    # state file with an empty path (broadcast/personal-push would then break).
    if [ -z "$DIGEST_LOCAL_PATH" ] || [ ! -f "$DIGEST_LOCAL_PATH" ]; then
        .venv/bin/python scripts/notify_failure.py \
            "main_pipeline_no_local_digest" \
            "Main pipeline rc=0 且有 URL=$URL，但找不到本地 digest 文件 (.xml/.md)。state 文件未写，12:00 broadcast 将跳过。日志: $LOG"
        echo "[run_daily_pipeline_main] ERROR: no local digest file for ${DATE}, state NOT written" >> "$LOG"
        exit 1
    fi

    # Write main state file for broadcast_today_main.sh to consume
    cat > "${STATE_DIR}/last_digest_main.json" <<EOF
{
  "date": "${DATE}",
  "url": "${URL}",
  "status": "success",
  "completed_at": "$(date -Iseconds)",
  "digest_local_path": "${DIGEST_LOCAL_PATH}",
  "line": "main"
}
EOF
    touch "${STATE_DIR}/pipeline_main_success_${DATE}.marker"
    echo "[run_daily_pipeline_main] state written: ${STATE_DIR}/last_digest_main.json (URL=$URL, digest=$DIGEST_LOCAL_PATH)" >> "$LOG"

    # ════════════════════════════════════════════════════════════════
    # Personal 1-on-1 card push (User 5-29 directive)
    # 日报生成后立即推送完整 interactive card 给用户本人
    # 不阻塞 retry loop, 失败也不中断 pipeline
    # ════════════════════════════════════════════════════════════════
    echo "[personal-push] sending 1-on-1 card (digest=$DIGEST_LOCAL_PATH) ..." >> "$LOG"
    .venv/bin/python scripts/send_digest_to_feishu_bot.py "$DATE" \
        --xml "$DIGEST_LOCAL_PATH" \
        --digest-url "$URL" \
        --recipients hlguo@hillhouseinvestment.com \
        --receive-id-type email \
        --no-bitable \
        --send >> "$LOG" 2>&1 \
        && echo "[personal-push] ✅ sent" >> "$LOG" \
        || echo "[personal-push] ⚠️ failed (non-blocking)" >> "$LOG"

    # ════════════════════════════════════════════════════════════════
    # Auto-retry: 用户 directive 2026-05-26
    # 如果 arxiv_fetched == 0 (arxiv 镜像未建好), 每 15 min 重抓 arxiv only,
    # 抓到 -> regenerate digest -> 覆盖 state file. BJT 11:00 截止避免影响 12:00 broadcast.
    # ════════════════════════════════════════════════════════════════
    ARXIV_N=$(grep '"arxiv_fetched"' "$LOG" | tail -1 | grep -oE '[0-9]+' | head -1)
    echo "[retry-check] initial arxiv_fetched=$ARXIV_N" >> "$LOG"

    if [ "$ARXIV_N" = "0" ]; then
        # ────────────────────────────────────────────────────────────
        # User 5-29 directive: arxiv 0 篇时立即 IM 告警
        # ────────────────────────────────────────────────────────────
        ARXIV_WINDOW_DESC="BJT $(date -j -v-1d +%Y-%m-%d) 08:30 → BJT $DATE 08:30"
        echo "[arxiv-warn] initial arxiv=0, sending IM warning to user" >> "$LOG"
        lark-cli --profile personal im +messages-send \
            --user-id ou_69c034f8f67053dca0cfaf9c6e9f3262 \
            --text "⚠️ arxiv 初次提取 0 篇

窗口: ${ARXIV_WINDOW_DESC}
即将进入 15min retry, 截止 BJT 11:00。

可能原因:
- arxiv 镜像今天未建好 (周末/节假日常见)
- arxiv API 异常 / 网络问题

retry 抓到会再发一条 IM 通知; 11:00 截止仍 0 会再告警。" \
            >> "$LOG" 2>&1 || echo "[arxiv-warn] IM send failed" >> "$LOG"

        RETRY_INTERVAL=900   # 15 min
        DEADLINE_HOUR=11     # BJT 11:00 截止
        ATTEMPT=0
        RETRY_SUCCESS=0  # User 5-29 directive: 跟踪 retry 结果, 0=未抓到/timeout 1=已成功

        while true; do
            ATTEMPT=$((ATTEMPT + 1))
            echo "[retry] sleeping ${RETRY_INTERVAL}s before attempt $ATTEMPT (now $(TZ='Asia/Shanghai' date '+%H:%M'))" >> "$LOG"
            sleep $RETRY_INTERVAL

            NOW_HOUR=$(TZ="Asia/Shanghai" date +%H)
            NOW_HOUR_INT=$((10#$NOW_HOUR))  # force base-10
            if [ "$NOW_HOUR_INT" -ge "$DEADLINE_HOUR" ]; then
                echo "[retry] attempt $ATTEMPT skipped: BJT ${NOW_HOUR}:00 >= deadline ${DEADLINE_HOUR}:00, give up" >> "$LOG"
                break
            fi

            RETRY_LOG="data/logs/cron/retry_arxiv_${DATE}_a${ATTEMPT}.log"
            echo "=========================================================" >> "$RETRY_LOG"
            echo "[retry attempt $ATTEMPT] at $(date -Iseconds)" >> "$RETRY_LOG"
            echo "  window: SINCE=$SINCE_UTC UNTIL=$UNTIL_UTC" >> "$RETRY_LOG"

            # 只抓 arxiv + 写入 Bitable, 不动 X / OpenAlex / RSS (已抓过), 不动 digest
            .venv/bin/python -m hh_research.pipeline.daily \
                --since "$SINCE_UTC" \
                --until "$UNTIL_UTC" \
                --dedup-db "data/dedup_main.sqlite" \
                --skip-x --skip-openalex --skip-rss \
                --skip-digest --skip-metrics \
                --arxiv-mode category \
                >> "$RETRY_LOG" 2>&1
            RETRY_RC=$?

            NEW_ARXIV=$(grep '"arxiv_fetched"' "$RETRY_LOG" | tail -1 | grep -oE '[0-9]+' | head -1)
            echo "[retry attempt $ATTEMPT] arxiv_fetched=$NEW_ARXIV rc=$RETRY_RC" >> "$LOG"
            echo "[retry attempt $ATTEMPT] done at $(date -Iseconds) arxiv=$NEW_ARXIV rc=$RETRY_RC" >> "$RETRY_LOG"

            if [ -n "$NEW_ARXIV" ] && [ "$NEW_ARXIV" -gt 0 ] && [ "$RETRY_RC" -eq 0 ]; then
                # 抓到 arxiv! Regenerate digest 含新 arxiv + 已有 X
                echo "[retry] arxiv pickup ($NEW_ARXIV papers), regenerating digest..." >> "$LOG"
                .venv/bin/python scripts/regenerate_digest.py "$DATE" \
                    --cst \
                    --title-suffix "主线 (retry)" \
                    --publish \
                    --notify-user ou_69c034f8f67053dca0cfaf9c6e9f3262 \
                    >> "$RETRY_LOG" 2>&1
                REGEN_RC=$?

                if [ "$REGEN_RC" -eq 0 ]; then
                    NEW_URL=$(grep -oE 'published: https://[^ ]+' "$RETRY_LOG" | tail -1 | awk '{print $NF}')
                    if [ -n "$NEW_URL" ]; then
                        # Re-resolve local digest (.xml preferred, .md fallback) — same
                        # logic as the main branch; regenerate may emit .md.
                        REGEN_LOCAL_PATH="data/digests/digest_${DATE}.xml"
                        if [ ! -f "$REGEN_LOCAL_PATH" ]; then
                            REGEN_LOCAL_PATH=$(ls -t data/digests/digest_${DATE}*.xml 2>/dev/null | head -1)
                        fi
                        if [ -z "$REGEN_LOCAL_PATH" ] || [ ! -f "$REGEN_LOCAL_PATH" ]; then
                            REGEN_LOCAL_PATH="data/digests/digest_${DATE}.md"
                        fi
                        if [ ! -f "$REGEN_LOCAL_PATH" ]; then
                            REGEN_LOCAL_PATH=$(ls -t data/digests/digest_${DATE}*.md 2>/dev/null | head -1)
                        fi
                        # 覆盖 state file -> 12:00 broadcast 自动用新 URL
                        cat > "${STATE_DIR}/last_digest_main.json" <<EOF
{
  "date": "${DATE}",
  "url": "${NEW_URL}",
  "status": "success",
  "completed_at": "$(date -Iseconds)",
  "digest_local_path": "${REGEN_LOCAL_PATH}",
  "line": "main",
  "note": "retry attempt $ATTEMPT picked up $NEW_ARXIV arxiv papers"
}
EOF
                        echo "[retry] ✅ state updated, URL=$NEW_URL ($NEW_ARXIV arxiv, digest=$REGEN_LOCAL_PATH)" >> "$LOG"
                        RETRY_SUCCESS=1  # User 5-29 directive: 标记 retry 已成功
                        # IM 通知主用户
                        lark-cli --profile personal im +messages-send \
                            --user-id ou_69c034f8f67053dca0cfaf9c6e9f3262 \
                            --text "🔁 retry 第 $ATTEMPT 次抓到 $NEW_ARXIV 篇 arxiv,digest 已更新: $NEW_URL" \
                            >> "$RETRY_LOG" 2>&1 || true
                        # Re-push 完整 card 给用户本人 (含 retry 后新内容)
                        .venv/bin/python scripts/send_digest_to_feishu_bot.py "$DATE" \
                            --xml "$REGEN_LOCAL_PATH" \
                            --digest-url "$NEW_URL" \
                            --recipients hlguo@hillhouseinvestment.com \
                            --receive-id-type email \
                            --no-bitable \
                            --send >> "$RETRY_LOG" 2>&1 \
                            && echo "[retry] ✅ re-pushed personal card after retry" >> "$LOG" \
                            || echo "[retry] ⚠️ re-push personal card failed (non-blocking)" >> "$LOG"
                    fi
                else
                    echo "[retry] regenerate failed rc=$REGEN_RC, keep original state" >> "$LOG"
                fi
                break  # 抓到就停止 retry
            fi

            # 还是 0, 继续循环 (除非到 deadline)
        done

        echo "[retry-check] retry loop exited after $ATTEMPT attempts, success=$RETRY_SUCCESS" >> "$LOG"

        # ────────────────────────────────────────────────────────────
        # User 5-29 directive: retry 全部失败时 (timeout 到 BJT 11:00) 再次告警
        # ────────────────────────────────────────────────────────────
        if [ "$RETRY_SUCCESS" -eq 0 ]; then
            echo "[arxiv-warn] retry exhausted without pickup, sending final IM warning" >> "$LOG"
            lark-cli --profile personal im +messages-send \
                --user-id ou_69c034f8f67053dca0cfaf9c6e9f3262 \
                --text "🚨 arxiv 提取失败 (BJT 11:00 截止)

窗口: ${ARXIV_WINDOW_DESC}
经 $ATTEMPT 次 retry 仍未抓到任何 paper。

今日日报将仅含 X / RSS / OpenAlex 信号，无 arxiv 前沿研究。
12:00 主线 broadcast 仍按计划进行（如已 load broadcast-main）。

排查建议:
- 检查 arxiv API 状态 (https://arxiv.org/status)
- 确认网络 / 代理 (LARK_CLI_NO_PROXY=1 已设)
- 看日志: ${LOG}" \
                >> "$LOG" 2>&1 || echo "[arxiv-warn] final IM send failed" >> "$LOG"
        fi
    else
        echo "[retry-check] arxiv_fetched=$ARXIV_N > 0, no retry needed" >> "$LOG"
    fi

    # ════════════════════════════════════════════════════════════════
    # Web 日历 index 同步 (2026-06-08): 以最终 last_digest_main.json 为准,
    # 放在 retry loop 之后。非阻断:失败只告警,不影响已完成的飞书发布。
    # 不触碰 broadcast_today_main.sh / launchd broadcast。
    # ════════════════════════════════════════════════════════════════
    echo "[web-index] syncing digests-index.json from final state ..." >> "$LOG"
    if .venv/bin/python scripts/sync_web_digest_index.py \
        --state "${STATE_DIR}/last_digest_main.json" \
        --index "../web/public/data/digests-index.json" \
        --source pipeline_main >> "$LOG" 2>&1; then
        echo "[web-index] index synced" >> "$LOG"
        HH_WEB_INDEX_AUTO_PUSH="${HH_WEB_INDEX_AUTO_PUSH:-0}" \
            scripts/deploy_web_index.sh "$DATE" >> "$LOG" 2>&1 \
            && echo "[web-index] deploy step done" >> "$LOG" \
            || echo "[web-index] deploy step skipped/failed (non-blocking)" >> "$LOG"
    else
        echo "[web-index] sync failed (non-blocking)" >> "$LOG"
        .venv/bin/python scripts/notify_failure.py "web_index_sync_failed" \
            "Web 日历 index 同步失败 (date=$DATE)。日报发布不受影响。日志: $LOG" \
            >> "$LOG" 2>&1 || true
    fi
else
    .venv/bin/python scripts/notify_failure.py \
        "main_pipeline_run_failed" \
        "Main pipeline rc=$RC 失败。请查看日志: $LOG (tail -100 看末尾)"
    exit $RC
fi
