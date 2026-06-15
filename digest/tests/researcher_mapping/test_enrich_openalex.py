"""enrich_openalex.py 单元测试"""
from unittest.mock import patch

from hh_research.extract.researcher_mapping.enrich_openalex import (
    query_paper_by_arxiv_id,
)


def _fake_work(authorships):
    """模拟 pyalex Work 对象。"""
    return {
        "id": "https://openalex.org/W123",
        "display_name": "Some Paper",
        "authorships": authorships,
    }


def test_query_paper_returns_target_author():
    fake_authorship = {
        "author": {"id": "https://openalex.org/A456", "display_name": "Tri Dao",
                   "orcid": "https://orcid.org/0000-0002-0000-0000"},
        "institutions": [
            {"id": "https://openalex.org/I789",
             "display_name": "Princeton University",
             "ror": "https://ror.org/00hx57361"},
        ],
        "is_corresponding": False,
    }
    work = _fake_work([fake_authorship])
    with patch(
        "hh_research.extract.researcher_mapping.enrich_openalex._fetch_work",
        return_value=work,
    ):
        result = query_paper_by_arxiv_id("2605.18603", "Tri Dao")
    assert result is not None
    assert result["display_name"] == "Tri Dao"
    assert result["institutions"][0]["display_name"] == "Princeton University"
    assert result["orcid"] == "https://orcid.org/0000-0002-0000-0000"


def test_query_paper_returns_none_when_no_match():
    fake_authorship = {
        "author": {"id": "x", "display_name": "Someone Else", "orcid": None},
        "institutions": [],
    }
    work = _fake_work([fake_authorship])
    with patch(
        "hh_research.extract.researcher_mapping.enrich_openalex._fetch_work",
        return_value=work,
    ):
        result = query_paper_by_arxiv_id("2605.18603", "Tri Dao")
    assert result is None


def test_query_paper_returns_none_when_paper_not_found():
    with patch(
        "hh_research.extract.researcher_mapping.enrich_openalex._fetch_work",
        return_value=None,
    ):
        result = query_paper_by_arxiv_id("9999.99999", "Anyone")
    assert result is None


import json
from hh_research.extract.researcher_mapping.enrich_openalex import (
    enrich_via_openalex,
)
from hh_research.storage.schemas import CoauthorInfo


def test_enrich_via_openalex_happy_path(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "hh_research.extract.researcher_mapping.enrich_openalex.CACHE_DIR",
        tmp_path,
    )
    fake_data = {
        "display_name": "Tri Dao",
        "orcid": "https://orcid.org/0000-0002-0000-0000",
        "institutions": [
            {"display_name": "Princeton University",
             "ror": "https://ror.org/00hx57361"},
        ],
        "is_corresponding": False,
    }
    with patch(
        "hh_research.extract.researcher_mapping.enrich_openalex.query_paper_by_arxiv_id",
        return_value=fake_data,
    ):
        result = enrich_via_openalex("2605.18603", "Tri Dao")
    assert isinstance(result, CoauthorInfo)
    assert result.name == "Tri Dao"
    assert result.affiliation == "Princeton University"
    assert "openalex" in result.provenance.get("affiliation", "")


def test_enrich_via_openalex_cache_hit(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "hh_research.extract.researcher_mapping.enrich_openalex.CACHE_DIR",
        tmp_path,
    )
    cache_key = "2605.18603:tri dao"
    import hashlib
    sha = hashlib.sha1(cache_key.encode()).hexdigest()
    cache_file = tmp_path / f"{sha}.json"
    cache_file.write_text(json.dumps({
        "display_name": "Tri Dao",
        "orcid": None,
        "institutions": [{"display_name": "Cached Inst", "ror": None}],
        "is_corresponding": False,
    }))
    # query function should NOT be called
    with patch(
        "hh_research.extract.researcher_mapping.enrich_openalex.query_paper_by_arxiv_id",
    ) as mock_q:
        result = enrich_via_openalex("2605.18603", "Tri Dao")
        mock_q.assert_not_called()
    assert result.affiliation == "Cached Inst"


def test_enrich_via_openalex_returns_none_on_total_miss():
    with patch(
        "hh_research.extract.researcher_mapping.enrich_openalex.query_paper_by_arxiv_id",
        return_value=None,
    ), patch(
        "hh_research.extract.researcher_mapping.enrich_openalex.query_author_by_name",
        return_value=None,
    ):
        result = enrich_via_openalex("9999.99999", "Nobody")
    assert result is None
