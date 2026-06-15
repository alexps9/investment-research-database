#!/usr/bin/env python3
"""发布手工编辑后的 digest XML 文件到飞书 wiki + 注入锚点 + 1-1 通知用户。
不重新生成（保留人工编辑的头条/TLDR）。

Usage:
    cd daily-digest && .venv/bin/python scripts/publish_edited_digest.py <digest_file> [--notify-user ou_xxx] [--title-suffix "..."]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.publish.lark_doc_publisher import notify_digest_ready, publish_digest  # noqa: E402

DEFAULT_STATE_DIR = Path(__file__).parent.parent / "data" / "state"
_STATE_FILES = {"main": "last_digest_main.json", "sub": "last_digest.json"}


def build_state_payload(*, line: str, date: str, url: str, node_token: str,
                        digest_local_path: str, title: str) -> dict:
    """构造与自动主线 (run_daily_pipeline_main.sh:144) 同 schema 的 state payload。

    额外带 source=manual_edit / node_token / title 以便追溯；broadcast 只读
    url/digest_local_path/date/line/status，额外字段无害。
    """
    return {
        "date": date,
        "url": url,
        "status": "success",
        "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "digest_local_path": digest_local_path,
        "line": line,
        "source": "manual_edit",
        "node_token": node_token,
        "title": title,
    }


def write_final_state(line: str, payload: dict, state_dir: Path = DEFAULT_STATE_DIR) -> Path:
    """写到对应 state 文件：main→last_digest_main.json / sub→last_digest.json。"""
    if line not in _STATE_FILES:
        raise ValueError(f"line must be one of {sorted(_STATE_FILES)}, got {line!r}")
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    target = state_dir / _STATE_FILES[line]
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("digest_file")
    ap.add_argument("--title", default="HH Research Daily · 2026-06-02")
    ap.add_argument("--notify-user", default=None)
    ap.add_argument("--headline-count", type=int, default=4)
    ap.add_argument("--signal-count", type=int, default=25)
    ap.add_argument("--mark-final", action="store_true",
                    help="发布成功后把本次 url 写入 state 供 broadcast 消费")
    ap.add_argument("--line", choices=["main", "sub"], default="main",
                    help="--mark-final 写哪条 state（main→last_digest_main.json）")
    ap.add_argument("--date", default=None, help="state date 字段，默认今天")
    args = ap.parse_args()

    xml = Path(args.digest_file).read_text(encoding="utf-8")
    print(f"发布 {args.digest_file}（{len(xml)} chars）...")
    result = publish_digest(title=args.title, markdown=xml)
    print(f"  published: {result['url']}")

    try:
        from publish_with_anchors import inject_anchors_inplace
        ar = inject_anchors_inplace(result["obj_token"], wiki_node_token=result.get("node_token"))
        print(f"  anchors resolved: {len(ar['anchor_map'])} · markers deleted: {ar['markers_deleted']}")
    except Exception as e:  # noqa: BLE001
        print(f"  anchor injection skipped: {e}")

    if args.notify_user:
        ok = notify_digest_ready(
            user_open_id=args.notify_user, title=args.title, doc_url=result["url"],
            signal_count=args.signal_count, headline_count=args.headline_count,
        )
        print(f"  notification sent: {ok}")

    if args.mark_final:
        date = args.date or datetime.now().strftime("%Y-%m-%d")
        payload = build_state_payload(
            line=args.line, date=date, url=result["url"],
            node_token=result.get("node_token", ""),
            digest_local_path=str(args.digest_file), title=args.title,
        )
        target = write_final_state(args.line, payload)
        print(f"  state written: {target} (line={args.line}, url={result['url']})")

    print(f"\nDONE url: {result['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
