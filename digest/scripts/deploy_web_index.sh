#!/bin/bash
# Gated commit/push of web/public/data/digests-index.json.
# 默认不 push;HH_WEB_INDEX_AUTO_PUSH=1 才提交并推送(触发 Vercel 重建)。
set -uo pipefail
DATE="${1:-$(date +%Y-%m-%d)}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"  # scripts -> daily-digest -> repo root
cd "$REPO" || exit 1
INDEX="web/public/data/digests-index.json"

if [ "${HH_WEB_INDEX_AUTO_PUSH:-0}" != "1" ]; then
    echo "[deploy_web_index] HH_WEB_INDEX_AUTO_PUSH != 1 -> skip commit/push (index left in working tree)"
    exit 0
fi
if git diff --quiet -- "$INDEX" && git diff --cached --quiet -- "$INDEX"; then
    echo "[deploy_web_index] no diff in $INDEX, nothing to do"
    exit 0
fi
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BRANCH" != "main" ] && [ "${HH_WEB_INDEX_ALLOW_BRANCH:-0}" != "1" ]; then
    echo "[deploy_web_index] branch=$BRANCH != main -> skip (set HH_WEB_INDEX_ALLOW_BRANCH=1 to override)"
    exit 0
fi
git add "$INDEX"
git commit -m "data(digest): sync web index ${DATE}" || { echo "[deploy_web_index] commit failed"; exit 1; }
git push || { echo "[deploy_web_index] push failed (manual push needed); index left committed"; exit 1; }
echo "[deploy_web_index] committed + pushed $INDEX for ${DATE}"
