"""
Impact scoring algorithm tests — TDD style.

Ground truth: human-expected ordering of representative papers.
The algorithm must produce scores that respect these orderings.
When tests fail → adjust weights/formula, not the expectations.
"""

import pytest

from app.models.evolution import EvolutionPaper
from app.services.impact_scoring import compute_impact_scores


def _make_paper(id, cited_by_count, year, quarter=1, venue_tier=None, institution_tier=None, **kw):
    """Minimal paper for scoring tests. Only scoring-relevant fields matter."""
    return EvolutionPaper(
        id=id, title=id, year=year, quarter=quarter,
        paradigm="rssm", layer="arch", lane="rl_wm", row="dreamer_series", path="trunk",
        size="md", cited_by_count=cited_by_count,
        venue_tier=venue_tier, institution_tier=institution_tier, **kw,
    )


# === Ground truth test set ===
# Hand-verified citation counts + correct tier annotations.
# These represent "what a domain expert expects" as relative ordering.

SEED_PAPERS = [
    # --- T1: Undisputed landmarks ---
    # Dreamer V3: OpenAlex has 2 entries (arXiv=92 + Nature=67), merged=159. Published Nature 2025 but arxiv 2023.
    _make_paper("dreamer_v3", cited_by_count=159, year=2023, quarter=1, venue_tier=1, institution_tier=1),
    _make_paper("sora", cited_by_count=0, year=2024, quarter=1, venue_tier=5, institution_tier=1,
                impact_override=92),  # Not in OpenAlex, industry inflection point
    _make_paper("i_jepa", cited_by_count=272, year=2023, quarter=2, venue_tier=2, institution_tier=1),
    _make_paper("planet", cited_by_count=367, year=2019, quarter=1, venue_tier=2, institution_tier=1),
    _make_paper("gpt4", cited_by_count=2318, year=2023, quarter=1, venue_tier=5, institution_tier=1),
    _make_paper("diffusion_policy", cited_by_count=397, year=2023, quarter=3, venue_tier=2, institution_tier=2),

    # --- T2: Solid, important contributions ---
    _make_paper("slot_attention", cited_by_count=218, year=2020, quarter=3, venue_tier=2, institution_tier=1),
    _make_paper("dreamer_v1", cited_by_count=137, year=2020, quarter=1, venue_tier=2, institution_tier=1),
    _make_paper("rt2", cited_by_count=266, year=2023, quarter=3, venue_tier=4, institution_tier=1),
    _make_paper("text2room", cited_by_count=129, year=2023, quarter=2, venue_tier=2, institution_tier=2),
    _make_paper("tdmpc2", cited_by_count=8, year=2024, quarter=1, venue_tier=2, institution_tier=2),
    _make_paper("v_jepa", cited_by_count=56, year=2024, quarter=1, venue_tier=4, institution_tier=1),
    _make_paper("tdmpc", cited_by_count=27, year=2022, quarter=3, venue_tier=2, institution_tier=2),

    # --- T3: New / niche / unproven ---
    _make_paper("tesseract", cited_by_count=14, year=2025, quarter=1, venue_tier=4, institution_tier=2),
    _make_paper("dino_wm", cited_by_count=5, year=2025, quarter=1, venue_tier=4, institution_tier=1),
    _make_paper("cosmos", cited_by_count=0, year=2025, quarter=1, venue_tier=5, institution_tier=1,
                impact_override=40),  # Not in OpenAlex, NVIDIA push but unproven
    _make_paper("slotformer", cited_by_count=10, year=2023, quarter=1, venue_tier=2, institution_tier=2),
    _make_paper("gen3", cited_by_count=0, year=2024, quarter=2, venue_tier=5, institution_tier=3,
                impact_override=45),  # Runway product, not academic
]


def _score_map():
    """Run scoring on seed papers and return {id: score} dict."""
    scored = compute_impact_scores(list(SEED_PAPERS))
    return {p.id: p.impact_score for p in scored}


