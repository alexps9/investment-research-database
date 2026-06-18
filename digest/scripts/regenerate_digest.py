"""Regenerate daily digest from Bitable signals (skip collection + extract).

Useful when:
  - The pipeline succeeded through extract + write_signals but the digest LLM
    call failed (timeout / empty output / etc.) — no need to recollect.
  - You want to iterate on prompt without re-paying for collection + extraction.

Usage:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/regenerate_digest.py 2026-04-27 --publish
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.extract.claude_client import CostTracker  # noqa: E402
from hh_research.extract.daily_writer import DailyWriter, should_enrich_authors  # noqa: E402
from hh_research.extract.author_enricher import (  # noqa: E402
    get_arxiv_full_authors,
    enrich_paper_coauthors,  # V3.2 fallback
)
from hh_research.extract.researcher_mapping import (  # noqa: E402
    enrich_paper_coauthors_v4,  # V4 双源 + 审查 agent — RM 准确性优化
)
from hh_research.storage.bitable_client import (  # noqa: E402
    _build_whitelist_name_index,
    _lark_cli,
    read_whitelist,
)
from hh_research.storage.schemas import Signal  # noqa: E402
from hh_research.utils.logger import get_logger  # noqa: E402

log = get_logger("regenerate_digest")


def _norm_name(s: str) -> str:
    """Normalize an author name for whitelist matching (same algo as bitable_client)."""
    import re
    return re.sub(r"[^\w一-鿿]+", "", (s or "").lower()).strip()


def _resolve_whitelist(author_name: str, people: list[str], wl_index: dict[str, str]) -> str | None:
    """Match an author against the whitelist index. Returns record_id or None.

    Tries the primary author_name, then each entity in `people`.
    """
    for cand in [author_name, *people]:
        if not cand:
            continue
        rid = wl_index.get(_norm_name(cand))
        if rid:
            return rid
        # Also try the part before any parens (English-only variant)
        import re
        base = re.sub(r"[\(（].+?[\)）]", "", cand).strip()
        if base and base != cand:
            rid = wl_index.get(_norm_name(base))
            if rid:
                return rid
    return None


# Cache for arxiv-author lookups: source_id → (matched_whitelist_name, record_id) | None
_arxiv_author_cache: dict[str, tuple[str, str] | None] = {}


def _fetch_arxiv_authors(arxiv_id: str) -> list[str]:
    """Fetch full author list from the arxiv abstract HTML page.

    Returns names in 'Firstname Lastname' order (arxiv stores 'Lastname, Firstname').
    Falls back to [] on HTTP error.
    """
    import re
    import httpx
    UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 Chrome/121.0"}
    url = f"https://arxiv.org/abs/{arxiv_id}"
    try:
        with httpx.Client(headers=UA, timeout=20.0, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code != 200:
                return []
            html = r.text
        raw = re.findall(r'<meta name="citation_author" content="([^"]+)"', html)
        out = []
        for a in raw:
            if "," in a:
                last, first = a.split(",", 1)
                out.append(f"{first.strip()} {last.strip()}")
            else:
                out.append(a.strip())
        return out
    except Exception:  # noqa: BLE001
        return []


def _enrich_arxiv_whitelist(arxiv_id: str, wl_index_first_last: dict[str, str]) -> tuple[str, str] | None:
    """For an arxiv paper, fetch HTML to get full author list, match against
    a first+last-token whitelist index. Returns (matched_author_name, record_id) or None.

    Uses _arxiv_author_cache to avoid repeated fetches across runs in same process.
    """
    import re
    if arxiv_id in _arxiv_author_cache:
        return _arxiv_author_cache[arxiv_id]
    authors = _fetch_arxiv_authors(arxiv_id)
    matched = None
    for a in authors:
        tok = a.split()
        if len(tok) >= 2:
            k = (tok[0] + " " + tok[-1]).lower()
            if k in wl_index_first_last:
                matched = (a, wl_index_first_last[k])
                break
    _arxiv_author_cache[arxiv_id] = matched
    return matched


def _build_first_last_index() -> dict[str, str]:
    """Build 'firstname lastname' (lowercased) → record_id index. Same algo as
    arxiv_collector.collect_by_window so we reproduce its matches.
    """
    import re
    from hh_research.storage.bitable_client import read_whitelist
    idx: dict[str, str] = {}
    for e in read_whitelist():
        if not e.name:
            continue
        cleaned = re.sub(r"[一-鿿㐀-䶿()()\[\]【】]+", " ", e.name)
        tokens = [t for t in cleaned.split() if len(t) >= 2]
        if len(tokens) < 2:
            continue
        key = (tokens[0] + " " + tokens[-1]).lower()
        if key not in idx:
            idx[key] = e.record_id
    return idx


def _as_list(v):
    """Coerce a value to list — handles bitable's JSON-string-of-list quirk."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return [s] if s else []
    return [v]


