"""Thin Feishu Bitable client.

MVP strategy: shell out to `lark-cli --profile personal` for reads and writes.
Reason: lark-cli handles user OAuth token refresh transparently, and we already
set it up. Later we can swap to `lark-oapi` Python SDK for in-process perf.

This module exposes narrow, typed methods — not a generic wrapper.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from ..utils.logger import get_logger
from .schemas import WhitelistEntry

log = get_logger("bitable_client")

# Task6: 只读命令失败时可安全重试（幂等）；写命令不重试以免重复写入。
_READ_CMDS = {"+record-list", "+field-list", "+field-get", "+field-search-options", "+record-search"}


class LarkCLIError(RuntimeError):
    pass


def _lark_cli(*args: str, profile: str = "personal", timeout: int = 60) -> dict[str, Any]:
    """Run lark-cli with --profile and return parsed JSON response.

    lark-cli 1.0.22+ 的 base +record-list 默认输出 markdown（help 说 default json
    但实际不然）→ 必须显式 `--format json`，否则 JSON 解析失败。
    record-batch-create 不支持 `--format`，但默认返回 JSON。
    """
    extra = list(args)
    command = extra[1] if len(extra) > 1 else ""
    if command != "+record-batch-create" and "--format" not in extra:
        extra.extend(["--format", "json"])
    cmd = ["lark-cli", "--profile", profile, *extra]
    # 5.23: LARK_CLI_NO_PROXY=1 to bypass local proxies (Clash, etc.).
    # Without this, /open-apis Bitable calls go through HTTPS_PROXY and may TLS-timeout
    # on long-paginated reads (offset=1000 in regenerate_digest).
    env = {**os.environ, "LARK_CLI_NO_PROXY": "1"}

    # Task6: 只读命令退避重试，受总超时预算约束（HH_LARK_TOTAL_BUDGET_S，默认 120s）+ attempt 日志。
    is_read = command in _READ_CMDS
    attempts = int(os.getenv("HH_LARK_READ_ATTEMPTS", "5")) if is_read else 1
    budget = float(os.getenv("HH_LARK_TOTAL_BUDGET_S", "120"))
    start = time.monotonic()
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, check=False, env=env,
            )
            if result.returncode != 0:
                raise LarkCLIError(
                    f"lark-cli failed ({' '.join(cmd)}): rc={result.returncode} stderr={result.stderr[:500]}"
                )
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise LarkCLIError(f"lark-cli returned non-JSON: {result.stdout[:300]}") from e
        except (LarkCLIError, subprocess.TimeoutExpired) as e:
            last_err = e
            if not is_read or i + 1 >= attempts:
                break
            elapsed = time.monotonic() - start
            wait = min(3 * (2 ** i), 30)
            if elapsed + wait > budget:
                log.warning("lark-cli %s total budget %.0fs reached (elapsed %.0fs) — giving up",
                            command, budget, elapsed)
                break
            log.warning("lark-cli %s attempt %d/%d failed (%s); wait %ds (elapsed %.0fs/%.0fs budget)",
                        command, i + 1, attempts, str(e)[:80], wait, elapsed, budget)
            time.sleep(wait)
    raise last_err if last_err is not None else LarkCLIError("lark-cli unknown failure")


def _unwrap_select_single(val: Any) -> str | None:
    """Bitable returns single-select as ['x']. Unwrap to 'x' or None."""
    if val is None:
        return None
    if isinstance(val, list):
        return val[0] if val else None
    return str(val)


def _unwrap_select_multi(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    return [str(val)]


def read_whitelist(app_token: str | None = None, table_id: str | None = None) -> list[WhitelistEntry]:
    """Read all whitelist records from the pipeline Bitable.

    Paginates through all pages. Returns typed WhitelistEntry list.
    """
    app_token = app_token or os.environ["HH_BITABLE_APP_TOKEN"]
    table_id = table_id or os.environ["HH_WHITELIST_TABLE_ID"]

    entries: list[WhitelistEntry] = []
    offset = 0
    page_size = 200
    while True:
        resp = _lark_cli(
            "base",
            "+record-list",
            "--base-token",
            app_token,
            "--table-id",
            table_id,
            "--limit",
            str(page_size),
            "--offset",
            str(offset),
        )
        data = resp.get("data", {})
        fields = data.get("fields", [])  # field name order
        rows = data.get("data", [])  # list of row arrays
        record_ids = data.get("record_id_list", [])

        name_to_idx = {name: i for i, name in enumerate(fields)}

        for rid, row in zip(record_ids, rows):
            def get(name: str) -> Any:
                idx = name_to_idx.get(name)
                return row[idx] if idx is not None else None

            entries.append(
                WhitelistEntry(
                    record_id=rid,
                    name=get("名字") or "",
                    twitter_url=get("Twitter"),
                    organization=_unwrap_select_single(get("组织")),
                    category=_unwrap_select_single(get("业界/学界/其他")),
                    tier=_unwrap_select_single(get("tier")),
                    entity_type=_unwrap_select_single(get("entity_type")),
                    source_authority=_unwrap_select_single(get("source_authority")),
                    research_tags=_unwrap_select_multi(get("研究方向")),
                    active_levels=_unwrap_select_multi(get("活跃情况")),
                    bio=get("简介"),
                    notes=get("备注"),
                    arxiv_author_query=get("arxiv_author_query"),
                    orcid=get("orcid"),
                    affiliation_regex=get("affiliation_regex"),
                    # last_tweet_at parsing: bitable returns epoch millis or ISO string
                    last_tweet_at=None,  # TODO: parse when we start writing it
                    avg_interval_days=get("avg_interval_days"),
                    # Enriched URLs
                    personal_url=get("personal_url"),
                    scholar_url=get("scholar_url"),
                    github_url=get("github_url"),
                    arxiv_homepage_url=get("arxiv_homepage_url"),
                    openalex_url=get("openalex_url"),
                )
            )

        if not data.get("has_more"):
            break
        offset += page_size

    return entries


def _build_whitelist_name_index(
    app_token: str | None = None, table_id: str | None = None
) -> dict[str, str]:
    """Build {normalized_name: record_id} index from the 信号源 (whitelist) table.

    Each whitelist row yields up to 3 variants for matching robustness:
      - full 名字 string
      - English part (before any parens), e.g. "Pengcheng Yin(殷鹏程)" -> "Pengcheng Yin"
      - Chinese part (inside parens), e.g. "Pengcheng Yin(殷鹏程)" -> "殷鹏程"
    """
    import re

    app_token = app_token or os.environ["HH_BITABLE_APP_TOKEN"]
    table_id = table_id or os.environ["HH_WHITELIST_TABLE_ID"]

    def norm(s: str) -> str:
        return re.sub(r"[^\w一-鿿]+", "", s.lower()).strip()

    idx: dict[str, str] = {}
    offset = 0
    while True:
        # lark-cli 1.0.22+ 不再接受 `--field-id 名字`（regression），改不传 field filter，
        # 拿全字段后本地按名字列取
        resp = _lark_cli(
            "base", "+record-list",
            "--base-token", app_token,
            "--table-id", table_id,
            "--limit", "200",
            "--offset", str(offset),
        )
        if not resp.get("ok"):
            break
        data = resp.get("data", {})
        fld_names = data.get("fields") or []
        if "名字" not in fld_names:
            break
        ni = fld_names.index("名字")
        for rid, row in zip(data.get("record_id_list", []), data.get("data", [])):
            raw = row[ni] if ni < len(row) else None
            if not raw:
                continue
            n = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", str(raw))
            variants = {n}
            base = re.sub(r"[\(（].+?[\)）]", "", n).strip()
            if base:
                variants.add(base)
            for m in re.finditer(r"[\(（]([^\)）]+)[\)）]", n):
                variants.add(m.group(1).strip())
            for v in variants:
                k = norm(v)
                if k and k not in idx:
                    idx[k] = rid
        if not data.get("has_more"):
            break
        offset += 200
    return idx


def _resolve_authors_to_record_ids(
    signal_rows: list[dict], whitelist_index: dict[str, str]
) -> None:
    """For each signal row, parse extract_json.entities.people and resolve to whitelist
    record IDs. Mutates rows in-place by adding a `作者` key with [{"id": rid}, ...].
    """
    import json as _json
    import re

    def norm(s: str) -> str:
        return re.sub(r"[^\w一-鿿]+", "", s.lower()).strip()

    for sig in signal_rows:
        ex = sig.get("extract_json")
        if not ex:
            continue
        try:
            d = _json.loads(ex) if isinstance(ex, str) else ex
        except Exception:
            continue
        ents = (d or {}).get("entities") or {}
        ppl = ents.get("people") or []
        if not ppl:
            continue
        ids = []
        seen = set()
        for a in ppl:
            k = norm(str(a))
            rid = whitelist_index.get(k)
            if rid and rid not in seen:
                ids.append({"id": rid})
                seen.add(rid)
        if ids:
            sig["authors_link"] = ids


def batch_create_signals(
    signal_rows: list[dict],
    app_token: str | None = None,
    table_id: str | None = None,
    batch_size: int = 100,
    auto_link_authors: bool = True,
    whitelist_index: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Insert a batch of signal records. `signal_rows` is a list of dicts keyed by Bitable field name.

    If `auto_link_authors` is True (default), automatically resolves
    `extract_json.entities.people` to whitelist (信号源) record IDs and writes
    them into the 信号.作者 bidirectional link field. This makes 信号源.关联信号
    + 信号源.论文链接 lookup populate automatically.

    Pass a pre-built `whitelist_index` to reuse across multiple calls (avoid
    refetching). If None and auto_link_authors=True, fetches once at start.

    Uses a relative path for --json (lark-cli requirement).
    Returns a summary dict with counts.
    """
    app_token = app_token or os.environ["HH_BITABLE_APP_TOKEN"]
    table_id = table_id or os.environ["HH_SIGNALS_TABLE_ID"]

    # Author link resolution (mutates signal_rows in place, adds 'authors_link' key)
    if auto_link_authors:
        if whitelist_index is None:
            whitelist_index = _build_whitelist_name_index(app_token=app_token)
        _resolve_authors_to_record_ids(signal_rows, whitelist_index)

    # internal_key (used in signal_to_row dict) → Chinese Bitable field name
    # When the user renames Bitable fields, only this map needs updating.
    SIGNAL_FIELD_MAP = [
        ("source_id",          "来源ID"),
        ("source",             "来源"),
        ("url",                "链接"),
        ("raw_text",           "原文"),
        ("lang",               "语言"),
        ("created_at",         "发布时间"),
        ("fetched_at",         "抓取时间"),
        ("summary_zh",         "中文摘要"),
        ("novelty_score",      "新颖性"),
        ("category",           "主赛道"),
        ("subcategory",        "子赛道"),
        ("key_terms",          "关键词"),
        ("in_daily_digest",    "入日报"),
        ("needs_human_review", "待审核"),
        ("extract_json",       "提取JSON"),
        ("authors_link",       "作者"),       # bidirectional link to 信号源
    ]
    internal_keys = [k for k, _ in SIGNAL_FIELD_MAP]
    fields = [zh for _, zh in SIGNAL_FIELD_MAP]

    total_inserted = 0
    errors: list[str] = []

    # Ensure we have a relative path to ./data (lark-cli requirement)
    rel_tmp = "./data/_tmp_batch_signals.json"
    tmp_path = Path(rel_tmp)
    tmp_path.parent.mkdir(parents=True, exist_ok=True)

    # Chunk into batches for rate-limit safety
    for i in range(0, len(signal_rows), batch_size):
        chunk = signal_rows[i : i + batch_size]
        # Build rows by looking up internal English keys but emitting under Chinese field headers
        rows = [[sig.get(k) for k in internal_keys] for sig in chunk]
        payload = {"fields": fields, "rows": rows}
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False))
        try:
            resp = _lark_cli(
                "base",
                "+record-batch-create",
                "--base-token",
                app_token,
                "--table-id",
                table_id,
                "--json",
                f"@{rel_tmp}",
            )
            if resp.get("ok"):
                total_inserted += len(resp.get("data", {}).get("record_id_list", []))
            else:
                err = resp.get("error", {})
                # Surface the API's hint + value path (most useful for debugging)
                detail = err.get("detail", {}) if isinstance(err, dict) else {}
                errors.append(json.dumps({
                    "code": err.get("code") if isinstance(err, dict) else None,
                    "message": err.get("message") if isinstance(err, dict) else str(err),
                    "hint": detail.get("hint"),
                    "path": detail.get("path"),
                    "value": detail.get("value"),
                }, ensure_ascii=False))
        except LarkCLIError as e:
            errors.append(str(e))

    try:
        tmp_path.unlink()
    except FileNotFoundError:
        pass

    return {"inserted": total_inserted, "errors": errors}


