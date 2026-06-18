"""Task1: publish_edited_digest 手工发布 state 写回闭环 测试。

验证手工编辑发布路径写出的 state 与自动主线 (run_daily_pipeline_main.sh) 同 schema，
让 broadcast_today_main.sh 能正常消费（依赖 url/digest_local_path/date/line/status）。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from publish_edited_digest import build_state_payload, write_final_state  # noqa: E402


def test_build_state_payload_main_full_schema():
    p = build_state_payload(
        line="main",
        date="2026-06-02",
        url="https://my.feishu.cn/wiki/ABC123",
        node_token="ABC123",
        digest_local_path="data/digests/digest_2026-06-02.md",
        title="HH Research Daily · 2026-06-02",
    )
    # 与自动路径同字段
    assert p["date"] == "2026-06-02"
    assert p["url"] == "https://my.feishu.cn/wiki/ABC123"
    assert p["status"] == "success"
    assert p["line"] == "main"
    assert p["digest_local_path"] == "data/digests/digest_2026-06-02.md"
    assert "completed_at" in p and p["completed_at"]
    # 手工路径专属标记
    assert p["source"] == "manual_edit"
    assert p["node_token"] == "ABC123"
    assert p["title"] == "HH Research Daily · 2026-06-02"


def test_build_state_payload_completed_at_is_tz_aware_iso():
    p = build_state_payload(
        line="main", date="2026-06-02", url="u", node_token="n",
        digest_local_path="d.md", title="t",
    )
    # ISO8601 带时区偏移（对齐 `date -Iseconds`），可被 fromisoformat 解析
    from datetime import datetime
    parsed = datetime.fromisoformat(p["completed_at"])
    assert parsed.tzinfo is not None


def test_write_final_state_main_targets_last_digest_main(tmp_path):
    p = build_state_payload(
        line="main", date="2026-06-02",
        url="https://my.feishu.cn/wiki/ABC123", node_token="ABC123",
        digest_local_path="data/digests/digest_2026-06-02.md", title="t",
    )
    target = write_final_state("main", p, state_dir=tmp_path)
    assert target == tmp_path / "last_digest_main.json"
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["url"] == "https://my.feishu.cn/wiki/ABC123"
    assert data["line"] == "main"
    assert data["source"] == "manual_edit"
    assert data["digest_local_path"] == "data/digests/digest_2026-06-02.md"


def test_write_final_state_sub_targets_last_digest(tmp_path):
    p = build_state_payload(
        line="sub", date="2026-06-02",
        url="https://my.feishu.cn/wiki/SUB1", node_token="SUB1",
        digest_local_path="data/digests/digest_2026-06-02.md", title="t",
    )
    target = write_final_state("sub", p, state_dir=tmp_path)
    assert target == tmp_path / "last_digest.json"
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["url"] == "https://my.feishu.cn/wiki/SUB1"


def test_write_final_state_idempotent_same_url(tmp_path):
    """幂等：同 url 重跑，url/line/digest_local_path 不变（completed_at 可不同）。"""
    p = build_state_payload(
        line="main", date="2026-06-02", url="https://my.feishu.cn/wiki/X",
        node_token="X", digest_local_path="d.md", title="t",
    )
    t1 = write_final_state("main", p, state_dir=tmp_path)
    d1 = json.loads(t1.read_text(encoding="utf-8"))
    t2 = write_final_state("main", p, state_dir=tmp_path)
    d2 = json.loads(t2.read_text(encoding="utf-8"))
    assert d1["url"] == d2["url"] == "https://my.feishu.cn/wiki/X"
    assert d1["line"] == d2["line"] == "main"
    assert d1["digest_local_path"] == d2["digest_local_path"]


def test_write_final_state_rejects_bad_line(tmp_path):
    p = build_state_payload(
        line="main", date="2026-06-02", url="u", node_token="n",
        digest_local_path="d.md", title="t",
    )
    import pytest
    with pytest.raises(ValueError):
        write_final_state("bogus", p, state_dir=tmp_path)
