from hh_research.publish.digest_index import extract_digest_meta

OLD_MD = """# HH Research Daily · 2026-05-13

## 今日 TL;DR

今天的焦点是 A 和 B。

## 头条

### 头条一
#### 信号卡一
#### 信号卡二
"""

HTML_LIKE = """<title>HH Research Daily · 2026-06-07 · 主线</title>
<h2>今日 TL;DR</h2><p>HTML 形态的摘要内容。</p>
<h3>信号一</h3><h3>信号二</h3><h3>信号三</h3>
"""


def test_old_markdown():
    m = extract_digest_meta(OLD_MD, fallback_title="x", fallback_date="2026-05-13")
    assert m["title"] == "HH Research Daily · 2026-05-13"
    assert "焦点" in m["tldr"]
    assert m["signal_count"] == 2  # 两个 #### 信号卡


def test_html_like():
    m = extract_digest_meta(HTML_LIKE, fallback_title="x", fallback_date="2026-06-07")
    assert "2026-06-07" in m["title"]
    assert "摘要" in m["tldr"]
    assert m["signal_count"] == 3  # 三个 <h3>


def test_garbage_does_not_raise():
    m = extract_digest_meta("\x00\x01 not real", fallback_title="fb", fallback_date="2026-01-01")
    assert m["title"] == "fb"
    assert m["signal_count"] == 0
