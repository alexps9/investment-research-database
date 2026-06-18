"""OpenAlex collector — fetches recent works (papers from any venue) for verified authors.

Why this exists alongside arXiv collector:
- arXiv covers preprints (most ML/AI but not all)
- OpenAlex covers ALL venues (NeurIPS, ICML, ACL, Nature, Cell, ...) deduplicated
- Net effect: catches conference + journal papers that don't appear on arXiv

Only operates on whitelist entries with `openalex_url` (24 verified persons in our case).
For unverified entries, the existing arxiv_collector still runs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..storage.schemas import Signal, WhitelistEntry
from ..utils.logger import get_logger
from .base import CollectorBase

log = get_logger("openalex_collector")

OPENALEX_API = "https://api.openalex.org"
UA = {"User-Agent": "HH Research Pipeline; mailto:goalin040302@gmail.com"}


class OpenAlexCollector(CollectorBase):
    source_name = "openalex"

    def __init__(self, request_timeout: float = 30.0) -> None:
        self._client = httpx.Client(headers=UA, timeout=request_timeout)

    def collect(
        self,
        whitelist: list[WhitelistEntry],
        since: datetime,
        until: datetime,
    ) -> Iterable[Signal]:
        """For each verified author, fetch their works in [since, until].

        Note: OpenAlex `publication_date` is in YYYY-MM-DD (no time-of-day),
        so we filter by date (inclusive). Dedup works at TWO levels:
          - source_id: catches identical entries
          - normalized title: catches arXiv-version vs venue-version of same paper
        """
        fetched_at = datetime.now(timezone.utc)
        seen_ids: set[str] = set()
        seen_titles: set[str] = set()

        for entry in whitelist:
            author_id = entry.openalex_id
            if not author_id:
                continue
            try:
                for work in self._fetch_works(author_id, since, until):
                    sid = self._make_source_id(work)
                    if sid in seen_ids:
                        continue
                    title_key = _normalize_title(
                        work.get("display_name") or work.get("title") or ""
                    )
                    if title_key and title_key in seen_titles:
                        continue
                    seen_ids.add(sid)
                    if title_key:
                        seen_titles.add(title_key)
                    yield self._work_to_signal(work, entry, fetched_at, sid)
            except httpx.HTTPError as e:
                log.warning("openalex fetch failed for %s (%s): %s", entry.name, author_id, e)
                continue

    def close(self) -> None:
        self._client.close()

    # -------- internals --------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def _fetch_works(
        self,
        author_id: str,
        since: datetime,
        until: datetime,
    ) -> Iterable[dict]:
        from_date = since.date().isoformat()
        to_date = until.date().isoformat()
        params = {
            "filter": (
                f"author.id:{author_id},"
                f"from_publication_date:{from_date},"
                f"to_publication_date:{to_date}"
            ),
            "per-page": 25,
            "sort": "publication_date:desc",
            "select": (
                "id,doi,title,display_name,publication_date,abstract_inverted_index,"
                "primary_location,authorships,locations,cited_by_count,type"
            ),
        }
        resp = self._client.get(f"{OPENALEX_API}/works", params=params)
        resp.raise_for_status()
        data = resp.json()
        for work in data.get("results", []):
            yield work

    def _make_source_id(self, work: dict) -> str:
        """Build a globally-unique source_id.

        Prefer arXiv ID if present (so we naturally dedupe against arxiv_collector),
        fall back to DOI (also recognising arXiv DOIs), fall back to OpenAlex ID.
        """
        # Look for arxiv ID in any location
        for loc in [work.get("primary_location") or {}] + (work.get("locations") or []):
            src = (loc or {}).get("source") or {}
            if (src.get("display_name") or "").lower() == "arxiv":
                landing = loc.get("landing_page_url") or ""
                if "arxiv.org/abs/" in landing:
                    arxiv_id = landing.split("arxiv.org/abs/")[-1].rstrip("/")
                    return f"arxiv:{arxiv_id}"

        # Fall back to DOI — but recognise arXiv-style DOIs like 10.48550/arxiv.YYMM.NNNNN
        doi = work.get("doi") or ""
        if doi:
            doi_clean = doi.replace("https://doi.org/", "").rstrip("/").lower()
            if doi_clean.startswith("10.48550/arxiv."):
                arxiv_id = doi_clean.removeprefix("10.48550/arxiv.")
                return f"arxiv:{arxiv_id}"
            return f"doi:{doi_clean}"

        # Last resort: OpenAlex ID
        oa_url = work.get("id", "")
        oa_id = oa_url.rstrip("/").rsplit("/", 1)[-1] if oa_url else "unknown"
        return f"openalex:{oa_id}"

    def _work_to_signal(
        self,
        work: dict,
        entry: WhitelistEntry,
        fetched_at: datetime,
        source_id: str,
    ) -> Signal:
        title = work.get("display_name") or work.get("title") or "(no title)"
        abstract = _decode_abstract(work.get("abstract_inverted_index"))
        venue_name = ""
        primary_loc = work.get("primary_location") or {}
        if primary_loc:
            venue_name = (primary_loc.get("source") or {}).get("display_name", "") or ""
        # Build a "raw_text" similar to arxiv format: title + abstract
        raw_text = f"{title}\n\n{abstract}".strip()[:8000]

        # Pub date → datetime (00:00 UTC since OpenAlex doesn't give time)
        pub_date_str = work.get("publication_date") or ""
        try:
            created_at = datetime.fromisoformat(pub_date_str).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            created_at = fetched_at

        # If the source_id is arxiv:..., mark source as arxiv (so dedup works
        # naturally and downstream prompts treat it as a paper). Otherwise openalex.
        signal_source = "arxiv" if source_id.startswith("arxiv:") else "openalex"

        # Get a canonical URL: prefer DOI, then OpenAlex landing
        url = ""
        if work.get("doi"):
            url = work["doi"]  # already has https://doi.org/ prefix
        elif primary_loc.get("landing_page_url"):
            url = primary_loc["landing_page_url"]
        else:
            url = work.get("id", "")

        return Signal(
            source=signal_source,
            source_id=source_id,
            author_name=entry.name,
            author_record_id=entry.record_id,
            url=url,
            raw_text=raw_text,
            lang="en",
            created_at=created_at,
            fetched_at=fetched_at,
            needs_human_review=False,
        )


def _decode_abstract(inverted: dict | None) -> str:
    """OpenAlex stores abstracts as inverted-index dict {token: [positions]}.
    Reconstruct ordered text."""
    if not inverted:
        return ""
    pos_to_token: dict[int, str] = {}
    for token, positions in inverted.items():
        for p in positions:
            pos_to_token[p] = token
    if not pos_to_token:
        return ""
    return " ".join(pos_to_token[p] for p in sorted(pos_to_token.keys()))


def _normalize_title(title: str) -> str:
    """Normalize a paper title for dedup: lowercase + strip punctuation/whitespace."""
    import re

    if not title:
        return ""
    s = title.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)  # punctuation → space
    s = re.sub(r"\s+", " ", s)  # collapse spaces
    return s.strip()
