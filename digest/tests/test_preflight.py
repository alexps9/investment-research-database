"""Task6: preflight 外部服务探测 测试。"""
import socket

from hh_research.utils.preflight import preflight_check


class _FakeSock:
    def close(self):
        pass


def test_all_services_up(monkeypatch):
    monkeypatch.setattr(socket, "create_connection", lambda addr, timeout: _FakeSock())
    assert preflight_check() == []


def test_feishu_down_only(monkeypatch):
    def fake(addr, timeout):
        if "feishu" in addr[0]:
            raise OSError("nodename nor servname")
        return _FakeSock()
    monkeypatch.setattr(socket, "create_connection", fake)
    down = preflight_check()
    assert "feishu" in down and "arxiv" not in down


def test_all_down(monkeypatch):
    def fake(addr, timeout):
        raise OSError("Network is unreachable")
    monkeypatch.setattr(socket, "create_connection", fake)
    assert set(preflight_check()) == {"feishu", "arxiv"}


def test_subset_services(monkeypatch):
    monkeypatch.setattr(socket, "create_connection", lambda addr, timeout: _FakeSock())
    assert preflight_check(services=("arxiv",)) == []
