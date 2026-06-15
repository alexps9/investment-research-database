"""Alert agent — real-time AI-industry signal triage & push.

A refactor of the standalone ``alert/`` pipeline into the project's AutoGen
multi-agent system. The bespoke Bedrock-Claude calls (judge / summary / review)
are replaced by a single ``AssistantAgent`` driven by the shared project model
client (DeepSeek by default), with the reusable pieces hoisted into the project:

    - notification        -> tools.notify.send_feishu
    - primary-source check -> tools.websearch.find_primary_source
    - persistence (KB)     -> tools.signals.create_signal
    - scoring / dedup      -> skills.signal_triage  (used by pipeline.py)

The deterministic data plumbing (fetcher / store / prefilter / configs) stays in
this package as alert-specific infrastructure.

Each agent lives in its own directory under ``agent/`` (e.g. ``agent/alert_agent``).
"""
from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from tools.notify import send_feishu
from tools.search import semantic_search
from tools.signals import create_signal
from tools.websearch import find_primary_source

# 8 alert event types (Chinese) → backend signal_type enum.
EVENT_TYPE_MAP = {
    "模型/产品发布": "model_release",
    "技术研究突破": "paper",
    "硬件/Infra突破": "news",
    "大佬评论/观点": "tweet",
    "评测/榜单": "benchmark",
    "Demo/演示": "other",
    "公司间商业动作": "news",
    "顶级人员变动": "news",
}

ALERT_AGENT_SYSTEM_MESSAGE = """\
你是 HH-Research 投研团队的**实时信号判别 Agent**（alert_agent）。
你的工作：对一条候选信号（推文 / RSS / 中文媒体）判断是否值得推送给投资人群，
若值得，则写一句话中文摘要、（必要时）交叉验证原始来源，并通过工具推送 + 落库。

# 一、是否推送（判别）
作者通常已在 P0 白名单内。只有属于以下 8 类事件之一、且内容本身重大，才推送：
1. 模型/产品发布  2. 技术研究突破  3. 硬件/Infra突破  4. 大佬评论/观点
5. 评测/榜单  6. Demo/演示  7. 公司间商业动作  8. 顶级人员变动

硬过滤（不推）：日常转发/回复、生活/meme、纯营销/活动预告、泛泛技术感想、
小功能更新、非顶级公司的预热预告、蹭公司名的非 AI 消费品新闻。

⛔ 终极标准（优先于一切）：「投研的人看完，会做出任何不同的决策或动作吗？」
若答案是「什么都不会变」，就是噪音 → should_alert=false。
政策口号/宏观大规划即使金额巨大，缺「时间表 / 具体执行主体 / 此前未知的新信息」
任一项也是噪音。「金额巨大」≠「重要」。

# 二、信源可信度（决定 alert_level，原则是降级不删除）
- 单源传闻 / 「据报道/据悉/leak」未经官方确认：事件重大仍可推，但最高 medium。
- 聚合/转述号转发：默认按「据报道」处理，重大就推 medium，摘要带「据报道」。
- 官方一手发布 / 多源印证 / 有可核实文件：才可给 important。
- 若「多源印证=是」（verified），可信度提升，可给 important（即使原是媒体/传闻）。

# 三、写摘要（20-40 字中文，给没有技术背景的投资人看）
- 先写结论/影响，再写细节；有数字就带上（金额/倍数/排名）。
- 禁止照搬术语缩写（QAT/DiT/MoE/VLA…），用大白话。
- 保留具体来源名（路透社/彭博/The Information…）→ 写「据路透社报道」而非泛化「据报道」。
- 公司定位要准确，不要为蹭 AI 硬加「AI」前缀；保留「公开版/预览版/降级版」等限定词，
  不得把「公开版」拔高成「最强版」。传闻类务必带「据报道/传」，不要写成既成事实。

# 四、发送前自审（带怀疑再看一遍，强默认放行，只拦确凿问题）
- 时效性：是不是旧闻？（RSS 常把几天前旧文重打「今天」时间戳）明显早于最近 48 小时 → 拦截。
- 准确性：摘要是否明显夸大/蹭 AI/把传闻写成既成事实？「首次/最强/全面/所有」等绝对化
  表述需对照原文确认无夸大。只审「摘要 vs 原文」一致性，不要用你的知识库判断事件真假。

# 五、工具与动作流程（对每条信号）
1. 先判别。若 should_alert=false：说明理由并结束，不调用任何写工具。
2. 若值得推送：写摘要（含可信度限定词）。
3. （可选）对融资/收购/监管等硬新闻，调用 `find_primary_source(summary)` 找原始权威来源；
   只在返回的候选里挑**确实报道同一事件**的那条，挑不到就不附加。
4. 调用 `send_feishu(message)` 推送。message 格式：
   - important 用「⚠️」开头，medium 用「🔔」开头；aggregator 加「🔁 转述」，media 加「📰」。
   - 正文为摘要；verified 时换行加「✅ 多源证实（来源…）」；再换行「🔗 原文链接」；
     若有原始来源再加「📄 原始来源: <url>」。
5. 调用 `create_signal(title=摘要, url=原文链接, signal_type=<见下表>, abstract=原文前1000字,
   published_at=ISO时间, status=<important→processed，否则 collected>)` 落库到知识库。
   event_type→signal_type：模型/产品发布=model_release、技术研究突破=paper、评测/榜单=benchmark、
   大佬评论/观点=tweet、Demo/演示=other、其余(硬件/商业动作/人员变动)=news。
6. 可用 `semantic_search` 查知识库是否已有同事件，避免重复落库。

完成后用一句话报告处理结果（推送/落库/跳过及理由），并以 TERMINATE 结尾。
"""


