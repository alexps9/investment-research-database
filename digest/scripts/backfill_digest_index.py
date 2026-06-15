#!/usr/bin/env python
"""历史日报回填:从 runtime corpus(digests + logs)推 date->canonical 飞书 URL + 元数据,
产出 backfill-review.csv 供人工抽查,--apply-review 后写入 web index。

用法:
  # 1. 只读 preflight
  python scripts/backfill_digest_index.py --digests-dir data/digests --logs-dir data/logs --preflight
  # 2. dry-run 产出 review.csv
  python scripts/backfill_digest_index.py --digests-dir data/digests --logs-dir data/logs --dry-run
  # 3. 人工抽查 data/backfill-review.csv 后 apply 到 web index
  python scripts/backfill_digest_index.py --digests-dir data/digests --logs-dir data/logs \
      --index ../web/public/data/digests-index.json --apply-review data/backfill-review.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hh_research.publish.digest_index import extract_digest_meta, upsert_entry  # noqa: E402

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_NODE_RE = re.compile(r"creating wiki node:\s*(.+?)\s*$")
_PUB_RE = re.compile(r"published:\s*(https://\S+)")
_VARIANT_MARKERS = (
    "demo", "v2", "v3", "v4", "v5", "v6", "trial", "修复", "修正", "personal",
    "完整预览", "对比", "画像", "trace", "(retry)", "测试", "insights", "tl;dr",
)
_EXCLUDE_FILE_MARKERS = (".bak", "_backup", "_compare", "_personal", "demo")


def pick_canonical(date: str, digests_dir: Path) -> Path | None:
    digests_dir = Path(digests_dir)
    plain_md = digests_dir / f"digest_{date}.md"
    if plain_md.exists():
        return plain_md
    plain_xml = digests_dir / f"digest_{date}.xml"
    if plain_xml.exists():
        return plain_xml

    def candidates(suffix: str) -> list[Path]:
        out = []
        for p in digests_dir.glob(f"digest_{date}*{suffix}"):
            low = p.name.lower()
            if any(m in low for m in _EXCLUDE_FILE_MARKERS):
                continue
            out.append(p)
        return sorted(out, key=lambda p: p.stat().st_mtime, reverse=True)

    for suffix in (".md", ".xml"):
        c = candidates(suffix)
        if c:
            return c[0]
    return None


def parse_publisher_log_pairs(lines: Iterable[str]) -> list[dict]:
    """把 'creating wiki node: <title>' 与其后最近一条 'published: <url>' 配对。"""
    pairs: list[dict] = []
    pending: str | None = None
    for line in lines:
        m = _NODE_RE.search(line)
        if m:
            pending = m.group(1).strip()
            continue
        m = _PUB_RE.search(line)
        if m and pending is not None:
            pairs.append({"title": pending, "url": m.group(1)})
            pending = None
    return pairs


def classify_title(title: str) -> tuple[str | None, str]:
    """返回 (date, kind),kind ∈ {main, clean, variant}。"""
    md = _DATE_RE.search(title)
    date = md.group(1) if md else None
    low = title.lower()
    if "主线" in title and "(retry)" not in low:
        return date, "main"
    if any(v in low for v in _VARIANT_MARKERS):
        return date, "variant"
    return date, "clean"


def choose_url_for_date(date: str, pairs_by_date: dict) -> tuple[str, str, str, list]:
    """pairs_by_date[date] = [(kind, title, url), ...]。返回 (url, confidence, source, alts)。"""
    cands = pairs_by_date.get(date, [])
    if not cands:
        return "", "low", "none", []
    mains = [c for c in cands if c[0] == "main"]
    cleans = [c for c in cands if c[0] == "clean"]
    alts = [c[2] for c in cands]
    if mains:
        return mains[-1][2], "high", "log_main", alts
    if len(cleans) == 1:
        return cleans[0][2], "medium", "log_clean", alts
    if cleans:
        return cleans[-1][2], "low", "log_clean_multi", alts
    return cands[-1][2], "low", "log_variant", alts


def build_pairs_by_date(logs_dir: Path) -> dict:
    out: dict = {}
    for log in sorted(Path(logs_dir).rglob("*.log")):
        try:
            lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for pair in parse_publisher_log_pairs(lines):
            date, kind = classify_title(pair["title"])
            if not date:
                continue
            out.setdefault(date, []).append((kind, pair["title"], pair["url"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--digests-dir", required=True)
    ap.add_argument("--logs-dir", required=True)
    ap.add_argument("--index", help="web index path (apply 时必填)")
    ap.add_argument("--review-csv", default="data/backfill-review.csv")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply-review", metavar="CSV", help="读已审 CSV 的 chosen_url/confidence 写入 index")
    args = ap.parse_args()

    digests_dir = Path(args.digests_dir)
    logs_dir = Path(args.logs_dir)
    if not digests_dir.is_dir() or not logs_dir.is_dir():
        print(f"[backfill] missing dir: digests={digests_dir} logs={logs_dir}", file=sys.stderr)
        return 2

    pairs_by_date = build_pairs_by_date(logs_dir)
    file_dates = sorted(
        {m.group(1) for p in digests_dir.glob("digest_*") if (m := _DATE_RE.search(p.name))},
        reverse=True,
    )

    if args.preflight:
        print(f"[preflight] digest files: {len(list(digests_dir.glob('digest_*')))}")
        print(f"[preflight] distinct dates from files: {len(file_dates)}")
        print(f"[preflight] dates with log url candidates: {len(pairs_by_date)}")
        print(f"[preflight] dates missing any url: {sorted(set(file_dates) - set(pairs_by_date))}")
        return 0

    # apply-review: 读审过的 CSV,写 index
    if args.apply_review:
        if not args.index:
            print("[backfill] --index required with --apply-review", file=sys.stderr)
            return 2
        n = 0
        with open(args.apply_review, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not row.get("chosen_url"):
                    continue
                upsert_entry(Path(args.index), {
                    "date": row["date"], "title": row.get("title", ""),
                    "signal_count": int(row.get("signal_count") or 0),
                    "tldr": row.get("tldr_preview", ""),
                    "feishu_wiki_url": row["chosen_url"],
                    "source": "manual_review", "line": "main",
                    "confidence": row.get("confidence", "medium"),
                })
                n += 1
        print(f"[backfill] applied {n} rows from review CSV -> {args.index}")
        return 0

    # dry-run(默认): 生成 review.csv
    review_path = Path(args.review_csv)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {"high": 0, "medium": 0, "low": 0}
    with open(review_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "chosen_url", "title", "confidence", "url_source",
                    "digest_path", "signal_count", "tldr_preview", "alt_urls", "notes"])
        for date in file_dates:
            url, conf, src, alts = choose_url_for_date(date, pairs_by_date)
            counts[conf] = counts.get(conf, 0) + 1
            canon = pick_canonical(date, digests_dir)
            title = f"HH Research Daily · {date}"
            sc, tldr = 0, ""
            if canon:
                meta = extract_digest_meta(
                    canon.read_text(encoding="utf-8", errors="ignore"),
                    fallback_title=title, fallback_date=date,
                )
                title, sc, tldr = meta["title"], meta["signal_count"], meta["tldr"]
            w.writerow([date, url, title, conf, src, str(canon or ""), sc,
                        tldr[:120], " | ".join(a for a in alts if a != url), ""])
    print(f"[backfill] wrote {review_path} for {len(file_dates)} dates; confidence: {counts}")
    print("[backfill] 人工检查 confidence != high 的行,改 chosen_url 后用 --apply-review 写入 index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
