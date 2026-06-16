#!/usr/bin/env bash
# Periodic knowledge-graph refresh: rebuild structured relations (/graph/sync)
# and re-infer implicit relations (/graph/infer). Idempotent — safe to run on a
# schedule. Wire up via cron, e.g.:
#   0 3 * * * /home/ubuntu/hh-research/deploy/graph_refresh.sh >> /var/log/hh_graph_refresh.log 2>&1
set -euo pipefail

BACKEND_CONTAINER="${BACKEND_CONTAINER:-hh-research-backend-1}"

docker exec "$BACKEND_CONTAINER" python - <<'PY'
import urllib.request, datetime

def post(path):
    req = urllib.request.Request(
        "http://localhost:8000/api" + path, data=b"{}", method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        body = urllib.request.urlopen(req, timeout=600).read().decode()
        print(datetime.datetime.now().isoformat(), path, body)
    except Exception as exc:  # noqa: BLE001
        print(datetime.datetime.now().isoformat(), path, "ERROR", exc)

post("/graph/sync")
post("/graph/infer")
PY
