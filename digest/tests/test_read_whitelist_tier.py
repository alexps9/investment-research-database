"""(a) read_whitelist 应把 tier / entity_type / source_authority 读入 WhitelistEntry。

这三列在 Bitable「信号源」表已存在（select 类型），但运行时模型此前未读取，
导致 tier/entity_type 对采集与头条均无作用。本测试固定"应能读到"的预期。
"""
from hh_research.storage import bitable_client


def _fake_resp(fields, rows, record_ids):
    return {"data": {"fields": fields, "data": rows,
                     "record_id_list": record_ids, "has_more": False}}


def test_read_whitelist_reads_tier_entity_type_source_authority(monkeypatch):
    # Bitable select 字段以 ['x'] 形式返回
    fields = ["名字", "Twitter", "tier", "entity_type", "source_authority"]
    rows = [["OpenAI", "https://x.com/openai", ["P0+"], ["company"], ["official"]]]
    monkeypatch.setattr(bitable_client, "_lark_cli",
                        lambda *a, **k: _fake_resp(fields, rows, ["recTEST01"]))

    entries = bitable_client.read_whitelist(app_token="t", table_id="tbl")

    assert len(entries) == 1
    e = entries[0]
    assert e.tier == "P0+"
    assert e.entity_type == "company"
    assert e.source_authority == "official"


def test_read_whitelist_tier_fields_default_none_when_absent(monkeypatch):
    # 列缺失时应安全降级为 None（不报错）
    fields = ["名字", "Twitter"]
    rows = [["Some Person", "https://x.com/someone"]]
    monkeypatch.setattr(bitable_client, "_lark_cli",
                        lambda *a, **k: _fake_resp(fields, rows, ["recTEST02"]))

    e = bitable_client.read_whitelist(app_token="t", table_id="tbl")[0]

    assert e.tier is None
    assert e.entity_type is None
    assert e.source_authority is None
