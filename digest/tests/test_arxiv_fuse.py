"""Task3: arxiv 质量熔断判定 测试。

Codex P1 口径（避免误杀「当天有新论文但无白名单命中」）：
- 双网络错误（network_error 且 matched==0）→ block（阻止自动发布）。
- html_candidates>0 且 matched==0 → degraded/warn（不直接 block）。
- html_candidates==0（空窗口）或 matched>0 → 放行。
- 仅 category 模式判定；author 模式无 html_candidates 口径，跳过。
"""
from hh_research.pipeline.daily import check_arxiv_fuse


def test_block_on_network_error_and_zero_matched():
    r = check_arxiv_fuse(html_candidates=0, matched=0, network_error=True, arxiv_mode="category")
    assert r is not None and r[0] == "block"


def test_degraded_on_candidates_but_zero_matched():
    r = check_arxiv_fuse(html_candidates=50, matched=0, network_error=False, arxiv_mode="category")
    assert r is not None and r[0] == "degraded"


def test_pass_on_empty_window():
    # candidates==0 且无网络错误 → 周末/短窗口本就无新论文，放行不误杀
    assert check_arxiv_fuse(html_candidates=0, matched=0, network_error=False,
                            arxiv_mode="category") is None


def test_pass_on_normal_collection():
    assert check_arxiv_fuse(html_candidates=50, matched=11, network_error=False,
                            arxiv_mode="category") is None


def test_author_mode_always_passes():
    # author 模式无 html metrics 口径，跳过判定（不误判）
    assert check_arxiv_fuse(html_candidates=0, matched=0, network_error=True,
                            arxiv_mode="author") is None


def test_network_blip_with_matches_not_blocked():
    # 有匹配（部分成功）即使有网络抖动也不 block
    assert check_arxiv_fuse(html_candidates=50, matched=5, network_error=True,
                            arxiv_mode="category") is None


def test_candidates_zero_matched_zero_with_network_error_blocks_not_degrades():
    # 双网络错误优先级高于 degraded：network_error+matched0 → block（即便 candidates=0）
    r = check_arxiv_fuse(html_candidates=0, matched=0, network_error=True, arxiv_mode="category")
    assert r[0] == "block"
