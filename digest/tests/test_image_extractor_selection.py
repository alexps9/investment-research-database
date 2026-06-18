"""TDD for image_extractor.score_figure_caption — v7.0 P0 caption-aware selection.

Plan reference: /Users/haolinguo/Desktop/2026-05-28-v7-quality-gates.md Task 5.
"""

from hh_research.extract.image_extractor import score_figure_caption


def test_overview_caption_scores_high():
    score = score_figure_caption("Figure 1: Overview of the proposed agent training pipeline")
    assert score >= 80, f"expected ≥80, got {score}"


def test_architecture_caption_scores_high():
    score = score_figure_caption("Fig. 2. System architecture and workflow")
    assert score >= 80, f"expected ≥80, got {score}"


def test_benchmark_caption_scores_low():
    score = score_figure_caption("Figure 4: Benchmark results on six datasets")
    assert score < 50, f"expected <50, got {score}"


def test_table_caption_scores_low():
    score = score_figure_caption("Table 1: Comparison with baselines")
    assert score < 30, f"expected <30, got {score}"


def test_no_caption_is_low_confidence():
    score = score_figure_caption("")
    assert score == 0, f"expected 0, got {score}"
