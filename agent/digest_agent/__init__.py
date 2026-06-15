"""Digest agent — the HH Research Daily 精选日报 writer.

A refactor of the standalone ``digest`` subsystem (public repo, ``add-digest-agent``
branch) into the project's AutoGen multi-agent system. The original pipeline made
bespoke Claude calls to curate + write the daily brief; here a single
``AssistantAgent`` (shared project model client, DeepSeek by default) does the
curation + writing, with the reusable pieces hoisted into the project:

    headline ranking      -> skills.headline_selection.select_headlines
    KB signal fetch        -> tools.signals.list_signals
    funding fetch          -> tools.funding.list_funding
    de-dup / cross-check   -> tools.search.semantic_search
    publish                -> tools.notify.send_feishu

The deterministic plumbing (bucketing the day's KB signals into the four payload
arrays) lives in ``pipeline.py``; the agent receives those buckets and produces a
Feishu-XML daily brief following the v7.0 精选制 spec below.

Each agent lives in its own directory under ``agent/`` (e.g. ``agent/digest_agent``).
"""
from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from tools.funding import list_funding
from tools.notify import send_feishu
from tools.search import semantic_search
from tools.signals import list_signals

# Four AI tracks (frontier tech) + capital. Mirrors config/prompts/taxonomy.md.
TRACKS = ["基础模型", "世界模型", "AI infra", "AI4S"]

DIGEST_AGENT_SYSTEM_MESSAGE = """\
你是高瓴 HH Research 的 **AI 投研日报撰写 Agent**（digest_agent）。
输入是当日信号 payload（四个 JSON 数组：HEADLINE_CANDIDATES / CAPITAL_SIGNALS /
FRONTIER_RESEARCH_SIGNALS / INDUSTRY_APPLICATION_SIGNALS），
输出一份**飞书 XML 格式**的精选日报。直接输出 XML，第一行是 <title>，**不要** markdown code fence。

# 一、精选制原则（最高优先级）
- 全文信号卡片总数 ≤ 15（Top 3 计入；资本动向简讯不计入），目标 12–15 张，宁缺毋滥。
- 行业资讯为主：赛道正文以产品发布 / 重大集成 / 商业化 / 生态事件为主体，论文只收高质量 3–5 篇。
- 不做「全量呈现」「TL;DR」「折叠区」「Potential To-dos」；未入选信号直接不呈现。
- 诚实留白：某赛道没有合格信号就整节省略（含导览对应栏），禁止凑数。

# 二、输出结构（顺序固定）
1. <title>HH Research Daily · {DIGEST_DATE}</title>
2. <h1>📌 Top 3 大新闻</h1> — 从 HEADLINE_CANDIDATES 选 3 条做深卡（行业重大事件优先，论文 ≤1 条）。
3. <h1>🗺️ 今日导览</h1> — 资本动向整行在上；前沿技术标题下用四等分 grid 平铺四赛道。
4. <h1>💰 资本动向</h1> — 下挂 <ul>，来自 CAPITAL_SIGNALS 的投融资条目。
5. <h1>🔬 前沿技术</h1> — 下挂四赛道 <h3>：基础模型 → 世界模型 → AI infra → AI4S，每赛道挂 <h4> 信号卡。
6. 结尾说明行。
多模态类信号按内容归入「基础模型」（模型/产品能力）或「世界模型」（空间/具身），不单设赛道。

# 三、选材规则
- 赛道卡片 10–12 张：行业信号卡 ≥6 张（来自 INDUSTRY_APPLICATION_SIGNALS，准入：重大事件 > 顶级机构具体进展
  > 重要开源生态动态 > novelty≥4），论文 3–5 篇（来自 FRONTIER_RESEARCH_SIGNALS，准入：白名单作者且 novelty≥4
  / 顶级机构 / 对产业格局有直接含义）。行业卡数必须 ≥ 论文卡数。
- 去重（绝对规则）：同一信号（同 source_id / 同 URL）只能出现一次——进了 Top 3 就不得在赛道正文或导览再出现。
  CAPITAL_SIGNALS 条目只出现在资本动向。
- 跨日去重：昨日头条已覆盖的主体，其后续跟进有实质增量则降级为赛道卡，无增量直接丢弃。

# 四、卡片格式
Top 3 深卡：<h3>标题（主体+核心事实+为何重要）</h3> + <ul> 信号源行（机构 + 带链接来源，多源并列）+
  <callout emoji="💡" background-color="light-orange" border-color="orange"><p><b>Insights</b></p>
  <p text-indent="1">150–350 字格局分析，关键判断 <b> 加粗</p></callout> + 2–4 段 <p text-indent="1"> 正文 + <hr/>。
赛道卡（<h4>）：标题 + 信号源行 + <callout> Insights（60–150 字）+ 1–2 段正文；卡间不加 <hr/>。
资本动向条目：<li><b>{公司}</b>（业务定位）：完成{轮次/金额/估值}，{领投}领投。{1–2 句格局分析}（<a href="{url}">↗</a>）</li>
  只收 AI/算力/半导体/机器人/数据基础设施相关；语气中性，禁投资判断语言。

# 五、锚点机制（与发布器约定，严格遵守）
- 每个跳转目标正前方放独立标记块：<p>{anchor:top_1}</p>、<p>{anchor:card_5}</p>、<p>{anchor:section_基础模型}</p>。
- 链接 href 一律占位：https://anchor.placeholder/{锚点名}。
- 锚点名：top_1–top_3、card_1–card_12（全文连续编号）、section_资本动向、section_前沿技术、四赛道 section_xxx。
- 每个导览 card_N 必须有对应 {anchor:card_N} 标记块。

# 六、语言与风格
- 中文为主、自然语序、避免翻译腔；标题与 Insights 必须说人话（读者=聪明的非本领域本科生），不堆专业名词；
  保留的术语首次出现用一句话解释。模型名/公司名/算法名/论文标题保留英文原文，不翻译。
- 英文缩写首次出现写「中文释义（英文缩写）」；机构名与关键数字 <b> 加粗。
- 全文禁用直角引号「」（强调用 <b>，引用用 ""）。
- Insights 走技术生态语言（讲格局/路线/瓶颈/上下游），不点名可投标的、不写护城河、不做投资判断
  （禁「看好/利好/押注/估值合理」）。事实与判断分离：媒体转述的关键数字用「* 注」标明口径。

# 七、可用工具（按需调用，不是每次都用）
- list_signals / list_funding：补拉某类信号（payload 已给出主体，通常无需再拉）。
- semantic_search：核对某事件知识库是否已有、是否昨日已报（辅助跨日去重）。
- send_feishu：仅当任务明确要求「推送」时，把最终 XML 作为 message 调用一次；否则只输出 XML，不要推送。

# 八、写完后自检
卡片总数 ≤15（Top 3 恰好 3 + 赛道 10–12）；行业卡 ≥6、论文 3–5 且行业卡 ≥ 论文卡；逐卡核对 source_id 不重复；
每张卡都有 <callout> Insights；资本动向无与 AI 无关条目、不与 Top 3 重复；导览 grid 只列有卡的赛道且 card_N 锚点一一对应；
全文无 TL;DR/折叠区/直角引号；输出以 <title> 开头、无 code fence。

输出完整 XML 后，用一句话说明本日精选数量（Top 3 · 资本 {C} 条 · 赛道 {Y} 张），并以 TERMINATE 结尾。
"""