def fetch_signals_for_date(
    date_str: str,
    cst: bool = False,
    since_override: datetime | None = None,
    until_override: datetime | None = None,
) -> list[Signal]:
    """Read all rows from Bitable signals where created_at falls within the window.

    date_str: 'YYYY-MM-DD'.
    cst=False (default): treat as UTC day → [date 00:00, date+1 00:00) UTC.
    cst=True: treat as Beijing "N 日的日报" semantic → 北京 (N-1) 0:00 → N 0:00 =
              UTC (N-1) - 8h → UTC N - 8h.
    since_override / until_override: explicit UTC datetime, overrides date_str+cst.
    """
    if since_override and until_override:
        target = since_override
        target_end = until_override
        log.info("  explicit window: UTC %s → %s", target.isoformat(), target_end.isoformat())
    elif cst:
        n = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        # 北京 (N-1) 0:00 = UTC (N-1) - 8h ; 北京 N 0:00 = UTC N - 8h
        target = n - timedelta(days=1, hours=8)
        target_end = n - timedelta(hours=8)
        log.info("  CST window: UTC %s → %s", target.isoformat(), target_end.isoformat())
    else:
        target = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        target_end = target + timedelta(days=1)

    app_token = os.environ["HH_BITABLE_APP_TOKEN"]
    table_id = os.environ["HH_SIGNALS_TABLE_ID"]

    # v5: 加载白名单索引以便 author_record_id 富化（headline_score 依赖此字段）
    # Two indices:
    #   wl_index: normalized full-name → record_id (used for LLM-extracted people[])
    #   wl_first_last: 'firstname lastname' (lower) → record_id (same as collector)
    log.info("  loading whitelist indices for author matching...")
    wl_index = _build_whitelist_name_index()
    wl_first_last = _build_first_last_index()
    log.info("  whitelist sizes: full-name=%d, first-last=%d", len(wl_index), len(wl_first_last))

    signals: list[Signal] = []
    offset = 0
    while True:
        resp = _lark_cli(
            "base", "+record-list",
            "--base-token", app_token,
            "--table-id", table_id,
            "--limit", "200",
            "--offset", str(offset),
        )
        data = resp.get("data", {})
        fields = data.get("fields", [])
        rows = data.get("data", [])
        if not rows:
            break
        idx = {n: i for i, n in enumerate(fields)}

        # After the 2026-05-16 Chinese rename, fields use Chinese names.
        # Try English (legacy) first, fall back to Chinese (current).
        FIELD_ALIAS = {
            "extract_json": "提取JSON",
            "created_at":   "发布时间",
            "fetched_at":   "抓取时间",
            "source_id":    "来源ID",
            "source":       "来源",
            "url":          "链接",
            "作者":          "作者",  # Bitable link field, holds whitelist record_id
            "raw_text":     "原文",
            "summary_zh":   "中文摘要",
            "category":     "主赛道",
            "subcategory":  "子赛道",
            "key_terms":    "关键词",
            "novelty_score":"新颖性",
        }

        def get(row, name):
            i = idx.get(name)
            if i is None:
                i = idx.get(FIELD_ALIAS.get(name, ""))
            return row[i] if i is not None else None

        for row in rows:
            extract_json = get(row, "extract_json")
            if not extract_json:
                continue
            try:
                extract = json.loads(extract_json) if isinstance(extract_json, str) else extract_json
            except (json.JSONDecodeError, TypeError):
                continue
            # Date filter using the row's created_at field
            ca = get(row, "created_at")
            if isinstance(ca, (int, float)):
                ca_dt = datetime.fromtimestamp(ca / 1000, tz=timezone.utc)
            elif isinstance(ca, str):
                try:
                    ca_dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                    if ca_dt.tzinfo is None:
                        ca_dt = ca_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            else:
                continue
            if not (target <= ca_dt < target_end):
                continue

            sid = get(row, "source_id") or "unknown"
            src_raw = get(row, "source")
            src = src_raw[0] if isinstance(src_raw, list) and src_raw else (src_raw or "other")
            url = get(row, "url") or ""
            raw_text = get(row, "raw_text") or ""

            # Reconstruct Signal from extract_json + minimal Bitable fields
            track_raw = extract.get("track")
            people = (extract.get("entities") or {}).get("people") or []
            author_name = people[0] if people else (extract.get("signal_source_zh") or sid)
            # v5: resolve whitelist record_id (for _is_whitelist_author / headline boost)
            # Priority 1: Bitable '作者' link field (already resolved by collector)
            wl_rid = None
            authors_field = get(row, "作者")
            if authors_field and isinstance(authors_field, list):
                for item in authors_field:
                    if isinstance(item, dict) and item.get("id"):
                        wl_rid = item["id"]
                        break
            # Priority 2: local name index against LLM-extracted people[]
            if wl_rid is None:
                wl_rid = _resolve_whitelist(author_name, people, wl_index)
            # Priority 3 (arxiv only): fetch HTML, match against first+last index
            if wl_rid is None and src == "arxiv":
                arxiv_id = sid.removeprefix("arxiv:").split("v")[0]
                hit = _enrich_arxiv_whitelist(arxiv_id, wl_first_last)
                if hit:
                    matched_name, wl_rid = hit
                    author_name = matched_name  # overwrite to the whitelist author
                    log.info("    arxiv enrich: %s → %s (wl=%s)", sid, matched_name, wl_rid)
            sig = Signal(
                source=src if src in ("x", "arxiv", "openalex", "rss", "other") else "other",
                source_id=sid,
                author_name=author_name,
                author_record_id=wl_rid,
                url=url,
                raw_text=raw_text,
                lang="en",
                created_at=ca_dt,
                fetched_at=ca_dt,
                summary_zh=extract.get("summary_zh"),
                cognitive_takeaway_zh=extract.get("cognitive_takeaway_zh"),
                track=track_raw if track_raw in ("基础模型", "认知模型", "多模态智能", "世界模型", "AI infra", "ai4s", "其他") else None,
                is_headline_candidate=bool(extract.get("is_headline_candidate", False)),
                headline_priority=int(extract.get("headline_priority", 1)),
                core_findings_zh=_as_list(extract.get("core_findings_zh", [])),
                method_framework_zh=extract.get("method_framework_zh") or None,
                method_detail_zh=extract.get("method_detail_zh") or None,
                result_summary_zh=extract.get("result_summary_zh") or None,
                key_terms=_as_list(extract.get("key_terms", [])),
                novelty_score=extract.get("novelty_score"),
                signal_source_zh=extract.get("signal_source_zh"),
                needs_human_review=False,
                extract_json=extract_json if isinstance(extract_json, str) else json.dumps(extract_json),
            )
            signals.append(sig)

        if not data.get("has_more"):
            break
        offset += 200

    return signals


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("date", help="日期 YYYY-MM-DD (默认 UTC；加 --cst 用北京'N 日的日报'语义)")
    ap.add_argument("--cst", action="store_true",
                    help="按北京时间 N 日的日报 = UTC (N-1)-8h → N-8h 窗口取信号")
    ap.add_argument("--publish", action="store_true", help="publish to Feishu wiki")
    ap.add_argument("--skip-author-enrich", action="store_true",
                    help="跳过 coauthor enrich(最慢步)；预览默认已跳过，此 flag 在 --publish 时也强制跳过")
    ap.add_argument("--allow-review-fail", action="store_true",
                    help="Allow publish even if v7 quality gate has blocking issues")
    ap.add_argument("--notify-user", type=str, default=None)
    ap.add_argument("--title-suffix", type=str, default="",
                    help="附加到标题末尾，如 'V2' → 'HH Research Daily 2026-05-20 V2'")
    ap.add_argument("--since", type=str, default=None,
                    help="explicit window start (ISO 8601 UTC, e.g. 2026-05-21T00:30:00Z); "
                         "with --until, overrides date+cst")
    ap.add_argument("--until", type=str, default=None,
                    help="explicit window end (ISO 8601 UTC); use with --since")
    args = ap.parse_args()

    since_override = until_override = None
    if args.since and args.until:
        since_override = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
        until_override = datetime.fromisoformat(args.until.replace("Z", "+00:00"))
        if since_override.tzinfo is None:
            since_override = since_override.replace(tzinfo=timezone.utc)
        if until_override.tzinfo is None:
            until_override = until_override.replace(tzinfo=timezone.utc)
        print(f"Reading signals for explicit window {since_override.isoformat()} → {until_override.isoformat()} from Bitable ...")
    else:
        print(f"Reading signals for {args.date} ({'CST' if args.cst else 'UTC'}) from Bitable ...")
    signals = fetch_signals_for_date(args.date, cst=args.cst,
                                       since_override=since_override,
                                       until_override=until_override)
    print(f"  found {len(signals)} signals")
    if not signals:
        print("Nothing to do.")
        return

    # v6 (5.21): enrich arxiv signals with full coauthor list via 5.18 strategy
    # (AnySearch + arxiv HTML co-first detection + whitelist Bitable fallback)
    # 注意：fetch 时已 enrich author_record_id（含 HTML matching），这里覆盖所有 arxiv with wl_rid
    arxiv_signals = [s for s in signals if s.source == "arxiv" and s.author_record_id]
    _do_enrich = should_enrich_authors(publish=args.publish, skip_flag=args.skip_author_enrich)
    print(f"\n[author enrich] {len(arxiv_signals)} 篇白名单 arxiv 论文（按 author_record_id）；enrich={_do_enrich}")
    if arxiv_signals and not _do_enrich:
        print("[author enrich] 跳过（预览或 --skip-author-enrich）——提速；coauthor/RM 不刷新")
    if arxiv_signals and _do_enrich:
        print(f"\n[author enrich] Enriching coauthors for {len(arxiv_signals)} whitelisted arxiv papers ...")
        # Build whitelist lookup by name for enrich_paper_coauthors
        wl_entries = read_whitelist()
        wl_by_name: dict[str, object] = {}
        for e in wl_entries:
            if e.name:
                wl_by_name[e.name] = e
        for sig in arxiv_signals:
            arxiv_id = sig.source_id.removeprefix("arxiv:").split("v")[0]
            print(f"  · {arxiv_id} ({sig.author_name})", end=" ")
            try:
                full_authors = get_arxiv_full_authors(arxiv_id)
                if not full_authors:
                    print("✗ no authors")
                    continue
                # Match whitelist by full name
                wl_match = {n: wl_by_name[n] for n in full_authors if n in wl_by_name}
                # V4 双源 + 审查 agent（对齐 daily.py 默认）
                sig.coauthors = enrich_paper_coauthors_v4(
                    arxiv_id=arxiv_id,
                    authors=full_authors,
                    whitelist_match=wl_match,
                    parallel_workers=4,
                )
                wl_hits = sum(1 for c in sig.coauthors if c.is_whitelist)
                verified_n = sum(
                    sum(1 for v in c.verification.values() if v == "verified")
                    for c in sig.coauthors
                )
                print(f"→ {len(sig.coauthors)} coauthors ({wl_hits} whitelist, {verified_n} verified fields)")
            except Exception as e:  # noqa: BLE001
                print(f"✗ {e}")
        print()

    cost = CostTracker()
    writer = DailyWriter(cost=cost)
    target_dt = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    # 与 daily.py 一致：白名单 tier 加权头条（regenerate 此前漏传，头条选择会与生产不一致）
    tier_lookup = {e.record_id: e.tier for e in read_whitelist() if e.tier}
    digest = writer.write(target_dt, signals, tier_lookup=tier_lookup)
    print(f"  digest: {len(digest.markdown)} chars; cost {cost.summary()}")

    digests_dir = Path("data/digests")
    digests_dir.mkdir(parents=True, exist_ok=True)
    digest_path = digests_dir / f"digest_{args.date}.md"
    digest_path.write_text(digest.markdown, encoding="utf-8")
    print(f"  saved to {digest_path}")

    # v7.0 P0 quality gate: run review before publish
    # (plan ref: /Users/haolinguo/Desktop/2026-05-28-v7-quality-gates.md Task 4)
    from hh_research.quality.digest_rules import review_xml_text

    review = review_xml_text(digest.markdown, source="file")
    review_path = digests_dir / f"review_{args.date}.md"
    review_path.write_text(review.to_markdown(), encoding="utf-8")
    print(f"  quality review: {review.blocking_count} blocking, {review.warning_count} warnings")
    print(f"  review saved to {review_path}")

    if review.has_blocking and args.publish and not args.allow_review_fail:
        print(f"  ⛔ publish BLOCKED by quality gate ({review.blocking_count} blocking issues).")
        print(f"     Re-run with --allow-review-fail to override.")
        print(f"     Review report: {review_path}")
        return

    if args.publish:
        from hh_research.publish.lark_doc_publisher import (
            insert_signal_images, notify_digest_ready, publish_digest,
        )
        title = f"HH Research Daily {args.date}"
        if args.title_suffix:
            title = f"{title} {args.title_suffix}"
        result = publish_digest(title=title, markdown=digest.markdown)
        print(f"  published: {result['url']}")

        # Task5: 只对 arxiv 论文提图（非 arxiv 为 no-op），头条优先（保证头条配图）；
        # 阶段总预算 — 超时跳过剩余、不阻塞已发布正文，并留可重试命令。
        from hh_research.extract.image_extractor import enrich_signal_with_images
        import os as _os
        import time as _t
        _headline_set = set(digest.headline_signal_ids)
        arxiv_imgs = sorted(
            [s for s in signals if s.source == "arxiv"],
            key=lambda s: s.source_id not in _headline_set,  # 头条 arxiv 排前
        )
        _budget = float(_os.getenv("HH_IMAGE_BUDGET_SECONDS", "480"))
        _t0 = _t.monotonic()
        _done = _failed = 0
        for s in arxiv_imgs:
            if _t.monotonic() - _t0 > _budget:
                print(f"  ⚠ image budget {_budget:.0f}s exceeded — 跳过剩余 "
                      f"{len(arxiv_imgs) - _done - _failed} 篇（正文已发布，不阻塞）")
                break
            try:
                enrich_signal_with_images(s, max_images_per_paper=1)
                _done += 1
            except Exception as e:  # noqa: BLE001
                _failed += 1
                log.warning("image enrich failed for %s: %s", s.source_id, e)
        n_with_imgs = sum(1 for s in signals if s.image_urls)
        print(f"  enriched {n_with_imgs}/{len(arxiv_imgs)} arxiv (done={_done} failed={_failed}, "
              f"headline-first)；可重试: .venv/bin/python scripts/regenerate_digest.py {args.date} --publish")

        img_counts = insert_signal_images(
            obj_token=result["obj_token"],
            signals=signals,
            max_per_signal=1,
        )
        print(f"  image insertion: {img_counts}")

        # Anchor injection (TL;DR ↗ → block_id within wiki node)
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from publish_with_anchors import inject_anchors_inplace
            print(f"\n  injecting anchors ...")
            anchor_r = inject_anchors_inplace(
                result["obj_token"],
                wiki_node_token=result.get("node_token"),
            )
            print(f"  anchors resolved: {len(anchor_r['anchor_map'])} · markers deleted: {anchor_r['markers_deleted']}")
        except Exception as e:  # noqa: BLE001
            print(f"  anchor injection skipped: {e}")

        if args.notify_user:
            ok = notify_digest_ready(
                user_open_id=args.notify_user,
                title=title,
                doc_url=result["url"],
                signal_count=len(signals),
                headline_count=sum(1 for s in signals if s.is_headline_candidate),
            )
            print(f"  notification sent: {ok}")


if __name__ == "__main__":
    main()
