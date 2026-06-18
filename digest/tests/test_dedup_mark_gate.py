"""Task4: dedup mark 绑定 Bitable 写入成功 测试。

6-02 frontier=0 根因：--skip-bitable-write 的 replay/test 跑仍无条件 mark dedup，
污染生产去重、吃掉 11 篇 arxiv。正确边界：仅写库成功且非 skip 才 mark。
"""
from hh_research.pipeline.daily import should_mark_dedup


def test_skip_bitable_write_never_marks():
    # replay/dry-run/test：绝不 mark（即使"写成功"也不该，因为根本没写）
    assert should_mark_dedup(skip_bitable_write=True, write_succeeded=True) is False
    assert should_mark_dedup(skip_bitable_write=True, write_succeeded=False) is False


def test_normal_write_success_marks():
    assert should_mark_dedup(skip_bitable_write=False, write_succeeded=True) is True


def test_write_failure_does_not_mark():
    # 写库异常 → 不 mark，retry-safe（下次重试不被去重吃掉）
    assert should_mark_dedup(skip_bitable_write=False, write_succeeded=False) is False
