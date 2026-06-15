import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "sync_web_digest_index",
    Path(__file__).resolve().parents[1] / "scripts" / "sync_web_digest_index.py",
)
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)  # type: ignore


def test_build_entry_with_local_digest(tmp_path: Path):
    dd = tmp_path / "data" / "digests"
    dd.mkdir(parents=True)
    (dd / "digest_2026-06-07.md").write_text(
        "# T\n## 今日 TL;DR\n\n摘要。\n#### s1\n#### s2\n", encoding="utf-8"
    )
    state = {
        "date": "2026-06-07",
        "url": "https://my.feishu.cn/wiki/X",
        "status": "success",
        "digest_local_path": "data/digests/digest_2026-06-07.md",
        "line": "main",
    }
    e = mod.build_entry(state, tmp_path, "pipeline_main")
    assert e["date"] == "2026-06-07"
    assert e["feishu_wiki_url"] == "https://my.feishu.cn/wiki/X"
    assert e["signal_count"] == 2
    assert e["confidence"] == "high"


def test_build_entry_missing_local_digest_degrades(tmp_path: Path):
    state = {
        "date": "2026-06-06",
        "url": "https://my.feishu.cn/wiki/Y",
        "status": "success",
        "digest_local_path": "data/digests/nope.md",
        "line": "main",
    }
    e = mod.build_entry(state, tmp_path, "pipeline_main")
    assert e["signal_count"] == 0 and e["tldr"] == ""
    assert e["confidence"] == "medium"