class TestTierOrdering:
    """T1 papers must score higher than T2, T2 higher than T3."""

    def test_t1_above_t3(self):
        """Every T1 paper must outscore every T3 paper."""
        scores = _score_map()
        t1 = ["dreamer_v3", "sora", "i_jepa", "planet", "gpt4", "diffusion_policy"]
        t3 = ["tesseract", "dino_wm", "cosmos", "slotformer"]
        for high in t1:
            for low in t3:
                assert scores[high] > scores[low], f"T1 {high}({scores[high]}) should > T3 {low}({scores[low]})"

    def test_t1_above_t2(self):
        """T1 papers should generally score above T2."""
        scores = _score_map()
        t1_min = min(scores[p] for p in ["dreamer_v3", "sora", "i_jepa", "planet", "gpt4", "diffusion_policy"])
        t2_avg = sum(scores[p] for p in ["tdmpc2", "v_jepa", "tdmpc"]) / 3
        assert t1_min > t2_avg, f"T1 min ({t1_min}) should > T2 avg ({t2_avg})"

    def test_sora_above_tesseract(self):
        """The inflection-point paper must outscore its follower."""
        scores = _score_map()
        assert scores["sora"] > scores["tesseract"]

    def test_sora_above_cosmos(self):
        """Sora (proven impact) > Cosmos (just released, unproven)."""
        scores = _score_map()
        assert scores["sora"] > scores["cosmos"]

    def test_i_jepa_above_dino_wm(self):
        """Foundational paper > derivative work."""
        scores = _score_map()
        assert scores["i_jepa"] > scores["dino_wm"]

    def test_planet_above_tesseract(self):
        """Classic seminal paper > recent incremental."""
        scores = _score_map()
        assert scores["planet"] > scores["tesseract"]

    def test_diffusion_policy_above_tesseract(self):
        """Major method paper > follow-up application."""
        scores = _score_map()
        assert scores["diffusion_policy"] > scores["tesseract"]

    def test_rt2_above_gen3(self):
        """DeepMind landmark > Runway product release."""
        scores = _score_map()
        assert scores["rt2"] > scores["gen3"]

    def test_dreamer_v1_above_slotformer(self):
        """Seminal RL-WM > niche object-centric dynamics."""
        scores = _score_map()
        assert scores["dreamer_v1"] > scores["slotformer"]


class TestScoreRange:
    """Scores should use a reasonable range of the 0-100 spectrum."""

    def test_top_paper_above_80(self):
        scores = _score_map()
        top = max(scores.values())
        assert top >= 80, f"Top score {top} is too low, should be >= 80"

    def test_bottom_paper_below_50(self):
        scores = _score_map()
        bottom = min(scores.values())
        assert bottom <= 50, f"Bottom score {bottom} is too high, should be <= 50"

    def test_spread_at_least_40(self):
        """Need enough visual differentiation."""
        scores = _score_map()
        spread = max(scores.values()) - min(scores.values())
        assert spread >= 40, f"Score spread {spread} too narrow for visual encoding"


class TestOverrideStrategy:
    """Papers not indexed by OpenAlex use impact_override to set score directly."""

    def test_sora_uses_override(self):
        """Sora override=92, should come out as 92."""
        scores = _score_map()
        assert scores["sora"] == 92

    def test_cosmos_uses_override(self):
        """Cosmos override=40, unproven but notable."""
        scores = _score_map()
        assert scores["cosmos"] == 40

    def test_gpt4_high_despite_venue(self):
        """GPT-4 is a tech report but has 2318 citations — venue penalty must be dampened."""
        scores = _score_map()
        assert scores["gpt4"] >= 80, f"GPT-4 score {scores['gpt4']} too low"


class TestRisingSignal:
    """Rising = high citation rate for age, among recent papers."""

    def test_cosmos_not_rising(self):
        """Brand new paper with low citations should NOT be rising."""
        scored = compute_impact_scores(list(SEED_PAPERS))
        cosmos = next(p for p in scored if p.id == "cosmos")
        assert not cosmos.is_rising

    def test_high_rate_paper_is_rising(self):
        """A 2025 paper with unusually high citations should be rising."""
        papers = list(SEED_PAPERS) + [
            _make_paper("hot_new", cited_by_count=200, year=2025, quarter=1, venue_tier=3, institution_tier=2),
        ]
        scored = compute_impact_scores(papers)
        hot = next(p for p in scored if p.id == "hot_new")
        assert hot.is_rising


class TestWeakSignal:
    """Weak signal = top institution + low citation + very recent (< 6 months)."""

    def test_brand_new_top_institution_is_weak_signal(self):
        """T1 institution, <6 months old, low citations → weak signal."""
        papers = list(SEED_PAPERS) + [
            _make_paper("new_meta_2026", cited_by_count=3, year=2026, quarter=1,
                        venue_tier=4, institution_tier=1),
        ]
        scored = compute_impact_scores(papers)
        new_paper = next(p for p in scored if p.id == "new_meta_2026")
        assert new_paper.is_weak_signal

    def test_old_paper_not_weak_signal(self):
        """Even with low citations, 14-month-old paper is not weak signal."""
        scored = compute_impact_scores(list(SEED_PAPERS))
        dino = next(p for p in scored if p.id == "dino_wm")
        assert not dino.is_weak_signal


# === Diagnostic helper (not a test, run with pytest -s) ===

def test_print_all_scores():
    """Print full score breakdown for tuning. Run: pytest -s -k print_all"""
    scores = _score_map()
    print("\n=== Impact Score Results ===")
    for pid, score in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"  {pid:20s} → {score:.1f}")
    print()
