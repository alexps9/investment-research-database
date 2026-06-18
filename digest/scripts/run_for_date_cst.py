"""Run daily pipeline for "N 日的日报" using Beijing-time semantic.

按用户偏好惯例（pipeline_state.md 第 9 行）：
    "N 日的日报" = 北京时间 (N-1) 0:00 → N 0:00
    = UTC (N-1) 16:00 → N 16:00 (转换关系: CST = UTC + 8)

实际上 北京 N-1 0:00 = UTC N-1 - 16h = UTC (N-2) 16:00, 加上"+一天" = UTC N-1 16:00
所以 "5.20 日报" = 北京 5.19 0:00 → 5.20 0:00 = UTC 5.18 16:00 → 5.19 16:00

发布后自动注入锚点跳转（publish_with_anchors.inject_anchors_inplace）。

Usage:
    .venv/bin/python scripts/run_for_date_cst.py 2026-05-20 \\
        --publish --notify-user ou_69c034f8f67053dca0cfaf9c6e9f3262
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.pipeline.daily import run  # noqa: E402
from hh_research.utils.logger import get_logger  # noqa: E402

log = get_logger("run_for_date_cst")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("date", help="标题日期 YYYY-MM-DD（按北京时间发布日）")
    ap.add_argument("--publish", action="store_true", help="发布到飞书 wiki")
    ap.add_argument("--notify-user", type=str, default=None)
    ap.add_argument("--skip-arxiv", action="store_true")
    ap.add_argument("--skip-x", action="store_true")
    ap.add_argument("--skip-openalex", action="store_true")
    ap.add_argument("--skip-rss", action="store_true")
    ap.add_argument("--skip-metrics", action="store_true")
    ap.add_argument("--arxiv-mode", choices=["author", "category"], default="category",
                    help="arXiv collection mode; category is safer for daily backfills")
    ap.add_argument("--no-anchors", action="store_true",
                    help="跳过锚点注入（默认发布后会注入）")
    ap.add_argument("--title-suffix", type=str, default="",
                    help="附加到标题末尾（如 'V2' → 'HH Research Daily 2026-05-21 V2'）")
    args = ap.parse_args()

    # 北京时间 (N-1) 0:00 → N 0:00 = UTC (N-1)-16h → N-16h
    target = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    since_dt = target - timedelta(days=1) - timedelta(hours=8)  # 北京 (N-1) 0:00 = UTC (N-1) - 8h - 16h? Let me redo
    # 北京 X 0:00 = UTC X 0:00 - 8h = UTC (X-1) 16:00
    # So 北京 (N-1) 0:00 = UTC (N-1) - 8h. 在 Python: (target - 1day - 8h)
    # 北京 N 0:00 = UTC N - 8h
    # since = 北京 (N-1) 0:00 = UTC (N - 1 day - 8h)
    # until = 北京 N 0:00 = UTC (N - 8h)
    since_dt = target - timedelta(days=1, hours=8)
    until_dt = target - timedelta(hours=8)

    log.info("窗口（北京）: %s 0:00 → %s 0:00", (target - timedelta(days=1)).date(), target.date())
    log.info("窗口（UTC）: %s → %s", since_dt.isoformat(), until_dt.isoformat())
    title_override = f"HH Research Daily {args.date}"
    if args.title_suffix:
        title_override = f"{title_override} {args.title_suffix}"
    log.info("标题: %s", title_override)

    summary = run(
        since_dt=since_dt,
        until_dt=until_dt,
        skip_arxiv=args.skip_arxiv,
        skip_x=args.skip_x,
        skip_openalex=args.skip_openalex,
        skip_rss=args.skip_rss,
        skip_metrics=args.skip_metrics,
        arxiv_mode=args.arxiv_mode,
        publish_to_feishu=args.publish,
        notify_user_id=args.notify_user,
        digest_title_override=title_override,
    )

    # Find obj_token from summary for anchor injection
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))

    # If published, inject anchors
    if args.publish and not args.no_anchors:
        obj_token = summary.get("digest_obj_token") or summary.get("obj_token")
        if obj_token:
            from publish_with_anchors import inject_anchors_inplace
            print()
            print("=" * 70)
            print("ANCHOR INJECTION")
            result = inject_anchors_inplace(obj_token)
            print(json.dumps(
                {
                    "anchors_resolved": len(result["anchor_map"]),
                    "markers_deleted": result["markers_deleted"],
                },
                ensure_ascii=False, indent=2,
            ))
        else:
            print("[WARN] no obj_token in summary, cannot inject anchors")

    return 0


if __name__ == "__main__":
    sys.exit(main())
