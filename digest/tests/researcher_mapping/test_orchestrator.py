"""orchestrator 单元测试"""
from unittest.mock import patch

from hh_research.extract.researcher_mapping.orchestrator import (
    select_authors_for_rm,
    enrich_paper_coauthors_v4,
)
from hh_research.storage.schemas import CoauthorInfo, WhitelistEntry


def test_select_only_first_corresponding_no_whitelist():
    authors = ["A", "B", "C", "D", "E"]
    roles = {"A": "一作", "E": "通讯"}
    wl = {}
    result = select_authors_for_rm(authors, roles, wl)
    names = [n for n, _ in result]
    assert "A" in names
    assert "E" in names
    assert "B" not in names
    assert "C" not in names


def test_select_includes_whitelist():
    authors = ["A", "B", "C", "D", "E"]
    roles = {"A": "一作", "E": "通讯"}
    wl = {"C": WhitelistEntry(record_id="rec_c", name="C", organization="Princeton")}
    result = select_authors_for_rm(authors, roles, wl)
    names = [n for n, _ in result]
    assert "C" in names


def test_select_includes_cofirst():
    authors = ["A", "B", "C", "D", "E"]
    roles = {"A": "一作", "B": "共一", "E": "通讯"}
    wl = {}
    result = select_authors_for_rm(authors, roles, wl)
    names = [n for n, _ in result]
    assert "A" in names and "B" in names and "E" in names


def test_select_dedup_no_upper_limit():
    """30 作者，含 5 个白名单 + 一作 + 通讯 + 2 共一 → 应该全部上表"""
    authors = [f"P{i}" for i in range(30)]
    roles = {"P0": "一作", "P1": "共一", "P2": "共一", "P29": "通讯"}
    wl = {f"P{i}": WhitelistEntry(record_id=f"r{i}", name=f"P{i}", organization="Org")
          for i in [3, 7, 11, 15, 20]}
    result = select_authors_for_rm(authors, roles, wl)
    selected = {n for n, _ in result}
    expected = {"P0", "P1", "P2", "P29", "P3", "P7", "P11", "P15", "P20"}
    assert selected == expected


def test_enrich_v4_dispatches_to_dual_path():
    """smoke test: enrich_paper_coauthors_v4 调用 anysearch + openalex + merge + verify"""
    with patch(
        "hh_research.extract.researcher_mapping.orchestrator.enrich_via_anysearch",
        return_value=CoauthorInfo(name="Tri Dao", affiliation="Princeton", github="tridao"),
    ), patch(
        "hh_research.extract.researcher_mapping.orchestrator.enrich_via_openalex",
        return_value=CoauthorInfo(name="Tri Dao", affiliation="Princeton University"),
    ), patch(
        "hh_research.extract.researcher_mapping.orchestrator.verify_coauthor",
        side_effect=lambda c: c,  # passthrough
    ), patch(
        "hh_research.extract.researcher_mapping.orchestrator.fetch_arxiv_html",
        return_value="<html/>",
    ), patch(
        "hh_research.extract.researcher_mapping.orchestrator.detect_co_first_authors",
        return_value={"Tri Dao": "一作"},
    ):
        result = enrich_paper_coauthors_v4(
            arxiv_id="2605.18603",
            authors=["Tri Dao"],
            whitelist_match={},
        )
    assert len(result) == 1
    assert result[0].name == "Tri Dao"
    assert "openalex" in result[0].enrich_sources.get("affiliation", [])
