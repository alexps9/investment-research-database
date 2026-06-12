import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Source, Signal, SignalAnalysis

router = APIRouter(prefix="/export", tags=["export"])


def _csv_response(rows: list[dict], columns: list[str], filename_prefix: str) -> StreamingResponse:
    """Build a UTF-8 (BOM) CSV streaming response so Excel opens Chinese correctly."""
    buffer = io.StringIO()
    buffer.write("\ufeff")  # UTF-8 BOM for Excel compatibility
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{ts}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


SOURCE_COLUMNS = [
    "id", "name", "source_type", "organization", "tier", "sector",
    "affiliation_type", "activity_status", "source_authority",
    "research_focus", "role_title", "description", "tier_reason", "notes",
    "importance_score", "reliability_score", "is_active",
    "avg_interval_days", "last_tweet_at",
    "twitter_url", "github_url", "scholar_url", "openalex_url",
    "personal_url", "arxiv_homepage_url", "arxiv_author_query",
    "affiliation_regex", "orcid", "created_at", "updated_at",
]


@router.get("/sources.csv")
async def export_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Source).options(selectinload(Source.organization)).order_by(Source.name)
    )
    sources = result.scalars().all()

    rows = []
    for s in sources:
        rows.append({
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "organization": s.organization.name if s.organization else "",
            "tier": s.tier or "",
            "sector": s.sector or "",
            "affiliation_type": s.affiliation_type or "",
            "activity_status": s.activity_status,
            "source_authority": s.source_authority or "",
            "research_focus": s.research_focus or "",
            "role_title": s.role_title or "",
            "description": s.description or "",
            "tier_reason": s.tier_reason or "",
            "notes": s.notes or "",
            "importance_score": s.importance_score,
            "reliability_score": s.reliability_score,
            "is_active": s.is_active,
            "avg_interval_days": s.avg_interval_days if s.avg_interval_days is not None else "",
            "last_tweet_at": s.last_tweet_at.isoformat() if s.last_tweet_at else "",
            "twitter_url": s.twitter_url or "",
            "github_url": s.github_url or "",
            "scholar_url": s.scholar_url or "",
            "openalex_url": s.openalex_url or "",
            "personal_url": s.personal_url or "",
            "arxiv_homepage_url": s.arxiv_homepage_url or "",
            "arxiv_author_query": s.arxiv_author_query or "",
            "affiliation_regex": s.affiliation_regex or "",
            "orcid": s.orcid or "",
            "created_at": s.created_at.isoformat() if s.created_at else "",
            "updated_at": s.updated_at.isoformat() if s.updated_at else "",
        })

    return _csv_response(rows, SOURCE_COLUMNS, "sources")


SIGNAL_COLUMNS = [
    "id", "title", "url", "signal_type", "status", "language",
    "abstract", "published_at", "collected_at",
    "tldr", "summary", "importance_score", "reading_priority",
    "created_at",
]


@router.get("/signals.csv")
async def export_signals(
    signal_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Signal)
        .options(selectinload(Signal.analysis))
        .order_by(Signal.created_at.desc())
    )
    if signal_type:
        stmt = stmt.where(Signal.signal_type == signal_type)
    if status:
        stmt = stmt.where(Signal.status == status)

    result = await db.execute(stmt)
    signals = result.scalars().all()

    rows = []
    for sig in signals:
        a: SignalAnalysis | None = sig.analysis
        rows.append({
            "id": sig.id,
            "title": sig.title,
            "url": sig.url,
            "signal_type": sig.signal_type,
            "status": sig.status,
            "language": sig.language,
            "abstract": sig.abstract or "",
            "published_at": sig.published_at.isoformat() if sig.published_at else "",
            "collected_at": sig.collected_at.isoformat() if sig.collected_at else "",
            "tldr": a.tldr if a else "",
            "summary": a.summary if a else "",
            "importance_score": a.importance_score if a else "",
            "reading_priority": a.reading_priority if a else "",
            "created_at": sig.created_at.isoformat() if sig.created_at else "",
        })

    return _csv_response(rows, SIGNAL_COLUMNS, "signals")
