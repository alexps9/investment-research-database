"""Test CoauthorInfo V4 fields backward compat."""
from hh_research.storage.schemas import CoauthorInfo


def test_coauthor_v4_fields_default_empty():
    c = CoauthorInfo(name="Tri Dao")
    assert c.verification == {}
    assert c.enrich_sources == {}


def test_coauthor_v4_fields_populate():
    c = CoauthorInfo(
        name="Tri Dao",
        verification={"affiliation": "verified", "github": "rejected:name_mismatch"},
        enrich_sources={"affiliation": ["anysearch", "openalex"]},
    )
    assert c.verification["github"].startswith("rejected:")
    assert "openalex" in c.enrich_sources["affiliation"]
