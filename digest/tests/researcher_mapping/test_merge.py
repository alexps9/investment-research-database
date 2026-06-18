"""merge.py 字段级合并测试"""
from hh_research.extract.researcher_mapping.merge import merge_candidates
from hh_research.storage.schemas import CoauthorInfo


def test_both_agree_on_affiliation():
    a = CoauthorInfo(name="Tri Dao", affiliation="Princeton")
    b = CoauthorInfo(name="Tri Dao", affiliation="Princeton University")
    merged = merge_candidates(a, b)
    # PyAlex 值优先（来自 b）
    assert merged.affiliation == "Princeton University"
    assert set(merged.enrich_sources["affiliation"]) == {"anysearch", "openalex"}


def test_conflict_affiliation_prefers_openalex():
    a = CoauthorInfo(name="X", affiliation="Princeton")
    b = CoauthorInfo(name="X", affiliation="MIT")  # 冲突
    merged = merge_candidates(a, b)
    assert merged.affiliation == "MIT"
    assert "openalex(conflict)" in merged.enrich_sources["affiliation"]


def test_only_anysearch_has_github():
    a = CoauthorInfo(name="X", github="tridao")
    b = CoauthorInfo(name="X")
    merged = merge_candidates(a, b)
    assert merged.github == "tridao"
    assert merged.enrich_sources["github"] == ["anysearch"]


def test_only_openalex_has_affiliation():
    a = CoauthorInfo(name="X")
    b = CoauthorInfo(name="X", affiliation="Stanford")
    merged = merge_candidates(a, b)
    assert merged.affiliation == "Stanford"
    assert merged.enrich_sources["affiliation"] == ["openalex"]


def test_both_empty_returns_minimal():
    a = CoauthorInfo(name="X")
    b = CoauthorInfo(name="X")
    merged = merge_candidates(a, b)
    assert merged.name == "X"
    assert merged.affiliation is None
    assert merged.github is None


def test_openalex_none_preserves_anysearch_only():
    a = CoauthorInfo(name="X", affiliation="Princeton", github="tridao", email="t@p.edu")
    merged = merge_candidates(a, None)
    assert merged.affiliation == "Princeton"
    assert merged.github == "tridao"
    assert merged.email == "t@p.edu"
    assert merged.enrich_sources == {
        "affiliation": ["anysearch"],
        "github": ["anysearch"],
        "email": ["anysearch"],
    }


def test_anysearch_none_preserves_openalex_only():
    b = CoauthorInfo(name="X", affiliation="Princeton")
    merged = merge_candidates(None, b)
    assert merged.affiliation == "Princeton"
    assert merged.enrich_sources == {"affiliation": ["openalex"]}
