import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "backfill_digest_index",
    Path(__file__).resolve().parents[1] / "scripts" / "backfill_digest_index.py",
)
bf = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(bf)  # type: ignore


def test_pick_canonical_prefers_plain_md(tmp_path: Path):
    d = tmp_path
    for name in [
        "digest_2026-05-20.md",
        "digest_2026-05-20_v3.md",
        "digest_2026-05-20.xml",
        "digest_2026-05-20.md.bak",
    ]:
        (d / name).write_text("x", encoding="utf-8")
    assert bf.pick_canonical("2026-05-20", d).name == "digest_2026-05-20.md"


def test_pick_canonical_xml_when_no_plain_md(tmp_path: Path):
    (tmp_path / "digest_2026-05-06.xml").write_text("x", encoding="utf-8")
    assert bf.pick_canonical("2026-05-06", tmp_path).name == "digest_2026-05-06.xml"


def test_parse_publisher_log_pairs():
    lines = [
        "2026-06-07 creating wiki node: HH Research Daily · 2026-06-07 · 主线",
        "2026-06-07 ...",
        "2026-06-07 published: https://my.feishu.cn/wiki/MAIN",
        "2026-05-19 creating wiki node: HH Research Daily · 2026-05-19 Our Insights 对比 v1",
        "2026-05-19 published: https://my.feishu.cn/wiki/VAR",
    ]
    pairs = bf.parse_publisher_log_pairs(lines)
    assert pairs[0] == {
        "title": "HH Research Daily · 2026-06-07 · 主线",
        "url": "https://my.feishu.cn/wiki/MAIN",
    }
    assert bf.classify_title(pairs[0]["title"]) == ("2026-06-07", "main")
    assert bf.classify_title(pairs[1]["title"]) == ("2026-05-19", "variant")
