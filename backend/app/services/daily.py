"""Daily Boost — pick the day's most important signals and write a digest.

Selection: signals whose date(coalesce(published_at, collected_at, created_at))
falls inside the window ending on `digest_date`, ranked by analysis importance
score (then recency). A short summary is generated via the chat LLM when
configured; otherwise a deterministic fallback summary is produced.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models import DailyDigest, Signal
from app.services import llm

settings = get_settings()

DIGEST_SYSTEM_PROMPT = (
    "You are an AI research-intelligence editor. Given a list of the day's most "
    "important AI signals (papers, releases, tweets, news), write a concise daily "
    "briefing in the SAME language as the signal titles (Chinese if titles are "
    "Chinese). Start with one sentence overview, then 3-6 bullet highlights, each "
    "explaining why it matters. Be specific and avoid filler."
)


def _today_str() -> str:
    return datetime.now(timezone.utc).date().isoformat()


async def _select_signals(db: AsyncSession, digest_date: str, window_days: int, limit: int):
    d = date.fromisoformat(digest_date)
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(days=window_days - 1)
    end = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1)

    eff = func.coalesce(Signal.published_at, Signal.collected_at, Signal.created_at)
    result = await db.execute(
        select(Signal)
        .options(selectinload(Signal.analysis))
        .where(eff >= start, eff < end)
    )
    signals = list(result.scalars().all())

    def rank_key(s: Signal):
        score = s.analysis.importance_score if s.analysis else 0.0
        when = s.published_at or s.collected_at or s.created_at
        return (score, when or datetime.min.replace(tzinfo=timezone.utc))

    signals.sort(key=rank_key, reverse=True)
    return signals[:limit]


def _build_highlights(signals: list[Signal]) -> list[dict]:
    highlights = []
    for s in signals:
        reason = None
        if s.analysis:
            reason = s.analysis.tldr or s.analysis.why_it_matters or s.analysis.summary
        highlights.append({
            "signal_id": s.id,
            "title": s.title,
            "url": s.url,
            "signal_type": s.signal_type,
            "reason": (reason or "")[:400] or None,
        })
    return highlights


def _fallback_summary(digest_date: str, highlights: list[dict]) -> str:
    if not highlights:
        return f"{digest_date}: 今日暂无新信号。"
    lines = [f"{digest_date} 每日精选（共 {len(highlights)} 条）："]
    for i, h in enumerate(highlights, 1):
        extra = f" — {h['reason']}" if h.get("reason") else ""
        lines.append(f"{i}. {h['title']}{extra}")
    return "\n".join(lines)


async def generate_digest(
    db: AsyncSession,
    digest_date: str | None = None,
    window_days: int = 1,
    limit: int = 8,
) -> DailyDigest:
    digest_date = digest_date or _today_str()
    signals = await _select_signals(db, digest_date, window_days, limit)
    highlights = _build_highlights(signals)

    model_name = None
    summary = _fallback_summary(digest_date, highlights)
    if highlights and llm.chat_enabled():
        ctx = "\n".join(
            f"[{i}] ({h['signal_type']}) {h['title']}"
            + (f" — {h['reason']}" if h.get("reason") else "")
            for i, h in enumerate(highlights, 1)
        )
        try:
            summary = await llm.chat([
                {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
                {"role": "user", "content": f"Date: {digest_date}\nSignals:\n{ctx}"},
            ], temperature=0.4, max_tokens=900)
            model_name = settings.llm_model
        except Exception:
            # keep deterministic fallback if the LLM call fails
            pass

    values = {
        "id": str(uuid.uuid4()),
        "digest_date": digest_date,
        "summary": summary,
        "highlights": highlights,
        "signal_count": len(highlights),
        "model_name": model_name,
    }
    stmt = (
        pg_insert(DailyDigest)
        .values(**values)
        .on_conflict_do_update(
            index_elements=["digest_date"],
            set_={
                "summary": values["summary"],
                "highlights": values["highlights"],
                "signal_count": values["signal_count"],
                "model_name": values["model_name"],
                "updated_at": func.now(),
            },
        )
    )
    await db.execute(stmt)
    await db.commit()

    row = (await db.execute(
        select(DailyDigest).where(DailyDigest.digest_date == digest_date)
    )).scalar_one()
    return row
