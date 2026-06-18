"""批量跑 V4 RM enrich + 统计通过率。

针对 5.21 日报的 8 篇 whitelist 论文，对每位作者：
- 双路 enrich (AnySearch + PyAlex)
- 审查 agent 验证字段
- 输出 verified / rejected / skipped 统计

Usage:
  .venv/bin/python scripts/batch_test_rm_v4.py
  .venv/bin/python scripts/batch_test_rm_v4.py --arxiv-ids 2605.18868,2605.19269

输出：
  - stdout 打印每篇论文每位作者完整 JSON
  - data/state/rm_v4_batch/<date>.json 全量数据
  - 最后通过率统计表
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date as _date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.extract.author_enricher import get_arxiv_full_authors  # noqa: E402
from hh_research.extract.researcher_mapping import enrich_paper_coauthors_v4  # noqa: E402
from hh_research.storage.bitable_client import read_whitelist  # noqa: E402


# 5.21 日报涉及的 8 篇 whitelist 论文
DEFAULT_ARXIV_IDS = [
    "2605.18868",
    "2605.19269",
    "2605.19319",
    "2605.19446",
    "2605.19633",
    "2605.19762",
    "2605.19932",
    "2605.20182",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--arxiv-ids",
        type=str,
        default=",".join(DEFAULT_ARXIV_IDS),
        help="逗号分隔的 arxiv_id 列表（默认 5.21 日报 8 篇 whitelist）",
    )
    ap.add_argument(
        "--out-dir",
        type=str,
        default="data/state/rm_v4_batch",
        help="结果保存目录",
    )
    args = ap.parse_args()

    arxiv_ids = [x.strip() for x in args.arxiv_ids.split(",") if x.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== batch V4 RM enrich for {len(arxiv_ids)} papers ===\n")

    # 1) load whitelist once
    print("loading whitelist from Bitable ...")
    try:
        wl_entries = read_whitelist()
    except Exception as e:  # noqa: BLE001
        print(f"  ! whitelist read failed: {e}; proceeding without")
        wl_entries = []
    wl_by_name = {e.name: e for e in wl_entries if e.name}
    print(f"  → {len(wl_by_name)} whitelist entries loaded\n")

    all_results: list[dict] = []
    field_counter: Counter = Counter()  # verification 状态
    author_outcome: Counter = Counter()  # rejected_whole / verified / partial

    # 2) per paper
    for i, arxiv_id in enumerate(arxiv_ids, 1):
        print(f"[{i}/{len(arxiv_ids)}] paper {arxiv_id}")
        try:
            authors = get_arxiv_full_authors(arxiv_id)
        except Exception as e:  # noqa: BLE001
            print(f"  ! fetch authors failed: {e}; skipping")
            continue
        if not authors:
            print("  ! 0 authors found; skipping")
            continue
        wl_match = {n: wl_by_name[n] for n in authors if n in wl_by_name}
        print(f"  → {len(authors)} authors, {len(wl_match)} whitelist matches")

        try:
            coauthors = enrich_paper_coauthors_v4(
                arxiv_id=arxiv_id,
                authors=authors,
                whitelist_match=wl_match,
                parallel_workers=4,
            )
        except Exception as e:  # noqa: BLE001
            print(f"  ! enrich failed: {e}; skipping")
            continue

        # 统计
        for c in coauthors:
            verifications = c.verification or {}
            if not verifications:
                author_outcome["skipped:no_verification"] += 1
            else:
                # any rejected?
                statuses = list(verifications.values())
                if any(v == "verified" for v in statuses):
                    if any(v.startswith("rejected") for v in statuses):
                        author_outcome["partial_pass"] += 1
                    elif all(v == "verified" or v.startswith("skipped") for v in statuses):
                        author_outcome["all_pass_or_skipped"] += 1
                    else:
                        author_outcome["other"] += 1
                elif any(v.startswith("rejected") for v in statuses):
                    author_outcome["all_rejected"] += 1
                else:
                    author_outcome["all_skipped"] += 1

            for field, status in verifications.items():
                # 把 status 简化（rejected:xxx → rejected）
                bucket = status.split(":")[0] if ":" in status else status
                field_counter[f"{field}:{bucket}"] += 1

        # paper record
        record = {
            "arxiv_id": arxiv_id,
            "n_authors_total": len(authors),
            "n_authors_whitelist": len(wl_match),
            "n_coauthors_on_table": len(coauthors),
            "coauthors": [c.model_dump(exclude_none=False) for c in coauthors],
        }
        all_results.append(record)

        # 打印每位作者简表
        for c in coauthors:
            wl_mark = "★白" if c.is_whitelist else ""
            v = c.verification or {}
            v_str = " ".join(f"{k}={v[k][:8]}" for k in sorted(v.keys()))
            print(f"    · {wl_mark} {c.name} ({c.role}) aff={c.affiliation} gh={c.github} home={c.homepage} | {v_str}")
        print()

    # 3) save full results
    today = _date.today().isoformat()
    out_file = out_dir / f"{today}.json"
    out_file.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2)
    )
    print(f"\n=== saved full data to {out_file} ===\n")

    # 4) 通过率统计
    print("=== 通过率统计 ===\n")
    print(f"总作者数（上 RM 表）: {sum(r['n_coauthors_on_table'] for r in all_results)}")
    print()
    print("作者级 outcome:")
    total_authors = sum(author_outcome.values())
    for outcome, n in author_outcome.most_common():
        pct = 100 * n / total_authors if total_authors else 0
        print(f"  {outcome:30s} {n:4d}  ({pct:.1f}%)")
    print()
    print("字段级 verification:")
    # 按字段分组打印
    fields = sorted(set(k.split(":")[0] for k in field_counter))
    for field in fields:
        print(f"  [{field}]")
        for bucket in ["verified", "rejected", "skipped"]:
            key = f"{field}:{bucket}"
            n = field_counter.get(key, 0)
            total_field = sum(v for k, v in field_counter.items() if k.startswith(field + ":"))
            pct = 100 * n / total_field if total_field else 0
            print(f"    {bucket:10s} {n:4d}  ({pct:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
