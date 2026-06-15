"""verify_coauthor 端到端字段级判定测试"""
from unittest.mock import patch

from hh_research.extract.researcher_mapping.verify_agent import verify_coauthor
from hh_research.storage.schemas import CoauthorInfo


def _fake_facts(name, affs):
    """生成假的 LLM 提取结果."""
    return ({"page_name": name, "page_affiliations": affs, "page_role": "PhD"}, "claude-haiku-4-5")


def test_verify_all_pass():
    candidate = CoauthorInfo(
        name="Tri Dao", affiliation="Princeton",
        github="tridao", homepage="https://tridao.me",
    )
    with patch(
        "hh_research.extract.researcher_mapping.verify_agent.fetch_all_urls",
        return_value={"github": "<html>tridao Tri Dao</html>",
                      "homepage": "<html>Tri Dao Princeton University</html>"},
    ), patch(
        "hh_research.extract.researcher_mapping.verify_agent.extract_page_facts",
        return_value=_fake_facts("Tri Dao", ["Princeton University"]),
    ):
        result = verify_coauthor(candidate)
    assert result.name == "Tri Dao"
    assert result.affiliation == "Princeton"
    assert result.github == "tridao"
    assert result.homepage == "https://tridao.me"
    assert result.verification["affiliation"] == "verified"
    assert result.verification["github"] == "verified"


def test_verify_github_name_mismatch():
    """github URL 返回别人姓名，但 homepage 通过姓名验证 → github 字段级丢弃，整人保留"""
    candidate = CoauthorInfo(
        name="Tri Dao", affiliation="Princeton",
        github="tridao",
        homepage="https://tridao.me",
    )

    def _fake_facts_per_url(url, html, candidate_name):
        # homepage 返回正确姓名；github 返回错误姓名
        if "tridao.me" in url:
            return ({"page_name": "Tri Dao", "page_affiliations": ["Princeton University"], "page_role": "PhD"}, "claude-haiku-4-5")
        return ({"page_name": "Someone Else", "page_affiliations": ["Random Inc"], "page_role": "PhD"}, "claude-haiku-4-5")

    with patch(
        "hh_research.extract.researcher_mapping.verify_agent.fetch_all_urls",
        return_value={
            "github": "<html>Someone Else</html>",
            "homepage": "<html>Tri Dao Princeton University</html>",
        },
    ), patch(
        "hh_research.extract.researcher_mapping.verify_agent.extract_page_facts",
        side_effect=_fake_facts_per_url,
    ):
        result = verify_coauthor(candidate)
    assert result is not None  # 整人保留（homepage 通过了姓名验证）
    assert result.github is None  # 字段级丢弃
    assert result.verification["github"].startswith("rejected:")


def test_verify_name_total_failure_returns_none():
    """所有 URL 上的 page_name 都跟候选不匹配 → 整位作者剔除"""
    candidate = CoauthorInfo(
        name="Tri Dao",
        github="tridao", homepage="https://x.me",
    )
    with patch(
        "hh_research.extract.researcher_mapping.verify_agent.fetch_all_urls",
        return_value={"github": "<html/>", "homepage": "<html/>"},
    ), patch(
        "hh_research.extract.researcher_mapping.verify_agent.extract_page_facts",
        return_value=_fake_facts("Wrong Person", ["Wrong Org"]),
    ):
        result = verify_coauthor(candidate)
    assert result is None


def test_verify_no_urls_returns_candidate_unchanged():
    """没有任何 URL 可验证 → 跳过审查直接返回候选(字段全留)"""
    candidate = CoauthorInfo(name="Tri Dao", affiliation="Princeton")
    result = verify_coauthor(candidate)
    assert result.affiliation == "Princeton"
    assert result.verification.get("affiliation") == "skipped:no_url"


def test_verify_partial_affiliation_match():
    """homepage 给出对的姓名 + 对的机构 → affiliation/homepage 都过；github 没拉到则该字段被丢弃"""
    candidate = CoauthorInfo(
        name="Tri Dao", affiliation="Princeton",
        github="tridao",  # 但 github fetch 失败
        homepage="https://tridao.me",
    )
    with patch(
        "hh_research.extract.researcher_mapping.verify_agent.fetch_all_urls",
        return_value={"homepage": "<html>Tri Dao at Princeton University</html>"},
    ), patch(
        "hh_research.extract.researcher_mapping.verify_agent.extract_page_facts",
        return_value=_fake_facts("Tri Dao", ["Princeton University"]),
    ):
        result = verify_coauthor(candidate)
    assert result.name == "Tri Dao"
    assert result.affiliation == "Princeton"
    assert result.homepage == "https://tridao.me"
    assert result.verification["affiliation"] == "verified"
    assert result.verification["homepage"] == "verified"
    # github URL fetch 没结果 → 字段被丢弃（保守）
    assert result.github is None
    assert result.verification["github"].startswith("rejected:") or \
           result.verification["github"] == "skipped:no_fetch"
