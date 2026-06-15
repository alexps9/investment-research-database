"""verify_agent LLM 提取测试（mock Claude API）"""
from unittest.mock import MagicMock, patch

from hh_research.extract.researcher_mapping.verify_agent import (
    extract_page_facts,
    should_upgrade_to_sonnet,
)


def _mock_message(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    msg.usage = MagicMock(input_tokens=100, output_tokens=50, cache_creation_input_tokens=0,
                          cache_read_input_tokens=0)
    return msg


def test_extract_page_facts_happy_path():
    fake_json = '{"page_name": "Tri Dao", "page_affiliations": ["Princeton University"], "page_role": "PhD"}'
    with patch(
        "hh_research.extract.researcher_mapping.verify_agent._call_claude",
        return_value=(_mock_message(fake_json), "claude-sonnet-4-6"),
    ):
        result, model_used = extract_page_facts(
            url="https://github.com/tridao",
            html="<title>tridao</title>",
        )
    assert result["page_name"] == "Tri Dao"
    assert result["page_affiliations"] == ["Princeton University"]
    # Bedrock Haiku 不可用，主跑 Sonnet 4.6（注：fix #bedrock-haiku-na）
    assert model_used == "claude-sonnet-4-6"


def test_extract_page_facts_invalid_json_returns_empty():
    with patch(
        "hh_research.extract.researcher_mapping.verify_agent._call_claude",
        return_value=(_mock_message("not json"), "claude-haiku-4-5"),
    ):
        result, _ = extract_page_facts("https://x", "<html/>")
    assert result == {"page_name": None, "page_affiliations": [], "page_role": None}


def test_should_upgrade_haiku_returned_nulls():
    haiku_out = {"page_name": None, "page_affiliations": [], "page_role": None}
    assert should_upgrade_to_sonnet(haiku_out, html_has_chinese=False, candidate_has_chinese=False) is True


def test_should_upgrade_chinese_candidate():
    haiku_out = {"page_name": "Tianqi Chen", "page_affiliations": ["CMU"], "page_role": None}
    assert should_upgrade_to_sonnet(haiku_out, html_has_chinese=False, candidate_has_chinese=True) is True


def test_should_not_upgrade_happy_case():
    haiku_out = {"page_name": "Tri Dao", "page_affiliations": ["Princeton"], "page_role": "PhD"}
    assert should_upgrade_to_sonnet(haiku_out, html_has_chinese=False, candidate_has_chinese=False) is False
