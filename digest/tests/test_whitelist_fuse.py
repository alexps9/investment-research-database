"""Task2: whitelist 熔断 测试。

read_whitelist 读失败/过少时，pipeline 必须 abort（不进采集/extract/publish/notify），
而不是吞异常置 [] 继续生成残缺版（6-02 事故根因）。
"""
from hh_research.pipeline.daily import WHITELIST_MIN, check_whitelist_fuse


def test_fuse_on_read_failure():
    # 读取失败（异常）→ 必熔断，即使拿到的 count 看似够
    assert check_whitelist_fuse(0, min_count=300, read_failed=True) is not None
    assert check_whitelist_fuse(350, min_count=300, read_failed=True) is not None


def test_fuse_on_empty():
    assert check_whitelist_fuse(0, min_count=300) is not None


def test_fuse_on_too_few():
    assert check_whitelist_fuse(299, min_count=300) is not None


def test_pass_on_sufficient():
    assert check_whitelist_fuse(347, min_count=300) is None


def test_pass_on_exactly_min():
    assert check_whitelist_fuse(300, min_count=300) is None


def test_default_min_reasonable_for_main_baseline():
    # main 基线 347 条；阈值应 0 < MIN <= 347（不误杀正常、能挡归零/部分读取）
    assert 0 < WHITELIST_MIN <= 347


def test_reason_is_descriptive():
    r = check_whitelist_fuse(0, min_count=300, read_failed=True)
    assert isinstance(r, str) and r  # 非空原因字符串，便于日志/告警
