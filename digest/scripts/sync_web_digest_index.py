#!/usr/bin/env python
"""读取主线最终 state(last_digest_main.json),upsert web/public/data/digests-index.json。

用法:
  .venv/bin/python scripts/sync_web_digest_index.py \
    --state data/state/last_digest_main.json \
    --index ../web/public/data/digests-index.json \
    --source pipeline_main [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# scripts/ 在 sys.path 外;把 src 加入以 import hh_research.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hh_research.publish.digest_index import extract_digest_meta, upsert_entry  # noqa: E402


def build_entry(state: dict, daily_digest_root: Path, source: str) -> dict:
    date = state["date"]
    url = state.get("url", "")
    line = state.get("line", "main")
    title = state.get("title") or f"HH Research Daily · {date}"
    tldr, signal_count = "", 0
    confidence = "high" if url else "low"

    dlp = state.get("digest_local_path")
    if dlp:
        f = daily_digest_root / dlp
        if f.exists():
            meta = extract_digest_meta(
                f.read_text(encoding="utf-8", errors="ignore"),
                fallback_title=title,
                fallback_date=date,
            )
            title = meta["title"] or title
            tldr = meta["tldr"]
            signal_count = meta["signal_count"]
        else:
            confidence = "medium"  # 有 URL 但本地正文缺失
    return {
        "date": date,
        "title": title,
        "signal_count": signal_count,
        "tldr": tldr,
        "feishu_wiki_url": url,
        "source": source,
        "line": line,
        "confidence": confidence,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--index", required=True)
    ap.add_argument("--source", default="pipeline_main")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state_path = Path(args.state)
    if not state_path.exists():
        print(f"[web-index] state not found: {state_path}", file=sys.stderr)
        return 1
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") != "success" or not state.get("date"):
        print("[web-index] state not success or missing date; skip", file=sys.stderr)
        return 1

    daily_digest_root = Path(__file__).resolve().parents[1]  # scripts/ -> daily-digest/
    entry = build_entry(state, daily_digest_root, args.source)
    if args.dry_run:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return 0
    upsert_entry(Path(args.index), entry)
    print(
        f"[web-index] upserted {entry['date']} url={entry['feishu_wiki_url']} "
        f"signals={entry['signal_count']} conf={entry['confidence']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
