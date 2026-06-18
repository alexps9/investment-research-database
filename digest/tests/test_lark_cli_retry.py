"""Task6: _lark_cli 只读命令重试 + 总超时预算 测试。

读失败（网络/DNS）时只读命令退避重试，受总超时预算约束；写命令不重试（避免重复写）。
"""
import subprocess
import time

import pytest

from hh_research.storage.bitable_client import LarkCLIError, _lark_cli


class _FakeFail:
    returncode = 1
    stdout = ""
    stderr = "nodename nor servname"


class _FakeOK:
    returncode = 0
    stdout = '{"data": {}}'
    stderr = ""


def test_read_command_retries(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: (calls.append(cmd), _FakeFail())[1])
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setenv("HH_LARK_READ_ATTEMPTS", "3")
    with pytest.raises(LarkCLIError):
        _lark_cli("base", "+record-list", "--base-token", "x")
    assert len(calls) == 3  # 只读命令重试 3 次


def test_write_command_no_retry(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: (calls.append(cmd), _FakeFail())[1])
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setenv("HH_LARK_READ_ATTEMPTS", "3")
    with pytest.raises(LarkCLIError):
        _lark_cli("base", "+record-batch-create", "--base-token", "x")
    assert len(calls) == 1  # 写命令不重试（避免重复写）


def test_read_command_succeeds_first_try(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: (calls.append(cmd), _FakeOK())[1])
    out = _lark_cli("base", "+record-list", "--base-token", "x")
    assert out == {"data": {}}
    assert len(calls) == 1  # 成功不重试


def test_total_budget_caps_retries(monkeypatch):
    """总超时预算耗尽则停止重试（即使 attempts 还没用完）。"""
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: (calls.append(cmd), _FakeFail())[1])
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setenv("HH_LARK_READ_ATTEMPTS", "20")
    monkeypatch.setenv("HH_LARK_TOTAL_BUDGET_S", "0")  # 预算 0 → 第一次失败后即停
    with pytest.raises(LarkCLIError):
        _lark_cli("base", "+record-list", "--base-token", "x")
    assert len(calls) == 1  # 预算耗尽，不再重试
