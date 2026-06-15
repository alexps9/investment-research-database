"""arXiv collector.

Strategy:
1. For each whitelist entry with `arxiv_author_query` set, query arXiv by author.
2. Also run a category-wide query (cs.AI/cs.LG/cs.CL) within the window, and
   filter by `affiliation_regex` when an entry has no explicit author_query.
3. Yield Signal objects. Dedup happens upstream (pipeline).

arXiv API is free but rate-limited; `arxiv` Python client applies a 3.1s delay
between requests by default. We serialize calls within this collector.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Iterable

import arxiv
import httpx

from ..storage.schemas import Signal, WhitelistEntry
from ..utils.logger import get_logger
from .base import CollectorBase

log = get_logger("arxiv_collector")


def _utcnow() -> datetime:
    """可注入的当前 UTC 时间（测试可 monkeypatch，避免「8 天 HTML 窗口」判断随真实时间漂移）。"""
    return datetime.now(timezone.utc)


_NET_ERR_MARKERS = (
    "nodename nor servname", "Temporary failure in name resolution",
    "Failed to resolve", "Connection", "timed out", "Max retries",
    "Network is unreachable",
)


def _is_network_error(e: BaseException) -> bool:
    """判断异常是否为网络层失败（用于 arxiv 熔断的 network_error 标记）。"""
    if isinstance(e, httpx.HTTPError):
        return True
    s = str(e)
    return any(m in s for m in _NET_ERR_MARKERS)

DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO", "cs.MA", "stat.ML"]
ARXIV_HTML_BASE = "https://arxiv.org"
HTML_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@dataclass(frozen=True)
class ArxivHtmlPaper:
    arxiv_id: str
    title: str
    authors: list[str]
    announced_date: datetime.date | None = None
    subjects: str = ""


class ArxivCollector(CollectorBase):
    source_name = "arxiv"

    def __init__(
        self,
        categories: list[str] | None = None,
        max_results_per_query: int = 50,
        client_delay_seconds: float = 5.0,
        max_consecutive_failures: int = 5,
    ) -> None:
        self.categories = categories or DEFAULT_CATEGORIES
        self.max_results_per_query = max_results_per_query
        self.max_consecutive_failures = max_consecutive_failures
        # Bumped delay 3.1 → 5.0s to reduce 429 rate-limit risk when running
        # many author queries in succession.
        self._client = arxiv.Client(
            page_size=max_results_per_query,
            delay_seconds=client_delay_seconds,
            num_retries=2,  # keep retries low; we have our own backoff loop
        )
        self._html_client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers=HTML_HEADERS,
        )

    def collect_by_window(
        self,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
    ) -> Iterable[Signal]:
        """Fast backfill: query each category for the time window once, then
        filter results locally to whitelist authors. Single-digit API calls
        instead of N (=author count). Recommended for backfill runs.
        """
        fetched_at = _utcnow()
        # Task3: 暴露窗口采集 metrics 供 daily.py 做 arxiv 质量熔断判定
        self.last_window_metrics = {"html_candidates": 0, "network_error": False}

        # Build author name -> WhitelistEntry index for fuzzy matching
        # Use lowercased last+first name fragments
        name_index: dict[str, WhitelistEntry] = {}
        for e in whitelist:
            if not e.name:
                continue
            # Normalize: lowercase, strip CJK/parens
            import re as _re
            cleaned = _re.sub(r"[一-鿿㐀-䶿()()\[\]【】]+", " ", e.name)
            tokens = [t for t in cleaned.split() if len(t) >= 2]
            if len(tokens) < 2:
                continue
            # Use "first_token last_token" as key (most common ordering)
            key = (tokens[0] + " " + tokens[-1]).lower()
            name_index[key] = e

        # Format dates for arxiv query: YYYYMMDDHHMM
        from_date = since.strftime("%Y%m%d%H%M")
        to_date = until.strftime("%Y%m%d%H%M")
        use_html_announcement_list = until >= _utcnow() - timedelta(days=8)

        seen_ids: set[str] = set()
        # For each category, fetch papers in the window
        for cat in self.categories:
            if use_html_announcement_list:
                try:
                    html_count = 0
                    for sig in self._collect_category_from_html(
                        cat, whitelist, since, until, fetched_at, seen_ids
                    ):
                        html_count += 1
                        yield sig
                    log.info("arxiv html cat=%s: %d matched papers", cat, html_count)
                    continue
                except Exception as e:  # noqa: BLE001
                    if _is_network_error(e):
                        self.last_window_metrics["network_error"] = True
                    log.warning(
                        "arxiv html primary failed for %s, falling back to export API: %s",
                        cat,
                        str(e)[:200],
                    )

            query = f"cat:{cat} AND submittedDate:[{from_date} TO {to_date}]"
            search = arxiv.Search(
                query=query,
                max_results=200,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            try:
                paper_count = 0
                for paper in self._client.results(search):
                    paper_count += 1
                    if not _in_window(paper.published, since, until):
                        continue
                    # Check if any author matches our whitelist
                    matched_entry: WhitelistEntry | None = None
                    for author in paper.authors:
                        a_tokens = author.name.split()
                        if len(a_tokens) >= 2:
                            a_key = (a_tokens[0] + " " + a_tokens[-1]).lower()
                            if a_key in name_index:
                                matched_entry = name_index[a_key]
                                break
                    if matched_entry is None:
                        continue
                    sid = f"arxiv:{_paper_id(paper)}"
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    yield self._paper_to_signal(paper, matched_entry, fetched_at)
                log.info("arxiv cat=%s: %d papers in window", cat, paper_count)
            except Exception as e:  # noqa: BLE001
                if _is_network_error(e):
                    self.last_window_metrics["network_error"] = True
                log.warning("arxiv category query failed for %s: %s", cat, str(e)[:200])
                try:
                    fallback_count = 0
                    for sig in self._collect_category_from_html(
                        cat, whitelist, since, until, fetched_at, seen_ids
                    ):
                        fallback_count += 1
                        yield sig
                    log.info("arxiv html fallback cat=%s: %d matched papers", cat, fallback_count)
                except Exception as fallback_e:  # noqa: BLE001
                    if _is_network_error(fallback_e):
                        self.last_window_metrics["network_error"] = True
                    log.warning(
                        "arxiv html fallback failed for %s: %s",
                        cat,
                        str(fallback_e)[:200],
                    )

    def collect(
        self,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
    ) -> Iterable[Signal]:
        fetched_at = datetime.now(timezone.utc)
        seen_ids: set[str] = set()

        # Pass 1: explicit author queries (with circuit breaker on consecutive
        # 429 failures — we abort early instead of hammering arXiv)
        consecutive_failures = 0
        for entry in whitelist:
            if not entry.arxiv_author_query:
                continue
            try:
                yield from self._collect_by_author(
                    entry, since, until, fetched_at, seen_ids
                )
                consecutive_failures = 0
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                log.warning("arxiv author query failed for %s: %s", entry.name, msg[:200])
                if "429" in msg or "rate" in msg.lower():
                    consecutive_failures += 1
                    if consecutive_failures >= self.max_consecutive_failures:
                        log.error(
                            "arxiv: %d consecutive rate-limit failures, aborting collection",
                            consecutive_failures,
                        )
                        break
                    # Add extra cool-down: sleep proportional to # of failures
                    import time
                    cooldown = min(60, 10 * consecutive_failures)
                    log.info("arxiv: cooling down %.0fs before next author", cooldown)
                    time.sleep(cooldown)

        # Pass 2: category-wide + affiliation_regex for entries missing author_query
        regex_entries = [
            e for e in whitelist if not e.arxiv_author_query and e.affiliation_regex
        ]
        if regex_entries:
            try:
                yield from self._collect_by_category_and_affil(
                    regex_entries, since, until, fetched_at, seen_ids
                )
            except Exception as e:  # noqa: BLE001
                log.warning("arxiv category-wide pass failed: %s", e)

    # ---------- internals ----------

    def _collect_category_from_html(
        self,
        category: str,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
        fetched_at: datetime,
        seen_ids: set[str],
    ) -> Iterable[Signal]:
        url = f"{ARXIV_HTML_BASE}/list/{category}/pastweek?skip=0&show=2000"
        resp = self._html_client.get(url)
        resp.raise_for_status()
        papers = _parse_arxiv_list_html(resp.text)
        candidate_count = sum(1 for paper in papers if self._html_paper_in_window(paper, since, until))
        log.info("arxiv html cat=%s: %d announcement-list candidates", category, candidate_count)
        _m = getattr(self, "last_window_metrics", None)
        if _m is not None:
            _m["html_candidates"] = _m.get("html_candidates", 0) + candidate_count

        abstracts: dict[str, tuple[str, str]] = {}
        for paper in papers:
            if self._match_html_paper(paper, whitelist, since, until) is None:
                continue
            try:
                abs_resp = self._html_client.get(f"{ARXIV_HTML_BASE}/abs/{paper.arxiv_id}")
                abs_resp.raise_for_status()
                title, abstract = _parse_arxiv_abs_html(abs_resp.text)
                abstracts[paper.arxiv_id] = (title or paper.title, abstract)
            except Exception as e:  # noqa: BLE001
                log.warning("arxiv html abs fetch failed for %s: %s", paper.arxiv_id, str(e)[:120])
                abstracts[paper.arxiv_id] = (paper.title, "")

        yield from self._html_papers_to_signals(
            papers,
            whitelist,
            since,
            until,
            fetched_at,
            seen_ids,
            abstracts,
        )

    def _html_papers_to_signals(
        self,
        papers: list[ArxivHtmlPaper],
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
        fetched_at: datetime,
        seen_ids: set[str],
        abstracts: dict[str, tuple[str, str]],
    ) -> Iterable[Signal]:
        for paper in papers:
            matched_entry = self._match_html_paper(paper, whitelist, since, until)
            if matched_entry is None:
                continue
            sid = f"arxiv:{paper.arxiv_id}"
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            title, abstract = abstracts.get(paper.arxiv_id, (paper.title, ""))
            raw = f"{title}\n\n{abstract}".strip()
            created_at = _html_announced_datetime(paper, fetched_at)
            yield Signal(
                source="arxiv",
                source_id=sid,
                author_name=matched_entry.name,
                author_record_id=matched_entry.record_id,
                url=f"{ARXIV_HTML_BASE}/abs/{paper.arxiv_id}",
                raw_text=raw[:8000],
                lang="en",
                created_at=created_at,
                fetched_at=fetched_at,
                needs_human_review=False,
            )

    def _match_html_paper(
        self,
        paper: ArxivHtmlPaper,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
    ) -> WhitelistEntry | None:
        if not self._html_paper_in_window(paper, since, until):
            return None

        name_index = _build_name_index(whitelist)
        for author in paper.authors:
            key = _name_key(author)
            if key and key in name_index:
                return name_index[key]
        return None

    def _html_paper_in_window(
        self,
        paper: ArxivHtmlPaper,
        since: datetime,
        until: datetime,
    ) -> bool:
        if paper.announced_date is None:
            return True
        announced_dt = _html_announced_datetime(paper, fallback=since)
        return _in_window(announced_dt, since, until)

    def _collect_by_author(
        self,
        entry: WhitelistEntry,
        since: datetime,
        until: datetime,
        fetched_at: datetime,
        seen_ids: set[str],
    ) -> Iterable[Signal]:
        assert entry.arxiv_author_query
        # Constrain to AI/ML-related categories to avoid same-name collisions
        # with physicists/biologists who share common names (e.g. "Ting Chen").
        category_clause = " OR ".join(f"cat:{c}" for c in self.categories)
        query = f"({entry.arxiv_author_query}) AND ({category_clause})"
        search = arxiv.Search(
            query=query,
            max_results=self.max_results_per_query,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        for paper in self._client.results(search):
            if not _in_window(paper.published, since, until):
                continue
            sid = f"arxiv:{_paper_id(paper)}"
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            yield self._paper_to_signal(paper, entry, fetched_at)

    def _collect_by_category_and_affil(
        self,
        regex_entries: list[WhitelistEntry],
        since: datetime,
        until: datetime,
        fetched_at: datetime,
        seen_ids: set[str],
    ) -> Iterable[Signal]:
        # Build regex union once
        pattern = "|".join(f"(?:{e.affiliation_regex})" for e in regex_entries)
        affil_re = re.compile(pattern, re.IGNORECASE)

        category_query = " OR ".join(f"cat:{c}" for c in self.categories)
        search = arxiv.Search(
            query=f"({category_query})",
            max_results=self.max_results_per_query * 4,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        for paper in self._client.results(search):
            if not _in_window(paper.published, since, until):
                continue
            # Note: arxiv python client doesn't expose affiliation directly;
            # match on comment / author string as a weak heuristic.
            haystack = " | ".join(a.name for a in paper.authors)
            if paper.comment:
                haystack += " | " + paper.comment
            if not affil_re.search(haystack):
                continue
            sid = f"arxiv:{_paper_id(paper)}"
            if sid in seen_ids:
                continue
            seen_ids.add(sid)
            # author_name: pick first matching author if possible
            matched = next(
                (a.name for a in paper.authors if affil_re.search(a.name)),
                paper.authors[0].name if paper.authors else "unknown",
            )
            yield self._paper_to_signal(paper, None, fetched_at, override_author=matched, needs_review=True)

    def _paper_to_signal(
        self,
        paper: arxiv.Result,
        entry: WhitelistEntry | None,
        fetched_at: datetime,
        override_author: str | None = None,
        needs_review: bool = False,
    ) -> Signal:
        pid = _paper_id(paper)
        author_name = override_author or (entry.name if entry else paper.authors[0].name if paper.authors else "unknown")
        raw = f"{paper.title}\n\n{paper.summary.strip()}"
        return Signal(
            source="arxiv",
            source_id=f"arxiv:{pid}",
            author_name=author_name,
            author_record_id=entry.record_id if entry else None,
            url=paper.entry_id,
            raw_text=raw[:8000],  # truncate very long abstracts
            lang="en",
            created_at=paper.published if paper.published.tzinfo else paper.published.replace(tzinfo=timezone.utc),
            fetched_at=fetched_at,
            needs_human_review=needs_review,
        )


def _in_window(dt: datetime, since: datetime, until: datetime) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    return since <= dt < until


def _build_name_index(whitelist: list[WhitelistEntry]) -> dict[str, WhitelistEntry]:
    name_index: dict[str, WhitelistEntry] = {}
    for entry in whitelist:
        key = _name_key(entry.name)
        if key:
            name_index[key] = entry
    return name_index


def _name_key(name: str | None) -> str | None:
    if not name:
        return None
    cleaned = re.sub(r"[一-鿿㐀-䶿()()\[\]【】]+", " ", name)
    tokens = [t for t in cleaned.split() if len(t) >= 2]
    if len(tokens) < 2:
        return None
    return (tokens[0] + " " + tokens[-1]).lower()


def _html_announced_datetime(paper: ArxivHtmlPaper, fallback: datetime) -> datetime:
    """ArXiv 的 announced_date 是 **EDT 当日 date**（HTML 显示 "Fri, 22 May 2026"）。
    arxiv 实际 announce 时刻是 **EDT 当日 20:00 = UTC 次日 00:00**。
    所以 announced_date 必须 +1 day 才能映射到真实 UTC announce 时刻：
      HTML "Fri, 22 May 2026" → announced_date=2026-05-22
      实际 announce = EDT 5.22 20:00 = UTC 5.23 00:00

    主线 BJT 8:30 起跑窗口 = UTC 昨天 00:30 → 今天 00:30。
    昨天 EDT announce 的 paper (HTML date = 昨天 EDT) → UTC 今天 00:00 → 命中窗口 ✓

    历史:
      v1 = +12 hours (UTC noon) — bug
      v2 = +30 minutes (UTC 00:30) — off-by-one
      v3 = +0 (UTC EDT-date 00:00) — 时区错算，把 EDT date 当 UTC date，少算 24h
      v4 = +1 day (UTC next-day 00:00) — fix: EDT 当日 20:00 = UTC 次日 00:00 (current)"""
    if paper.announced_date is None:
        return fallback
    return datetime.combine(
        paper.announced_date,
        datetime.min.time(),
        tzinfo=timezone.utc,
    ) + timedelta(days=1)


def _paper_id(paper: arxiv.Result) -> str:
    """Extract 'arxiv:2501.12345v1' style id from a Result."""
    # entry_id: http://arxiv.org/abs/2501.12345v1
    return paper.entry_id.rsplit("/", 1)[-1]


class _ArxivListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.papers: list[ArxivHtmlPaper] = []
        self.current_date: datetime.date | None = None
        self._in_h3 = False
        self._h3_text: list[str] = []
        self._current: dict | None = None
        self._field: str | None = None
        self._field_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "h3":
            self._in_h3 = True
            self._h3_text = []
            return
        if tag == "dt":
            self._current = {
                "arxiv_id": "",
                "title": "",
                "authors": [],
                "subjects": "",
                "announced_date": self.current_date,
            }
            return
        if self._current is not None and tag == "a":
            href = attr.get("href") or ""
            match = re.match(r"/abs/([^?#]+)", href)
            if match and not self._current.get("arxiv_id"):
                self._current["arxiv_id"] = match.group(1)
            return
        if self._current is not None and tag == "div":
            classes = attr.get("class") or ""
            if "list-title" in classes:
                self._start_field("title")
            elif "list-authors" in classes:
                self._start_field("authors")
            elif "list-subjects" in classes:
                self._start_field("subjects")

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._in_h3:
            self.current_date = _parse_arxiv_date_heading(" ".join(self._h3_text))
            self._in_h3 = False
            return
        if tag == "div" and self._field and self._current is not None:
            text = _clean_text(" ".join(self._field_text))
            if self._field == "title":
                self._current["title"] = _strip_descriptor(text, "Title:")
            elif self._field == "authors":
                authors_text = _strip_descriptor(text, "Authors:")
                self._current["authors"] = [
                    a.strip()
                    for a in re.split(r"\s*,\s*", authors_text)
                    if a.strip()
                ]
            elif self._field == "subjects":
                self._current["subjects"] = _strip_descriptor(text, "Subjects:")
            self._field = None
            self._field_text = []
            return
        if tag == "dd" and self._current is not None:
            if self._current.get("arxiv_id") and self._current.get("title"):
                self.papers.append(
                    ArxivHtmlPaper(
                        arxiv_id=self._current["arxiv_id"],
                        title=self._current["title"],
                        authors=self._current.get("authors", []),
                        announced_date=self._current.get("announced_date"),
                        subjects=self._current.get("subjects", ""),
                    )
                )
            self._current = None

    def handle_data(self, data: str) -> None:
        if self._in_h3:
            self._h3_text.append(data)
        if self._field:
            self._field_text.append(data)

    def _start_field(self, field: str) -> None:
        self._field = field
        self._field_text = []


class _ArxivAbsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.abstract = ""
        self._field: str | None = None
        self._field_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = attr.get("class") or ""
        if tag == "h1" and "title" in classes:
            self._start_field("title")
        elif tag == "blockquote" and "abstract" in classes:
            self._start_field("abstract")

    def handle_endtag(self, tag: str) -> None:
        if self._field == "title" and tag == "h1":
            self.title = _strip_descriptor(_clean_text(" ".join(self._field_text)), "Title:")
            self._field = None
            self._field_text = []
        elif self._field == "abstract" and tag == "blockquote":
            self.abstract = _strip_descriptor(
                _clean_text(" ".join(self._field_text)),
                "Abstract:",
            )
            self._field = None
            self._field_text = []

    def handle_data(self, data: str) -> None:
        if self._field:
            self._field_text.append(data)

    def _start_field(self, field: str) -> None:
        self._field = field
        self._field_text = []


def _parse_arxiv_list_html(html: str) -> list[ArxivHtmlPaper]:
    parser = _ArxivListParser()
    parser.feed(html)
    return parser.papers


def _parse_arxiv_abs_html(html: str) -> tuple[str, str]:
    parser = _ArxivAbsParser()
    parser.feed(html)
    return parser.title, parser.abstract


def _parse_arxiv_date_heading(text: str) -> datetime.date | None:
    clean = re.sub(r"\s*\(.*\)\s*$", "", _clean_text(text))
    for fmt in ("%a, %d %b %Y", "%d %b %Y"):
        try:
            return datetime.strptime(clean, fmt).replace(tzinfo=timezone.utc).date()
        except ValueError:
            continue
    return None


def _strip_descriptor(text: str, descriptor: str) -> str:
    if text.startswith(descriptor):
        return text[len(descriptor):].strip()
    return text.strip()


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text)).strip()
