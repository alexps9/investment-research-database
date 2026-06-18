"""Main daily pipeline entry point.

Run:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python -m hh_research.pipeline.daily [--days N] [--skip-llm] ...

Steps:
1. Load whitelist from Bitable
2a. Collect from arXiv
2b. Collect from X (socialdata.tools)
3. Dedup against local SQLite seen-set
4. (optional) Run Claude extractor on new signals
5. (optional) Write signals to Bitable
6. (optional) Generate daily digest
7. (optional) Write run metrics to Bitable ops_metrics table
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from hh_research.collectors.arxiv_collector import ArxivCollector  # noqa: E402
from hh_research.collectors.openalex_collector import OpenAlexCollector  # noqa: E402
from hh_research.collectors.rss_collector import RssCollector  # noqa: E402
from hh_research.collectors.x_collector import SocialDataXCollector  # noqa: E402
from hh_research.storage.bitable_client import (  # noqa: E402
    batch_create_signals,
    get_last_pipeline_run_at,
    read_whitelist,
    signal_to_row,
    write_ops_metric,
)
from hh_research.storage.sqlite_dedup import SQLiteDedupStore  # noqa: E402
from hh_research.utils.logger import get_logger  # noqa: E402

log = get_logger("pipeline.daily")

# Task2: whitelist 熔断阈值。main 基线 347 条；低于此值视为读取异常/部分读取，
# pipeline 必须 abort 而非生成残缺日报（6-02 事故根因）。可用 HH_WHITELIST_MIN 覆盖。
WHITELIST_MIN = int(os.getenv("HH_WHITELIST_MIN", "300"))


def check_whitelist_fuse(count: int, *, min_count: int = WHITELIST_MIN,
                         read_failed: bool = False) -> str | None:
    """whitelist 熔断判定。返回 abort 原因字符串（应熔断）或 None（放行）。

    - read_failed=True：读取抛错（网络/DNS/rc≠0），即使 count 看似够也熔断（防部分读取）。
    - count < min_count：归零或过少，熔断。
    """
    if read_failed:
        return f"whitelist read failed (got {count}, need >= {min_count})"
    if count < min_count:
        return f"whitelist too few ({count} < {min_count})"
    return None


def check_arxiv_fuse(*, html_candidates: int, matched: int, network_error: bool,
                     arxiv_mode: str) -> tuple[str, str] | None:
    """arxiv 质量熔断判定。返回 (level, reason) 或 None（放行）。

    level: "block"（阻止自动发布）/ "degraded"（告警但不阻止发布）。
    仅 category 模式判定（author 模式无 html_candidates 口径）。
    - 双网络错误（network_error 且 matched==0）→ block；
    - html_candidates>0 且 matched==0 → degraded（当天有新论文但无白名单命中，不阻止）；
    - html_candidates==0（空窗口）或 matched>0 → 放行。
    """
    if arxiv_mode != "category":
        return None
    if network_error and matched == 0:
        return ("block", "arxiv network error and 0 matched papers")
    if html_candidates > 0 and matched == 0:
        return ("degraded", f"{html_candidates} candidates but 0 whitelist matches")
    return None


def should_mark_dedup(*, skip_bitable_write: bool, write_succeeded: bool) -> bool:
    """Task4: 仅当写库成功且非 skip 时才 mark dedup。

    - skip_bitable_write（replay/dry-run/test）→ 绝不 mark（防污染生产去重，6-02 根因）；
    - 写库失败 → 不 mark（retry-safe，下次重试不被去重吃掉）；
    - 写库成功 → mark（沿用「写后再 mark」语义）。
    """
    return write_succeeded and not skip_bitable_write


def run(
    window_days: int | None = None,
    since_dt: datetime | None = None,
    until_dt: datetime | None = None,
    limit_authors: int = 0,
    skip_llm: bool = False,
    skip_bitable_write: bool = False,
    skip_digest: bool = False,
    skip_arxiv: bool = False,
    skip_x: bool = False,
    skip_openalex: bool = False,
    skip_rss: bool = False,
    skip_metrics: bool = False,
    publish_to_feishu: bool = False,
    notify_user_id: str | None = None,
    digest_title_override: str | None = None,
    x_max_pages: int = 3,
    arxiv_mode: str = "author",  # "author" (default) or "category" (fast backfill)
    dedup_db_path: str | None = None,  # default: data/dedup.sqlite; main line uses dedup_main.sqlite
    rm_v4: str = "off",  # Researcher Mapping V4 mode: off / shadow / on (默认 off 为函数 caller 安全)
) -> dict:
    """Run one iteration of the daily pipeline.

    Returns a summary dict with counts and stats at each stage.
    """
    started_at = datetime.now(timezone.utc)
    summary: dict = {"started_at": started_at.isoformat()}
    errors_count = 0  # incremented on each failure path
    arxiv_blocked = False  # Task3: arxiv 熔断 block 时阻止自动发布
    error_notes: list[str] = []

    # Shared cost tracker across extractor and digest writer (so we get one row of LLM stats)
    cost_tracker = None
    if not skip_llm:
        from hh_research.extract.claude_client import CostTracker

        cost_tracker = CostTracker()

    # --- Step 0: preflight (Task6) — 发布模式下飞书/arxiv 不可达则 abort，不生成残缺日报 ---
    if publish_to_feishu:
        from hh_research.utils.preflight import preflight_check
        _down = preflight_check()
        if _down:
            log.error("preflight failed: %s unreachable — ABORT (no collect/generate/publish)", _down)
            summary["status"] = "aborted"
            summary["abort_reason"] = f"preflight: {_down} unreachable"
            summary["errors_count"] = errors_count + 1
            return summary

    # --- Step 1: whitelist (Task2: 读失败/过少 → 熔断 abort，不生成残缺日报) ---
    log.info("step 1: reading whitelist from Bitable")
    whitelist = []
    whitelist_read_failed = False
    _wl_attempts = int(os.getenv("HH_WHITELIST_READ_ATTEMPTS", "3"))
    for _i in range(_wl_attempts):
        try:
            whitelist = read_whitelist()
            whitelist_read_failed = False
            break
        except Exception as e:  # noqa: BLE001
            whitelist_read_failed = True
            last_attempt = _i + 1 >= _wl_attempts
            wait = 0 if last_attempt else min(5 * (2 ** _i), 30)
            log.error("whitelist read failed (attempt %d/%d): %s%s",
                      _i + 1, _wl_attempts, e,
                      "" if last_attempt else f" — retry in {wait}s")
            error_notes.append(f"whitelist_read attempt {_i+1}: {e}")
            if not last_attempt:
                time.sleep(wait)

    fuse_reason = check_whitelist_fuse(len(whitelist), read_failed=whitelist_read_failed)
    if fuse_reason:
        errors_count += 1
        log.error("whitelist fuse triggered: %s — ABORT (no collect/extract/publish/notify)",
                  fuse_reason)
        error_notes.append(f"whitelist_fuse: {fuse_reason}")
        summary["status"] = "aborted"
        summary["abort_reason"] = f"whitelist_fuse: {fuse_reason}"
        summary["whitelist_total"] = len(whitelist)
        summary["errors_count"] = errors_count
        summary["error_notes"] = error_notes
        return summary

    arxiv_pool = [e for e in whitelist if e.arxiv_author_query]
    x_pool = [e for e in whitelist if e.twitter_handle]
    log.info(
        "  whitelist: %d total, %d with arxiv_author_query, %d with x_handle",
        len(whitelist), len(arxiv_pool), len(x_pool),
    )
    if limit_authors > 0:
        arxiv_pool = arxiv_pool[:limit_authors]
        x_pool = x_pool[:limit_authors]
        log.info("  limited to first %d for this run", limit_authors)
    summary["whitelist_total"] = len(whitelist)
    summary["whitelist_with_arxiv_query"] = len(arxiv_pool)
    summary["whitelist_with_x_handle"] = len(x_pool)

    # ---- Time window resolution (priority: explicit since/until > window_days > smart) ----
    now = datetime.now(timezone.utc)
    if since_dt is not None and until_dt is not None:
        since, until = since_dt, until_dt
        log.info("window: explicit since=%s until=%s", since.isoformat(), until.isoformat())
    elif window_days is not None:
        since = now - timedelta(days=window_days)
        until = now
        log.info("window: explicit, %d days back → %s", window_days, since.isoformat())
    else:
        last_run = get_last_pipeline_run_at()
        if last_run is None:
            since = now - timedelta(days=2)
            log.info("window: first run, default 2 days back → %s", since.isoformat())
        else:
            since = last_run - timedelta(hours=2)
            gap_days = (now - since).total_seconds() / 86400
            log.info(
                "window: smart, last run %s, gap %.1f days → since %s",
                last_run.isoformat(), gap_days, since.isoformat(),
            )
        until = now
    summary["window_since"] = since.isoformat()
    summary["window_until"] = until.isoformat()

    # OpenAlex/RSS sources are author-organization filtered, RSS is feed-list filtered.
    # arxiv/x use the same whitelist.
    verified_pool = [e for e in whitelist if e.openalex_url]
    summary["whitelist_with_openalex"] = len(verified_pool)
    if limit_authors > 0:
        verified_pool = verified_pool[:limit_authors]

    raw_signals = []

    # --- Step 2a: arXiv collect ---
    if skip_arxiv:
        log.info("step 2a: arXiv collection skipped (--skip-arxiv)")
        summary["arxiv_fetched"] = 0
    else:
        log.info("step 2a: collecting from arXiv (window: %s -> %s)",
                 since.date(), until.date())
        try:
            arxiv_collector = ArxivCollector()
            # In "category" mode, use whole whitelist (not arxiv_pool) since
            # we filter by author name post-hoc rather than by author_query.
            if arxiv_mode == "category":
                log.info("  arxiv mode: category (fast backfill)")
                arxiv_signals = list(arxiv_collector.collect_by_window(whitelist, since, until))
            else:
                arxiv_signals = list(arxiv_collector.collect(arxiv_pool, since, until))
            log.info("  fetched %d arXiv papers", len(arxiv_signals))
            # Task3: arxiv 质量熔断判定（双网络错误→block；有候选无命中→degraded）
            _am = getattr(arxiv_collector, "last_window_metrics", {})
            _af = check_arxiv_fuse(
                html_candidates=_am.get("html_candidates", 0),
                matched=len(arxiv_signals),
                network_error=_am.get("network_error", False),
                arxiv_mode=arxiv_mode,
            )
            if _af:
                _level, _reason = _af
                summary["arxiv_fuse"] = f"{_level}: {_reason}"
                if _level == "block":
                    log.error("arxiv fuse [BLOCK]: %s — 阻止自动发布（人工确认后手动发）", _reason)
                    arxiv_blocked = True
                else:
                    log.warning("arxiv fuse [DEGRADED]: %s — 告警但继续", _reason)
            # Enrich each arXiv signal with paper figures from ar5iv
            from hh_research.extract.image_extractor import enrich_signal_with_images
            for s in arxiv_signals:
                try:
                    enrich_signal_with_images(s, max_images_per_paper=2)
                except Exception as e:  # noqa: BLE001
                    log.warning("image enrich failed for %s: %s", s.source_id, e)
            n_with_images = sum(1 for s in arxiv_signals if s.image_urls)
            log.info("  enriched %d/%d arXiv papers with images", n_with_images, len(arxiv_signals))
            summary["arxiv_fetched"] = len(arxiv_signals)
            summary["arxiv_with_images"] = n_with_images
            raw_signals.extend(arxiv_signals)
        except Exception as e:  # noqa: BLE001
            log.error("arxiv collection failed: %s", e)
            errors_count += 1
            error_notes.append(f"arxiv: {e}")
            summary["arxiv_fetched"] = 0

    # --- Step 2b: X collect (socialdata.tools) ---
    if skip_x:
        log.info("step 2b: X collection skipped (--skip-x)")
        summary["x_fetched"] = 0
    else:
        log.info("step 2b: collecting from X via socialdata.tools")
        try:
            x_collector = SocialDataXCollector(
                exclude_retweets=True, exclude_replies=False,
                max_pages_per_user=x_max_pages,
            )
            x_signals = list(x_collector.collect(x_pool, since, until))
            x_collector.close()
            log.info("  fetched %d X tweets", len(x_signals))
            summary["x_fetched"] = len(x_signals)
            raw_signals.extend(x_signals)
        except RuntimeError as e:
            log.warning("X collection skipped: %s", e)
            summary["x_status"] = "skipped_missing_key"
            summary["x_fetched"] = 0
        except Exception as e:  # noqa: BLE001
            log.error("x collection failed: %s", e)
            errors_count += 1
            error_notes.append(f"x: {e}")
            summary["x_fetched"] = 0

    # --- Step 2c: OpenAlex collect (verified persons only — non-arXiv venues) ---
    if skip_openalex:
        log.info("step 2c: OpenAlex collection skipped (--skip-openalex)")
        summary["openalex_fetched"] = 0
    else:
        log.info("step 2c: collecting from OpenAlex (%d verified authors)", len(verified_pool))
        try:
            oa = OpenAlexCollector()
            oa_signals = list(oa.collect(verified_pool, since, until))
            oa.close()
            log.info("  fetched %d OpenAlex works", len(oa_signals))
            summary["openalex_fetched"] = len(oa_signals)
            raw_signals.extend(oa_signals)
        except Exception as e:  # noqa: BLE001
            log.error("openalex collection failed: %s", e)
            errors_count += 1
            error_notes.append(f"openalex: {e}")
            summary["openalex_fetched"] = 0

    # --- Step 2d: RSS collect (company / lab official channels) ---
    if skip_rss:
        log.info("step 2d: RSS collection skipped (--skip-rss)")
        summary["rss_fetched"] = 0
    else:
        log.info("step 2d: collecting from RSS feeds")
        try:
            rss = RssCollector()
            rss_signals = list(rss.collect(whitelist, since, until))
            rss.close()
            log.info("  fetched %d RSS posts", len(rss_signals))
            summary["rss_fetched"] = len(rss_signals)
            raw_signals.extend(rss_signals)
        except Exception as e:  # noqa: BLE001
            log.error("rss collection failed: %s", e)
            errors_count += 1
            error_notes.append(f"rss: {e}")
            summary["rss_fetched"] = 0

    log.info("  total raw signals: %d", len(raw_signals))
    summary["raw_fetched"] = len(raw_signals)

    # --- Step 3: dedup ---
    log.info("step 3: dedup against SQLite seen-set (db=%s)", dedup_db_path or "default")
    dedup = SQLiteDedupStore(db_path=dedup_db_path)
    unseen_ids = set(dedup.filter_unseen([s.source_id for s in raw_signals]))
    new_signals = [s for s in raw_signals if s.source_id in unseen_ids]
    log.info("  %d new (skipped %d already-seen)", len(new_signals), len(raw_signals) - len(new_signals))
    summary["new_signals"] = len(new_signals)

    if new_signals:
        # --- Step 4: LLM extract ---
        if skip_llm:
            log.info("step 4: skipped (--skip-llm)")
        else:
            log.info("step 4: running Claude signal extractor")
            try:
                from hh_research.extract.signal_extractor import SignalExtractor

                extractor = SignalExtractor(cost=cost_tracker)
                new_signals = extractor.extract_many(new_signals)
            except RuntimeError as e:
                log.warning("LLM extract skipped: %s", e)
                summary["llm_status"] = "skipped_missing_key"
            except Exception as e:  # noqa: BLE001
                log.error("LLM extract failed: %s", e)
                errors_count += 1
                error_notes.append(f"llm_extract: {e}")
                summary["llm_status"] = f"error: {e}"

        # --- Step 5: write signals to Bitable ---
        write_succeeded = False
        if skip_bitable_write:
            log.info("step 5: skipped (--skip-bitable-write) — 不写库也不 mark dedup")
        else:
            log.info("step 5: writing %d signals to Bitable", len(new_signals))
            try:
                rows = [signal_to_row(s) for s in new_signals]
                result = batch_create_signals(rows)
                log.info("  inserted %d, errors: %d", result["inserted"], len(result["errors"]))
                summary["bitable_inserted"] = result["inserted"]
                summary["bitable_errors"] = len(result["errors"])
                if result["errors"]:
                    for err_detail in result["errors"][:3]:
                        log.error("  bitable error: %s", err_detail)
                    errors_count += len(result["errors"])
                    error_notes.append(f"bitable_write: {result['errors'][0][:200]}")
                write_succeeded = True
            except Exception as e:  # noqa: BLE001
                log.error("bitable write failed: %s", e)
                errors_count += 1
                error_notes.append(f"bitable_write: {e}")

        # Task4: dedup mark 绑定写库成功。skip_bitable_write(replay/dry-run/test) 绝不 mark
        # （防污染生产去重——6-02 frontier=0 根因）；写库失败也不 mark（retry-safe）。
        # 5-29 note: dedup 在写库阶段后 mark；进程被 kill 则下次重新提取（重付 LLM 成本但不丢数据）。
        if should_mark_dedup(skip_bitable_write=skip_bitable_write, write_succeeded=write_succeeded):
            dedup.mark_many([s.source_id for s in new_signals])
            log.info("  marked %d source_ids as seen", len(new_signals))
        else:
            log.info("  dedup mark skipped (skip_bitable_write=%s, write_succeeded=%s)",
                     skip_bitable_write, write_succeeded)

        # --- Step 5.5: author enrich ---
        if not (skip_digest or skip_llm):
            try:
                rm_v4_mode = rm_v4
                arxiv_signals_for_enrich = [
                    s for s in new_signals
                    if s.source == "arxiv" and s.author_record_id
                ]
                if not arxiv_signals_for_enrich:
                    pass
                elif rm_v4_mode == "off":
                    # 旧 V3.2 路径（保持不变）
                    from hh_research.extract.author_enricher import (  # noqa: PLC0415
                        enrich_paper_coauthors, get_arxiv_full_authors,
                    )
                    log.info("step 5.5 (V3.2): enriching coauthors for %d whitelisted arxiv papers",
                             len(arxiv_signals_for_enrich))
                    wl_by_name = {e.name: e for e in whitelist if e.name}
                    for sig in arxiv_signals_for_enrich:
                        arxiv_id = sig.source_id.removeprefix("arxiv:").split("v")[0]
                        try:
                            full_authors = get_arxiv_full_authors(arxiv_id)
                            if not full_authors:
                                continue
                            wl_match = {n: wl_by_name[n] for n in full_authors if n in wl_by_name}
                            sig.coauthors = enrich_paper_coauthors(
                                arxiv_id=arxiv_id, authors=full_authors,
                                whitelist_match=wl_match,
                                max_authors=6, parallel_workers=4,
                            )
                            log.info("  · %s → %d coauthors (%d whitelist)",
                                     arxiv_id, len(sig.coauthors),
                                     sum(1 for c in sig.coauthors if c.is_whitelist))
                        except Exception as e:  # noqa: BLE001
                            log.warning("enrich failed for %s: %s", arxiv_id, e)
                else:
                    # V4 路径（shadow 或 on）
                    from hh_research.extract.researcher_mapping import (  # noqa: PLC0415
                        enrich_paper_coauthors_v4,
                    )
                    from hh_research.extract.author_enricher import (  # noqa: PLC0415
                        get_arxiv_full_authors,
                    )
                    log.info("step 5.5 (V4 mode=%s): enriching %d papers",
                             rm_v4_mode, len(arxiv_signals_for_enrich))
                    wl_by_name = {e.name: e for e in whitelist if e.name}
                    shadow_dir = Path("data/state/rm_v4_shadow")
                    if rm_v4_mode == "shadow":
                        shadow_dir.mkdir(parents=True, exist_ok=True)
                    shadow_records: list[dict] = []

                    for sig in arxiv_signals_for_enrich:
                        arxiv_id = sig.source_id.removeprefix("arxiv:").split("v")[0]
                        try:
                            full_authors = get_arxiv_full_authors(arxiv_id)
                            if not full_authors:
                                continue
                            wl_match = {n: wl_by_name[n] for n in full_authors if n in wl_by_name}
                            v4_coauthors = enrich_paper_coauthors_v4(
                                arxiv_id=arxiv_id, authors=full_authors,
                                whitelist_match=wl_match,
                                parallel_workers=4,
                            )
                            if rm_v4_mode == "on":
                                sig.coauthors = v4_coauthors
                            else:  # shadow：旧路径填 Signal.coauthors，新路径仅落盘
                                from hh_research.extract.author_enricher import enrich_paper_coauthors  # noqa: PLC0415
                                sig.coauthors = enrich_paper_coauthors(
                                    arxiv_id=arxiv_id, authors=full_authors,
                                    whitelist_match=wl_match,
                                    max_authors=6, parallel_workers=4,
                                )
                                shadow_records.append({
                                    "arxiv_id": arxiv_id,
                                    "v3_2": [c.model_dump() for c in sig.coauthors],
                                    "v4": [c.model_dump() for c in v4_coauthors],
                                })
                            log.info("  · %s V4 → %d coauthors (verified fields: %d)",
                                     arxiv_id, len(v4_coauthors),
                                     sum(sum(1 for v in c.verification.values() if v == "verified")
                                         for c in v4_coauthors))
                        except Exception as e:  # noqa: BLE001
                            log.warning("V4 enrich failed for %s: %s", arxiv_id, e)

                    if rm_v4_mode == "shadow" and shadow_records:
                        date_str = (until_dt if until_dt else now).strftime("%Y-%m-%d")
                        shadow_file = shadow_dir / f"{date_str}.json"
                        shadow_file.write_text(
                            json.dumps(shadow_records, ensure_ascii=False, indent=2)
                        )
                        log.info("rm_v4 shadow: wrote %d records to %s",
                                 len(shadow_records), shadow_file)
            except Exception as e:  # noqa: BLE001
                log.warning("step 5.5 author enrich failed: %s", e)

        # --- Step 6: daily digest ---
        if skip_digest or skip_llm:
            log.info("step 6: skipped (requires LLM)")
        else:
            log.info("step 6: generating daily digest")
            try:
                from hh_research.extract.daily_writer import DailyWriter

                writer = DailyWriter(cost=cost_tracker)
                # For backfill, use the target date as digest_date
                digest_date_for_writer = until_dt if until_dt is not None else now
                # 6-09: 白名单 tier 加权头条（record_id→tier；None tier 跳过）
                tier_lookup = {e.record_id: e.tier for e in whitelist if e.tier}
                digest = writer.write(digest_date_for_writer, new_signals, tier_lookup=tier_lookup)
                log.info("  digest generated: %d chars", len(digest.markdown))
                summary["digest_chars"] = len(digest.markdown)
                summary["digest_markdown_preview"] = digest.markdown[:500]

                # Save full markdown locally
                digests_dir = Path(__file__).parent.parent.parent.parent / "data" / "digests"
                digests_dir.mkdir(parents=True, exist_ok=True)
                # Name file by digest target date
                file_date_tag = digest_date_for_writer.strftime("%Y-%m-%d")
                digest_path = digests_dir / f"digest_{file_date_tag}.md"
                digest_path.write_text(digest.markdown, encoding="utf-8")
                log.info("  saved digest to %s", digest_path)
                summary["digest_local_path"] = str(digest_path)

                # Optional: publish to Feishu wiki
                if publish_to_feishu and arxiv_blocked:
                    log.error("  publish SKIPPED by arxiv fuse: %s — 人工确认后手动发布",
                              summary.get("arxiv_fuse", "?"))
                    summary["publish_skipped"] = "arxiv_fuse_block"
                elif publish_to_feishu:
                    try:
                        from hh_research.publish.lark_doc_publisher import (  # noqa: PLC0415
                            insert_signal_images, notify_digest_ready, publish_digest,
                        )

                        title = digest_title_override or (
                            f"HH Research Daily {file_date_tag}"
                        )
                        log.info("  publishing to Feishu: %s", title)
                        result = publish_digest(title=title, markdown=digest.markdown)
                        summary["digest_feishu_url"] = result["url"]
                        summary["digest_obj_token"] = result["obj_token"]
                        summary["digest_node_token"] = result.get("node_token", "")
                        log.info("  feishu url: %s", result["url"])

                        # Insert paper images via media-insert API (more reliable
                        # than letting Feishu fetch remote ![](url) — which often
                        # fails on hotlinked or CDN-protected images).
                        try:
                            img_counts = insert_signal_images(
                                obj_token=result["obj_token"],
                                signals=new_signals,
                                max_per_signal=1,
                            )
                            log.info("  image insertion: %s", img_counts)
                            summary["images_inserted"] = img_counts.get("inserted", 0)
                            summary["images_failed"] = img_counts.get("failed", 0)
                        except Exception as e:  # noqa: BLE001
                            log.warning("image insertion step failed: %s", e)

                        # V3.2 锚点注入：传 wiki_node_token → URL 用真 anchor_id (`#share-...`)
                        # 失败时 graceful degrade，不影响主流程。
                        try:
                            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
                            from publish_with_anchors import inject_anchors_inplace  # noqa: E402
                            anchor_r = inject_anchors_inplace(
                                result["obj_token"],
                                wiki_node_token=result.get("node_token"),
                            )
                            summary["anchors_resolved"] = len(anchor_r.get("anchor_map", {}))
                            summary["markers_deleted"] = anchor_r.get("markers_deleted", 0)
                            log.info("  anchor injection: %d resolved, %d markers deleted",
                                     summary["anchors_resolved"], summary["markers_deleted"])
                        except Exception as e:  # noqa: BLE001
                            log.warning("anchor injection step failed: %s", e)

                        # V3.2: 不再调 author_lookup_post_process — RM 表已在 daily_writer 阶段
                        # 由 LLM 用 Signal.coauthors 数据直接渲染（step 5.5 enrich 后）。
                        # 旧 author_lookup_post_process.py 保留作 fallback，不在主流程调。

                        # Count headlines for the notification
                        headline_n = sum(
                            1 for s in new_signals if getattr(s, "is_headline_candidate", False)
                        )
                        if notify_user_id:
                            ok = notify_digest_ready(
                                user_open_id=notify_user_id,
                                title=title,
                                doc_url=result["url"],
                                signal_count=len(new_signals),
                                headline_count=headline_n,
                            )
                            summary["notify_sent"] = ok
                    except Exception as e:  # noqa: BLE001
                        log.error("publish_to_feishu failed: %s", e)
                        errors_count += 1
                        error_notes.append(f"publish: {e}")
                        summary["digest_feishu_url"] = None
            except Exception as e:  # noqa: BLE001
                log.error("digest generation failed: %s", e)
                errors_count += 1
                error_notes.append(f"digest: {e}")
                summary["digest_status"] = f"error: {e}"
    else:
        log.info("no new signals; skipping LLM/write/digest steps")

    # Roll up LLM stats from the shared cost_tracker
    if cost_tracker:
        summary["llm_calls"] = cost_tracker.calls
        summary["llm_input_tokens"] = cost_tracker.input_tokens
        summary["llm_cache_read_tokens"] = cost_tracker.cache_read_tokens
        summary["llm_cache_write_tokens"] = cost_tracker.cache_write_tokens
        summary["llm_output_tokens"] = cost_tracker.output_tokens
        summary["llm_cost_usd"] = round(cost_tracker.usd, 6)

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()
    summary["finished_at"] = finished_at.isoformat()
    summary["duration_seconds"] = round(duration, 1)
    summary["errors_count"] = errors_count
    summary["status"] = "ok" if errors_count == 0 else "completed_with_errors"

    # --- Step 7: write run metrics to Bitable ---
    if skip_metrics:
        log.info("step 7: ops_metrics write skipped (--skip-metrics)")
    else:
        log.info("step 7: writing run metrics to Bitable ops_metrics")
        try:
            metric_row = _build_metric_row(summary, started_at, error_notes)
            result = write_ops_metric(metric_row)
            if result["errors"]:
                log.warning("  ops_metrics write errors: %s", result["errors"])
            else:
                log.info("  ops_metrics row written successfully")
        except Exception as e:  # noqa: BLE001
            log.error("ops_metrics write failed (non-fatal): %s", e)

    return summary


def _build_metric_row(summary: dict, started_at: datetime, error_notes: list[str]) -> dict:
    """Convert pipeline summary → ops_metrics row dict."""
    # Total LLM input = fresh + cache read + cache write (everything that hit the model)
    llm_input_total = (
        summary.get("llm_input_tokens", 0)
        + summary.get("llm_cache_read_tokens", 0)
        + summary.get("llm_cache_write_tokens", 0)
    )
    notes_parts = [f"status={summary.get('status', 'unknown')}"]
    if error_notes:
        notes_parts.append("errors=" + " | ".join(error_notes[:3]))  # cap at 3 to fit
    notes_parts.append(
        f"new_signals={summary.get('new_signals', 0)}"
        f" raw_fetched={summary.get('raw_fetched', 0)}"
    )
    return {
        "metric_date": started_at.strftime("%Y-%m-%d %H:%M:%S"),
        "x_tweets_fetched": summary.get("x_fetched", 0),
        "arxiv_papers_fetched": summary.get("arxiv_fetched", 0),
        "llm_calls": summary.get("llm_calls", 0),
        "llm_tokens_in": llm_input_total,
        "llm_tokens_out": summary.get("llm_output_tokens", 0),
        "llm_cost_usd": summary.get("llm_cost_usd", 0.0),
        "pipeline_duration_seconds": summary.get("duration_seconds", 0.0),
        "errors_count": summary.get("errors_count", 0),
        "notes": " | ".join(notes_parts)[:500],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="HH Research daily pipeline")
    ap.add_argument("--days", type=int, default=None,
                    help="explicit window in days; if omitted, derive from last ops_metrics row")
    ap.add_argument("--for-date", type=str, default=None,
                    help="backfill: generate digest for this UTC date (YYYY-MM-DD); window = that day only")
    ap.add_argument("--since", type=str, default=None,
                    help="explicit window start (ISO 8601 UTC, e.g. 2026-05-21T00:30:00Z); "
                         "use with --until; overrides --for-date / --days")
    ap.add_argument("--until", type=str, default=None,
                    help="explicit window end (ISO 8601 UTC); use with --since")
    ap.add_argument("--dedup-db", type=str, default=None,
                    help="path to SQLite dedup db; default ./data/dedup.sqlite. "
                         "Main line uses ./data/dedup_main.sqlite to isolate from legacy 00:00 line")
    ap.add_argument("--title-override", type=str, default=None,
                    help="override digest title (e.g. 'HH Research Daily · 2026-05-22 · 主线')")
    ap.add_argument("--limit-authors", type=int, default=0, help="limit to first N authors (testing)")
    ap.add_argument("--skip-llm", action="store_true", help="skip Claude extractor + digest")
    ap.add_argument("--skip-bitable-write", action="store_true", help="dry-run: don't write to Bitable")
    ap.add_argument("--skip-digest", action="store_true", help="skip daily digest generation")
    ap.add_argument("--skip-arxiv", action="store_true", help="skip arXiv collector")
    ap.add_argument("--skip-x", action="store_true", help="skip X collector")
    ap.add_argument("--skip-openalex", action="store_true", help="skip OpenAlex collector")
    ap.add_argument("--skip-rss", action="store_true", help="skip RSS collector")
    ap.add_argument("--skip-metrics", action="store_true", help="skip ops_metrics row write")
    ap.add_argument("--publish", action="store_true", help="publish digest to Feishu wiki")
    ap.add_argument("--notify-user", type=str, default=None, help="Feishu open_id to notify")
    ap.add_argument("--x-max-pages", type=int, default=3,
                    help="max pagination pages per X user (bump for backfill of older dates)")
    ap.add_argument("--arxiv-mode", type=str, default="author", choices=["author", "category"],
                    help="arxiv collection mode: 'author' (per-author query, slow) or "
                         "'category' (per-category window query, fast for backfill)")
    ap.add_argument(
        "--rm-v4", type=str, default="on", choices=["off", "shadow", "on"],
        help="Researcher Mapping V4 路径开关：on=V4 双源+审查 agent（默认，自 5.21）；"
             "shadow=双跑只用旧值；off=旧 V3.2 单源",
    )
    args = ap.parse_args()

    since_dt = until_dt = None
    title_override = None

    # Priority: --since/--until > --for-date > --days > smart default
    if args.since and args.until:
        since_dt = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
        until_dt = datetime.fromisoformat(args.until.replace("Z", "+00:00"))
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)
        if until_dt.tzinfo is None:
            until_dt = until_dt.replace(tzinfo=timezone.utc)
    elif args.for_date:
        target = datetime.strptime(args.for_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        since_dt = target
        until_dt = target + timedelta(days=1)
        title_override = f"HH Research Daily {args.for_date}"

    if args.title_override:
        title_override = args.title_override  # explicit override wins

    summary = run(
        window_days=args.days,
        since_dt=since_dt,
        until_dt=until_dt,
        limit_authors=args.limit_authors,
        skip_llm=args.skip_llm,
        skip_bitable_write=args.skip_bitable_write,
        skip_digest=args.skip_digest,
        skip_arxiv=args.skip_arxiv,
        skip_x=args.skip_x,
        skip_openalex=args.skip_openalex,
        skip_rss=args.skip_rss,
        skip_metrics=args.skip_metrics,
        publish_to_feishu=args.publish,
        notify_user_id=args.notify_user,
        digest_title_override=title_override,
        x_max_pages=args.x_max_pages,
        arxiv_mode=args.arxiv_mode,
        dedup_db_path=args.dedup_db,
        rm_v4=args.rm_v4,
    )

    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
