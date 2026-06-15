"""Task6: 启动前 preflight — 探测关键外部服务可达性。

避免在飞书 / arxiv / 网络不可用时跑完整 pipeline 并发布残缺日报（6-02 事故根因之一：
DNS 挂导致 arxiv 全 0 + 飞书读 whitelist 失败，却仍生成并发布）。
"""
from __future__ import annotations

import socket

from .logger import get_logger

log = get_logger("preflight")

_HOSTS: dict[str, tuple[str, int]] = {
    "feishu": ("open.feishu.cn", 443),
    "arxiv": ("arxiv.org", 443),
}


def preflight_check(*, services: tuple[str, ...] = ("feishu", "arxiv"),
                    timeout: float = 5.0) -> list[str]:
    """探测各服务 TCP 可达性（DNS + 连接）。返回不可达的服务名列表（空 = 全部可达）。

    用 TCP 连接而非 HTTP，快速且能直接 catch 6-02 那类 DNS 解析失败
    （nodename nor servname）。
    """
    down: list[str] = []
    for svc in services:
        host, port = _HOSTS[svc]
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
        except OSError as e:
            log.warning("preflight: %s (%s:%d) unreachable: %s", svc, host, port, e)
            down.append(svc)
    return down