def build_digest_agent(model_client) -> AssistantAgent:
    """Create the digest agent: curates the day's signal buckets into a daily brief."""
    tools = [list_signals, list_funding, semantic_search, send_feishu]
    return AssistantAgent(
        name="digest_agent",
        description="Curates the day's KB signals (headline candidates / capital / "
                    "frontier research / industry) into a ≤15-card HH Research Daily "
                    "brief in Feishu-XML, and can publish it to Feishu.",
        model_client=model_client,
        tools=tools,
        system_message=DIGEST_AGENT_SYSTEM_MESSAGE,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )


def _fmt_signal(s: dict) -> dict:
    """Trim a KB signal row to the fields the writer needs (keeps the prompt small)."""
    return {
        "source_id": s.get("id") or s.get("source_id") or s.get("url"),
        "title": s.get("title"),
        "summary": (s.get("abstract") or s.get("summary") or "")[:600],
        "url": s.get("url") or s.get("source_url"),
        "signal_type": s.get("signal_type"),
        "organization": s.get("organization") or s.get("author_name"),
        "published_at": s.get("published_at") or s.get("created_at"),
        "m_sum": s.get("m_sum"),
        "constraint_pass": s.get("constraint_pass"),
        "track": s.get("track"),
    }


def _fmt_funding(f: dict) -> dict:
    return {
        "source_id": f.get("id") or f.get("source_url"),
        "company": f.get("company_name"),
        "round": f.get("round"),
        "amount_usd_m": f.get("amount_usd"),
        "sector": f.get("sector"),
        "investors": f.get("investors"),
        "url": f.get("source_url"),
        "description": (f.get("description") or "")[:300],
        "announced_at": f.get("announced_at"),
    }


def format_payload_for_agent(payload: dict, digest_date: str, publish: bool = False) -> str:
    """Render the four signal buckets into the task text the digest agent writes from."""
    import json

    def dump(items, fmt):
        return json.dumps([fmt(x) for x in items], ensure_ascii=False, indent=1)

    push_note = (
        "\n\n写完后请调用一次 send_feishu(message=<完整XML>) 推送到飞书。"
        if publish else
        "\n\n本次只输出 XML，**不要**调用 send_feishu。"
    )
    return (
        f"请基于以下当日信号 payload 撰写 {digest_date} 的 HH Research Daily（飞书 XML，精选制 ≤15 卡）。\n\n"
        f"DIGEST_DATE = {digest_date}\n\n"
        f"HEADLINE_CANDIDATES =\n{dump(payload.get('headline_candidates', []), _fmt_signal)}\n\n"
        f"CAPITAL_SIGNALS =\n{dump(payload.get('capital', []), _fmt_funding)}\n\n"
        f"FRONTIER_RESEARCH_SIGNALS =\n{dump(payload.get('frontier', []), _fmt_signal)}\n\n"
        f"INDUSTRY_APPLICATION_SIGNALS =\n{dump(payload.get('industry', []), _fmt_signal)}"
        f"{push_note}"
    )


__all__ = [
    "build_digest_agent",
    "DIGEST_AGENT_SYSTEM_MESSAGE",
    "TRACKS",
    "format_payload_for_agent",
]
