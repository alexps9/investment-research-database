"""TDD for hh_research.quality.digest_rules — v7.0 P0 quality gate rules.

Plan reference: /Users/haolinguo/Desktop/2026-05-28-v7-quality-gates.md Task 2.
"""

from hh_research.quality.digest_rules import (
    ReviewSeverity,
    review_xml_text,
    text_len_zh,
)


def test_insight_over_120_is_blocking():
    xml = """
<h2>头条</h2>
<h3>MiniMax-M2:测试标题</h3>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p><b>这是加粗的 takeaway 句</b>,然后是一段超过一百二十字的 Insights,用来模拟模型继续把技术细节、训练配置、benchmark 名称、模型参数规模都塞进同一个段落里,导致行研人员无法快速读出最值得关注的判断。这段文字必须被阻断,因为它已经不是三到四行的投研判断,严重超过 v7.0 P0 quality gate 规定的 120 字硬上限。</p>
</callout>
<p>　　解读第一段。</p>
<p>　　解读第二段。</p>
<table><tr><td><p>RM</p></td></tr></table>
"""
    report = review_xml_text(xml, source="file")
    assert any(
        i.severity == ReviewSeverity.BLOCKING and "Insights 字数" in i.message
        for i in report.issues
    ), f"expected BLOCKING 'Insights 字数' issue, got: {[(i.severity, i.message) for i in report.issues]}"


def test_technical_model_scale_number_is_blocking():
    xml = """
<h2>头条</h2>
<h3>MiniMax-M2:测试标题</h3>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p><b>这条信号说明国产 agent 模型正在补齐训练闭环</b>,但 229.9B 参数和 9.8B 激活参数不应进入 Insights,应放在解读正文。</p>
</callout>
<p>　　解读第一段。</p>
<p>　　解读第二段。</p>
<table><tr><td><p>RM</p></td></tr></table>
"""
    report = review_xml_text(xml, source="file")
    assert any(
        "技术细节数字" in i.message for i in report.issues
    ), f"expected '技术细节数字' issue (229.9B), got: {[i.message for i in report.issues]}"


def test_impact_number_is_allowed():
    xml = """
<h2>头条</h2>
<h3>招聘算法:测试标题</h3>
<callout emoji="💡" background-color="light-orange" border-color="orange">
  <p><b>Insights</b></p>
  <p><b>招聘算法的风险不只在单一雇主,而在同一供应商被市场反复复用</b>;Black 求职者 25.87% 申请受损这一数字直接指向监管压力。</p>
</callout>
<p>　　解读第一段。</p>
<p>　　解读第二段。</p>
<table><tr><td><p>RM</p></td></tr></table>
"""
    report = review_xml_text(xml, source="file")
    assert not any(
        "25.87" in i.message for i in report.issues
    ), f"impact number 25.87% should be allowed (求职者/监管 context), got: {[i.message for i in report.issues]}"


def test_feishu_rendered_missing_callout_colors_warns_only():
    """Feishu docx 渲染后 callout color attribute 会丢失（fall back rgb 数值），
    review agent 不应该阻断 — 只警告。
    """
    xml = """
<h2>头条</h2>
<h3>测试标题</h3>
<callout emoji="💡">
  <p><b>Insights</b></p>
  <p><b>这条信号改变的是跟踪框架</b>,不是模型参数大小;后续应观察真实客户场景是否验证。</p>
</callout>
<p>　　解读第一段。</p>
<p>　　解读第二段。</p>
<table><tr><td><p>RM</p></td></tr></table>
"""
    report = review_xml_text(xml, source="feishu")
    assert not report.has_blocking, f"feishu source should not block on missing callout colors, got blocking: {[i.message for i in report.issues if i.severity == ReviewSeverity.BLOCKING]}"
    assert any(
        i.severity == ReviewSeverity.WARNING and "callout" in i.message
        for i in report.issues
    ), f"expected WARNING about callout, got: {[(i.severity, i.message) for i in report.issues]}"


def test_text_len_zh_strips_tags_and_spaces():
    assert text_len_zh("<p><b>判断</b> 123 </p>") == len("判断123")
