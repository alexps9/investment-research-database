"""
Impact scoring service.

Computes impact_score (0-100) for each paper based on:
- citation_score: cited_by_count normalized within same year (percentile)
- venue_score: publication venue tier
- institution_score: author institution tier

Also identifies:
- is_rising: citation rate in top 20% for papers < 2 years old
- is_weak_signal: top institution + low citation + published < 6 months ago
"""

from datetime import datetime
from typing import List

from app.models.evolution import EvolutionPaper


VENUE_SCORE_MAP = {1: 100, 2: 75, 3: 50, 4: 25, 5: 10}
INSTITUTION_SCORE_MAP = {1: 100, 2: 75, 3: 50, 4: 25}

WEIGHTS = {"citation": 0.45, "venue": 0.30, "institution": 0.25}


def compute_impact_scores(papers: List[EvolutionPaper]) -> List[EvolutionPaper]:
    """Compute impact_score, is_rising, is_weak_signal for all papers."""
    papers_by_year: dict[int, list[EvolutionPaper]] = {}
    for p in papers:
        papers_by_year.setdefault(p.year, []).append(p)

    citation_percentiles = _compute_citation_percentiles(papers_by_year)

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    citation_rates: list[tuple[EvolutionPaper, float]] = []

    for p in papers:
        citation_pct = citation_percentiles.get(p.id, 50.0)
        venue_raw = VENUE_SCORE_MAP.get(p.venue_tier or 4, 25)
        institution_raw = INSTITUTION_SCORE_MAP.get(p.institution_tier or 4, 25)

        score = (
            WEIGHTS["citation"] * citation_pct
            + WEIGHTS["venue"] * venue_raw
            + WEIGHTS["institution"] * institution_raw
        )

        if p.impact_override is not None:
            p.impact_score = p.impact_override
        else:
            p.impact_score = round(min(100.0, max(0.0, score)), 1)

        age_months = (current_year - p.year) * 12 + (current_month - (p.quarter * 3))
        age_months = max(1, age_months)
        rate = p.cited_by_count / age_months
        citation_rates.append((p, rate))

        # Weak signal: top institution + low citation + recent
        p.is_weak_signal = (
            (p.institution_tier or 99) <= 2
            and p.cited_by_count < 20
            and age_months <= 6
        )

    _mark_rising(citation_rates)

    return papers


def _compute_citation_percentiles(
    papers_by_year: dict[int, list[EvolutionPaper]],
) -> dict[str, float]:
    """Percentile rank of cited_by_count within same publication year."""
    result: dict[str, float] = {}
    for year, year_papers in papers_by_year.items():
        citations = sorted(p.cited_by_count for p in year_papers)
        n = len(citations)
        for p in year_papers:
            if n <= 1:
                result[p.id] = 50.0
            else:
                rank = citations.index(p.cited_by_count)
                result[p.id] = (rank / (n - 1)) * 100.0
    return result


def _mark_rising(citation_rates: list[tuple[EvolutionPaper, float]]) -> None:
    """Mark top 20% citation rate papers (< 2 years old) as rising."""
    recent = [(p, rate) for p, rate in citation_rates if p.year >= datetime.now().year - 2]
    if not recent:
        return
    rates_sorted = sorted(r for _, r in recent)
    threshold_idx = int(len(rates_sorted) * 0.8)
    threshold = rates_sorted[threshold_idx] if threshold_idx < len(rates_sorted) else float("inf")
    for p, rate in recent:
        if rate >= threshold and rate > 0:
            p.is_rising = True