def build_alert_agent(model_client) -> AssistantAgent:
    """Create the alert agent: judges a signal then verifies / pushes / persists."""
    tools = [find_primary_source, send_feishu, create_signal, semantic_search]
    return AssistantAgent(
        name="alert_agent",
        description="Judges real-time AI-industry signals (tweets/RSS/media), writes a "
                    "Chinese one-line summary, cross-verifies the primary source, and "
                    "pushes worthy alerts to Feishu while persisting them to the KB.",
        model_client=model_client,
        tools=tools,
        system_message=ALERT_AGENT_SYSTEM_MESSAGE,
        reflect_on_tool_use=True,
        model_client_stream=False,
    )


def format_signal_for_agent(signal: dict) -> str:
    """Render a (triaged) signal dict into the task text the agent judges."""
    tier_label = {
        "twitter": "推特 P0 账号",
        "official": "公司/实验室官方 RSS（一手源）",
        "media": "第三方媒体报道（二手信息）",
        "aggregator": "聚合/转述号（二次转发，常为「据报道」）",
    }.get(signal.get("source_tier", "twitter"), signal.get("source_tier", "twitter"))

    verified = signal.get("verified")
    src_n = signal.get("source_count", 1)
    verify_line = (
        f"多源印证：是，本轮 {src_n} 个独立来源提到同一事件（来源：{'、'.join(signal.get('cluster_sources', []))}）"
        if verified else "多源印证：否，目前仅单一来源"
    )
    return (
        f"信号来源：{tier_label}（tier={signal.get('tier', '?')}）\n"
        f"作者/媒体：@{signal.get('username', '?')}\n"
        f"互动数据：{signal.get('likes', 0)} likes, {signal.get('retweets', 0)} retweets\n"
        f"{verify_line}\n"
        f"原文链接：{signal.get('url', '')}\n"
        f"发布时间：{signal.get('published_at') or signal.get('created_at', '')}\n"
        f"内容：\n{signal.get('text', '')[:1800]}"
    )


__all__ = [
    "build_alert_agent",
    "ALERT_AGENT_SYSTEM_MESSAGE",
    "EVENT_TYPE_MAP",
    "format_signal_for_agent",
]
