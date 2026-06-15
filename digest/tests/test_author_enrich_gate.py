"""Task5: regenerate author-enrich 提速门控 测试。

author coauthor enrich（AnySearch + arxiv HTML + 飞书逐篇）是 regenerate 最慢步。
预览(不发布)默认跳过以提速；正式发布默认做(保署名质量)；--skip-author-enrich 强制跳过。
"""
from hh_research.extract.daily_writer import should_enrich_authors


def test_preview_skips_author_enrich():
    assert should_enrich_authors(publish=False, skip_flag=False) is False


def test_publish_does_author_enrich():
    assert should_enrich_authors(publish=True, skip_flag=False) is True


def test_skip_flag_overrides_publish():
    assert should_enrich_authors(publish=True, skip_flag=True) is False


def test_preview_with_skip_still_skips():
    assert should_enrich_authors(publish=False, skip_flag=True) is False
