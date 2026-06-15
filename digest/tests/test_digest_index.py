import json
from pathlib import Path

from hh_research.publish.digest_index import load_index, write_index_atomic, upsert_entry


def test_load_missing_returns_empty(tmp_path: Path):
    assert load_index(tmp_path / "nope.json") == []


def test_write_is_sorted_desc_and_atomic(tmp_path: Path):
    p = tmp_path / "idx.json"
    write_index_atomic(p, [{"date": "2026-05-01"}, {"date": "2026-06-01"}])
    rows = json.loads(p.read_text(encoding="utf-8"))
    assert [r["date"] for r in rows] == ["2026-06-01", "2026-05-01"]


def test_upsert_replaces_same_date_and_merges(tmp_path: Path):
    p = tmp_path / "idx.json"
    upsert_entry(p, {"date": "2026-06-07", "signal_count": 10, "tldr": "a"})
    upsert_entry(p, {"date": "2026-06-07", "signal_count": 42})  # same date
    upsert_entry(p, {"date": "2026-06-06", "signal_count": 5})
    rows = json.loads(p.read_text(encoding="utf-8"))
    assert [r["date"] for r in rows] == ["2026-06-07", "2026-06-06"]
    row = next(r for r in rows if r["date"] == "2026-06-07")
    assert row["signal_count"] == 42 and row["tldr"] == "a"  # merged, count overwritten


def test_upsert_requires_date(tmp_path: Path):
    import pytest

    with pytest.raises(ValueError):
        upsert_entry(tmp_path / "idx.json", {"signal_count": 1})
