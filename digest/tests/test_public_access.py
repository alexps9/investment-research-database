"""set_public_access: 发布后把云文档设为「互联网可读」(anyone_readable)。

互联网可读 = external_access:true + link_share_entity:anyone_readable，type=docx（非 wiki）。
best-effort：失败不抛错、不阻断发布。需 lark-cli 有 docs:permission.setting scope（运行时）。
"""
import json

import hh_research.publish.lark_doc_publisher as pub


def test_set_public_access_sends_anyone_readable(monkeypatch):
    captured = {}

    def fake(*args, **kwargs):
        captured["args"] = args
        return {"ok": True, "code": 0}

    monkeypatch.setattr(pub, "_lark_cli", fake)
    ok = pub.set_public_access("docx_token_123", obj_type="docx")
    assert ok is True
    args = captured["args"]
    assert args[:3] == ("drive", "permission.public", "patch")
    params = json.loads(args[args.index("--params") + 1])
    assert params == {"token": "docx_token_123", "type": "docx"}
    data = json.loads(args[args.index("--data") + 1])
    assert data == {"external_access": True, "link_share_entity": "anyone_readable"}
    assert "--yes" in args  # high-risk-write 需确认


def test_set_public_access_non_blocking_on_error(monkeypatch):
    def boom(*a, **k):
        raise pub.PublishError("rc=1 insufficient scope")
    monkeypatch.setattr(pub, "_lark_cli", boom)
    assert pub.set_public_access("t") is False  # 不抛错（不阻断发布）


def test_set_public_access_returns_false_on_non_ok(monkeypatch):
    monkeypatch.setattr(pub, "_lark_cli", lambda *a, **k: {"ok": False, "error": "denied"})
    assert pub.set_public_access("t") is False


def test_set_public_access_default_objtype_is_docx(monkeypatch):
    captured = {}
    monkeypatch.setattr(pub, "_lark_cli", lambda *a, **k: (captured.update(args=a), {"code": 0})[1])
    pub.set_public_access("t")  # 不传 obj_type
    params = json.loads(captured["args"][captured["args"].index("--params") + 1])
    assert params["type"] == "docx"  # 默认 docx（wiki 不支持 anyone_readable）
