#!/usr/bin/env python3
"""v8.0 headline classifier 9-day backtest (Plan v3 §11.3).

Reads signals from Bitable for 5-19 ~ 5-27, runs v8 classifier + selector,
and produces an evidence-based report comparing v8 selection vs v7 actual
headlines.

Output: docs/reports/2026-05-28-v8-backtest.md

Usage:
    python scripts/backtest_headlines.py
    python scripts/backtest_headlines.py --start 2026-05-19 --end 2026-05-27
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from hh_research.pipeline.headline_classifier import HeadlineClassifier
from hh_research.pipeline.headline_selector import HeadlineSelector
from hh_research.storage.schemas import Signal

BASE_TOKEN = "UdwrbpCMoasCs3snCvbcKgbsnfc"
SIGNALS_TABLE_ID = "tbllGsqhy4swhzkz"
WHITELIST_TABLE_ID = "tblpVgQBAkPptnip"
P0_WHITELIST_PATH = "config/p0_whitelist.yml"


def load_tier_lookup() -> tuple[dict[str, str], dict[str, str]]:
    """Load name → tier and name → organization from p0_whitelist.yml."""
    data = yaml.safe_load(Path(P0_WHITELIST_PATH).read_text())
    tier_lookup = {}
    org_lookup = {}
    record_to_name = {}
    for e in data["entities"]:
        if e.get("name"):
            tier_lookup[e["name"]] = e["tier"]
            org_lookup[e["name"]] = e.get("org_in_bitable", "")
        record_to_name[e["record_id"]] = e.get("name", "")
    return tier_lookup, org_lookup, record_to_name


def fetch_signals_in_range(start_date: date, end_date: date) -> list[dict[str, Any]]:
    """Fetch signals from Bitable in date range (by '发布时间')."""
    all_rows = []
    offset = 0
    limit = 200
    while True:
        result = subprocess.run(
            ["lark-cli", "base", "+record-list",
             "--as", "user",
             "--base-token", BASE_TOKEN,
             "--table-id", SIGNALS_TABLE_ID,
             "--limit", str(limit),
             "--offset", str(offset),
             "--format", "json",
             "--field-id", "来源ID",
             "--field-id", "作者",
             "--field-id", "原文",
             "--field-id", "中文摘要",
             "--field-id", "发布时间",
             "--field-id", "主赛道",
             "--field-id", "入日报",
             "--field-id", "新颖性",
             "--field-id", "关键词",
             "--field-id", "来源",
             "--field-id", "提取JSON"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"record-list failed: {result.stderr[:200]}")
        payload = json.loads(result.stdout)
        data = payload["data"]
        fields_order = data["fields"]
        record_ids = data["record_id_list"]
        rows = data["data"]

        # Filter by date
        for record_id, vals in zip(record_ids, rows):
            row = {"record_id": record_id}
            for i, fname in enumerate(fields_order):
                row[fname] = vals[i]

            # Parse 发布时间 (ms timestamp or datetime string)
            ts = row.get("发布时间")
            if isinstance(ts, (int, float)):
                # Bitable returns datetime as ms epoch
                dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
            elif isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    continue
            else:
                continue

            # Convert to BJT date
            bjt_date = (dt + timedelta(hours=8)).date()
            if start_date <= bjt_date <= end_date:
                row["_bjt_date"] = bjt_date
                all_rows.append(row)

        if not data.get("has_more", False):
            break
        offset += limit
        if offset > 5000:  # safety
            break

    return all_rows


def _first(v: Any) -> Any:
    if isinstance(v, list):
        return v[0] if v else None
    return v


def row_to_signal(row: dict[str, Any], record_to_name: dict[str, str]) -> Signal | None:
    """Convert Bitable row to Signal."""
    source_id = row.get("来源ID") or ""
    if not source_id:
        return None

    # Resolve 作者 link
    # Bitable link field format: [{'id': 'recXXX'}, ...]
    authors_link = row.get("作者") or []
    author_name = "Unknown"
    if isinstance(authors_link, list) and authors_link:
        first = authors_link[0]
        if isinstance(first, dict):
            rec_id = first.get("id")
            if rec_id:
                author_name = record_to_name.get(rec_id, "Unknown")

    raw_text = row.get("原文") or ""
    summary_zh = row.get("中文摘要")
    track = _first(row.get("主赛道"))
    source_str = _first(row.get("来源")) or "x"
    novelty = row.get("新颖性")

    # Map source enum
    source_map = {"x": "x", "arxiv": "arxiv", "openalex": "openalex", "rss": "rss"}
    src = source_map.get(source_str, "other")

    # 发布时间
    ts = row.get("发布时间")
    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    elif isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    try:
        return Signal(
            source=src,
            source_id=source_id,
            author_name=author_name,
            url=row.get("链接") or "https://example.com",
            raw_text=str(raw_text),
            lang="en",
            created_at=dt,
            fetched_at=dt,
            summary_zh=str(summary_zh) if summary_zh else None,
            track=track if track in (
                "基础模型", "认知模型", "多模态智能", "世界模型", "AI infra", "ai4s", "其他"
            ) else None,
            novelty_score=int(novelty) if isinstance(novelty, (int, float)) else None,
        )
    except Exception as e:
        print(f"⚠️ Skip row {source_id}: {e}", file=sys.stderr)
        return None


def run_backtest(start: date, end: date) -> dict[str, Any]:
    print(f"📥 Loading P0 whitelist...")
    tier_lookup, org_lookup, record_to_name = load_tier_lookup()
    print(f"   {len(tier_lookup)} entities in lookup")

    print(f"📥 Fetching signals from Bitable {start} ~ {end}...")
    rows = fetch_signals_in_range(start, end)
    print(f"   {len(rows)} rows fetched")

    # Group by BJT date
    by_date: dict[date, list[Signal]] = {}
    skipped = 0
    for row in rows:
        sig = row_to_signal(row, record_to_name)
        if sig is None:
            skipped += 1
            continue
        by_date.setdefault(row["_bjt_date"], []).append(sig)
    print(f"   {sum(len(v) for v in by_date.values())} signals usable, {skipped} skipped")

    # Run classifier + selector per day (with cross-day suppression accumulating)
    cross_day_keys: set[str] = set()
    daily_results = []
    for day in sorted(by_date.keys()):
        signals = by_date[day]
        clf = HeadlineClassifier(
            tier_lookup=tier_lookup,
            organization_lookup=org_lookup,
            cross_day_event_keys=set(cross_day_keys),
        )
        classified = clf.classify_many(signals)
        selector = HeadlineSelector()
        result = selector.select(classified)

        # Accumulate event keys from auto headlines for cross-day suppression
        for s in result.auto_headlines:
            if s.canonical_event_key:
                cross_day_keys.add(s.canonical_event_key)

        # Event type distribution
        et_counts: dict[str, int] = {}
        for s in classified:
            if s.event_type:
                et_counts[s.event_type] = et_counts.get(s.event_type, 0) + 1

        daily_results.append({
            "date": day.isoformat(),
            "total_signals": len(classified),
            "auto_headlines": [
                {
                    "source_id": s.source_id,
                    "author": s.author_name,
                    "event_type": s.event_type,
                    "rule": s.constraint_rule,
                    "m_sum": sum(filter(None, [s.m1_score, s.m2_score, s.m3_score, s.m4_score, s.m5_score])),
                    "text_preview": (s.summary_zh or s.raw_text or "")[:200],
                }
                for s in result.auto_headlines
            ],
            "edge_cases": [
                {
                    "source_id": s.source_id,
                    "author": s.author_name,
                    "event_type": s.event_type,
                    "m_sum": sum(filter(None, [s.m1_score, s.m2_score, s.m3_score, s.m4_score, s.m5_score])),
                    "text_preview": (s.summary_zh or s.raw_text or "")[:200],
                }
                for s in result.edge_cases[:5]
            ],
            "auto_count": len(result.auto_headlines),
            "edge_count": len(result.edge_cases),
            "body_count": len(result.body_signals),
            "suppressed_count": len(result.suppressed),
            "event_type_distribution": et_counts,
        })

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "total_days": len(by_date),
            "total_signals": sum(len(v) for v in by_date.values()),
            "skipped_rows": skipped,
        },
        "daily_results": daily_results,
    }


def write_report(results: dict[str, Any], output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    lines = []
    md = results["metadata"]
    daily = results["daily_results"]

    lines.append("# v8.0 Headline Classifier · 9 天回测报告")
    lines.append("")
    lines.append(f"- **生成时间**: {md['generated_at']}")
    lines.append(f"- **回测范围**: {md['start_date']} ~ {md['end_date']}")
    lines.append(f"- **总天数**: {md['total_days']}")
    lines.append(f"- **总信号数**: {md['total_signals']}")
    lines.append(f"- **跳过**: {md['skipped_rows']}")
    lines.append("")

    # Summary table
    lines.append("## 1. 每日强约束通过统计")
    lines.append("")
    lines.append("| 日期 | 信号总数 | 自动头条 | 边缘 case | 正文 | 合并去重 |")
    lines.append("|---|---|---|---|---|---|")
    auto_total = 0
    for d in daily:
        lines.append(f"| {d['date']} | {d['total_signals']} | "
                     f"**{d['auto_count']}** | {d['edge_count']} | "
                     f"{d['body_count']} | {d['suppressed_count']} |")
        auto_total += d["auto_count"]
    avg = auto_total / max(len(daily), 1)
    lines.append("")
    lines.append(f"**平均每天自动头条**: {avg:.2f}（目标 1-2/天，理论上限 2）")
    lines.append("")

    # Per-day detail
    lines.append("## 2. 每日详情")
    lines.append("")
    for d in daily:
        lines.append(f"### {d['date']}")
        lines.append("")
        lines.append(f"**信号总数**: {d['total_signals']} | "
                     f"**自动头条**: {d['auto_count']} | "
                     f"**边缘 case**: {d['edge_count']}")
        lines.append("")

        if d["event_type_distribution"]:
            lines.append("**Event type 分布**:")
            for et, n in sorted(d["event_type_distribution"].items(), key=lambda x: -x[1]):
                lines.append(f"- {et}: {n}")
            lines.append("")

        if d["auto_headlines"]:
            lines.append("**🔴 强约束自动头条**:")
            for h in d["auto_headlines"]:
                lines.append(f"- **[{h['event_type']}]** · "
                             f"`{h['rule']}` · m_sum={h['m_sum']} · "
                             f"{h['author']}: {h['text_preview'][:120]}...")
            lines.append("")

        if d["edge_cases"]:
            lines.append("**🟡 边缘 case 候选**（top 5, 按 m_sum 排序）:")
            for h in d["edge_cases"]:
                lines.append(f"- m_sum={h['m_sum']} · "
                             f"[{h['event_type']}] · "
                             f"{h['author']}: {h['text_preview'][:100]}...")
            lines.append("")

    # Event type aggregate
    lines.append("## 3. Event Type 整体分布")
    lines.append("")
    et_agg: dict[str, int] = {}
    for d in daily:
        for et, n in d["event_type_distribution"].items():
            et_agg[et] = et_agg.get(et, 0) + n
    lines.append("| Event Type | 总数 | 占比 |")
    lines.append("|---|---|---|")
    total_with_et = sum(et_agg.values()) or 1
    for et, n in sorted(et_agg.items(), key=lambda x: -x[1]):
        pct = 100 * n / total_with_et
        lines.append(f"| {et} | {n} | {pct:.1f}% |")
    lines.append("")

    lines.append("## 4. 关键 finding & 建议")
    lines.append("")
    lines.append("> 待人工 review 后填写")
    lines.append("")
    if avg < 0.5:
        lines.append("- ⚠️ **平均通过 < 0.5/天 → 规则可能过严**, 建议放宽部分条件")
    elif avg > 2.5:
        lines.append("- ⚠️ **平均通过 > 2.5/天 → 规则可能过松**, 建议收紧")
    else:
        lines.append(f"- ✅ 平均 {avg:.2f}/天 在合理范围 1-2 内")
    lines.append("")

    Path(output_path).write_text("\n".join(lines))
    print(f"\n✅ Report written to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-05-19", help="start date YYYY-MM-DD (BJT)")
    parser.add_argument("--end", default="2026-05-27", help="end date YYYY-MM-DD (BJT)")
    parser.add_argument("--output", default="docs/reports/2026-05-28-v8-backtest.md")
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start).date()
    end = datetime.fromisoformat(args.end).date()

    results = run_backtest(start, end)

    # Also dump raw JSON for analysis
    json_path = args.output.replace(".md", ".json")
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(json_path).write_text(json.dumps(results, indent=2, ensure_ascii=False))

    write_report(results, args.output)

    # Print summary
    print("\n📊 Backtest summary:")
    auto_sum = sum(d["auto_count"] for d in results["daily_results"])
    avg = auto_sum / max(len(results["daily_results"]), 1)
    print(f"  Average auto-headlines/day: {avg:.2f}")
    print(f"  Total days: {len(results['daily_results'])}")
    print(f"  Total signals: {results['metadata']['total_signals']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