def write_ops_metric(
    metric: dict[str, Any],
    app_token: str | None = None,
    table_id: str | None = None,
) -> dict[str, Any]:
    """Write one row to the ops_metrics table.

    `metric` is a dict keyed by Bitable field name. Missing fields are sent as null.
    Returns {"inserted": int, "errors": [str]}.
    """
    app_token = app_token or os.environ["HH_BITABLE_APP_TOKEN"]
    table_id = table_id or os.environ["HH_OPS_METRICS_TABLE_ID"]

    OPS_METRIC_FIELD_MAP = [
        ("metric_date",                 "日期"),
        ("x_tweets_fetched",            "X推文数"),
        ("arxiv_papers_fetched",        "arXiv论文数"),
        ("llm_calls",                   "LLM调用数"),
        ("llm_tokens_in",               "输入Token"),
        ("llm_tokens_out",              "输出Token"),
        ("llm_cost_usd",                "成本USD"),
        ("pipeline_duration_seconds",   "运行时长秒"),
        ("errors_count",                "错误数"),
        ("notes",                       "备注"),
    ]
    internal_keys = [k for k, _ in OPS_METRIC_FIELD_MAP]
    fields = [zh for _, zh in OPS_METRIC_FIELD_MAP]
    payload = {"fields": fields, "rows": [[metric.get(k) for k in internal_keys]]}

    rel_tmp = "./data/_tmp_ops_metric.json"
    tmp_path = Path(rel_tmp)
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False))

    try:
        resp = _lark_cli(
            "base",
            "+record-batch-create",
            "--base-token",
            app_token,
            "--table-id",
            table_id,
            "--json",
            f"@{rel_tmp}",
        )
        if resp.get("ok"):
            inserted = len(resp.get("data", {}).get("record_id_list", []))
            return {"inserted": inserted, "errors": []}
        return {"inserted": 0, "errors": [str(resp.get("error", "unknown"))]}
    except LarkCLIError as e:
        return {"inserted": 0, "errors": [str(e)]}
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def get_last_pipeline_run_at(
    app_token: str | None = None,
    table_id: str | None = None,
) -> "datetime | None":
    """Read the most recent metric_date from ops_metrics. Returns None if no rows yet.

    Used by pipeline/daily.py for smart-window mode: we collect from this
    timestamp forward, naturally covering weekends / holidays.
    """
    from datetime import datetime, timezone  # noqa: PLC0415

    app_token = app_token or os.environ["HH_BITABLE_APP_TOKEN"]
    table_id = table_id or os.environ["HH_OPS_METRICS_TABLE_ID"]

    try:
        resp = _lark_cli(
            "base", "+record-list",
            "--base-token", app_token,
            "--table-id", table_id,
            "--limit", "200",
        )
    except LarkCLIError:
        return None

    data = resp.get("data", {})
    fields = data.get("fields", [])
    rows = data.get("data", [])
    if not rows:
        return None

    # Chinese rename of metric_date field (was "metric_date", now "日期")
    metric_date_field = "日期" if "日期" in fields else "metric_date"
    if metric_date_field not in fields:
        return None
    idx = fields.index(metric_date_field)

    latest: datetime | None = None
    for row in rows:
        try:
            v = row[idx]
        except IndexError:
            continue
        if v is None:
            continue
        # Bitable returns datetime as epoch millis (int) or ISO string
        try:
            if isinstance(v, (int, float)):
                dt = datetime.fromtimestamp(v / 1000, tz=timezone.utc)
            else:
                dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if latest is None or dt > latest:
            latest = dt
    return latest


def signal_to_row(signal, author_record_id: str | None = None) -> dict[str, Any]:
    """Convert a Signal object to a Bitable row dict (HH 5-track schema).

    The legacy `category` column now stores the new `track` value (5 tracks
    + 其他); `subcategory` is left empty. The new fields (cognitive_takeaway_zh,
    is_headline_candidate, etc.) are packed into `extract_json` for now to
    avoid Bitable schema churn — they can be added as columns later if desired.
    """
    def fmt_dt(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

    row = {
        "source_id": signal.source_id,
        "source": signal.source if signal.source != "rss" else "other",
        "url": signal.url,
        "raw_text": signal.raw_text,
        "lang": signal.lang,
        "created_at": fmt_dt(signal.created_at),
        "fetched_at": fmt_dt(signal.fetched_at),
        "summary_zh": signal.summary_zh,
        "novelty_score": signal.novelty_score,
        "category": signal.track,  # new track value goes here (after schema migration)
        "subcategory": None,
        "key_terms": ", ".join(signal.key_terms) if signal.key_terms else None,
        "in_daily_digest": False,
        "needs_human_review": signal.needs_human_review,
        "extract_json": signal.extract_json,
    }
    return {k: v for k, v in row.items() if v is not None}
