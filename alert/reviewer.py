"""Pre-send reviewer (迭代 G).

A final independent review pass before pushing — the "review" step in the agent
loop that judge/summary lack. judge/summary look *forward* (should this alert? how
to phrase?); the reviewer looks *back* with skepticism at the finished alert and
catches what slipped through:

  1. 时效性 — is this actually old news? (RSS often re-timestamps stale posts to "today")
  2. 重复性 — same event as something pushed recently?
  3. 准确性 — does the summary exaggerate / mislabel / contradict the source?
  4. 够格性 — is it really worth an outward push to the group?

Outward-facing pushes are costly to get wrong, so this extra gate is worth the
one LLM call. Failure-safe: if the review call fails, default to ALLOW (don't let
a flaky LLM block real alerts) — the upstream judge already approved it.
"""

import time
from datetime import datetime, timezone

from classifier import _call_llm

REVIEW_PROMPT = """你是投研 Alert 的终审编辑。一条新闻已通过初判、写好摘要，准备推送到投资人群。
你的职责是「带着怀疑再看一遍」，但**不要重复前面已做的判断**——是否够格、是否重大，
初判已经把过关了，你默认尊重。你只拦**确凿**的问题，重点是第 1 项时效性：

1.【主审】时效性：这是不是旧闻？
   - RSS 经常把几天前的旧文重新打上「今天」的时间戳。看摘要/正文里的事件线索
     （「上周」「6月初」「数天前」「已于X日发布」「Published June X」或明显更早的事）。
   - 当前时间：{now}。若内容描述的事件明显早于最近 48 小时 → 判旧闻，拦截。这是你最主要的任务。
2. 重复性：摘要是否明显是最近反复推过的同一事件？（不确定就放行）
3. 准确性：摘要是否明显夸大、蹭「AI」标签、把传闻写成既成事实？
   重点审查：
   - 摘要含「首次」「最强」「全面」「所有」等绝对化表述时：对照原文，原文是否真的说了这么绝对？
     例：原文说"公开版/降级版"，摘要写成"开放最强模型" → 夸大，拦截。
   - 产品层级关系：原文区分了"公开版 vs 完整版"、"预览版 vs 正式版"，摘要是否模糊了这个区别？
   - 公司定位：原文没说"AI公司"，摘要是否自行加了"AI"前缀？
   ⚠️ 只审「摘要 vs 原文」一致性，不要用你自己的知识库判断事件真假，也不要因
   「正文简短/信息少」就拦截——简短不是问题，旧闻和失实才是。官方/媒体说发布了就当发布了，
   即使你没听说过这个产品（新发布本就在你训练数据之后）。

返回严格 JSON：
{{"approve": true/false, "reason": "一句话说明（尤其拦截时必须说清原因）"}}

强默认放行。只在【确凿旧闻】或【明显失实/夸大】时 approve=false；任何犹豫都放行。"""


def review_alert(tweet: dict, classification: dict) -> dict:
    """Return {"approve": bool, "reason": str}. Defaults to approve on any failure."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    summary = classification.get("summary", "")
    level = classification.get("alert_level", "")
    etype = classification.get("event_type", "")
    tier = tweet.get("source_tier", "twitter")

    created_at = tweet.get("created_at", "")
    date_hint = f"\n信号发布时间（RSS/Twitter 标注）：{created_at}" if created_at else ""

    user_msg = f"""信号来源：{tier}
事件类型：{etype}　优先级：{level}{date_hint}
摘要：{summary}

原始内容（含正文，注意其中的时间线索）：
{tweet.get('text', '')[:1500]}"""

    result = _call_llm(REVIEW_PROMPT.format(now=now), user_msg)
    if not result or "approve" not in result:
        # Flaky LLM shouldn't block a real alert the judge already approved.
        return {"approve": True, "reason": "review unavailable, default allow"}
    return {"approve": bool(result.get("approve")), "reason": result.get("reason", "")}
