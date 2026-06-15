#!/usr/bin/env python3
"""HH Research Daily 2026-06-10 精选版 · form A 卡（咖啡句 + 今日要点 + docx 锚点），默认推本人。"""
import os, sys, json
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_H, "..", "src"))
from dotenv import load_dotenv
load_dotenv(os.path.join(_H, "..", ".env"))
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher

DOC = "https://my.feishu.cn/wiki/MZHnwCDmaioE4ZkWhwdcEVxGnwf"
DATE = "2026-06-10"
SELF_EMAIL = "hlguo@hillhouseinvestment.com"  # 本人在 hres-bot 应用下的 email（FEISHU_BOT_RECIPIENT_OPENIDS 首位）
B = {
    "fable5": "doxcn72RFBXfwFGAGbFTJ1fPM6f",
    "gemini": "doxcn3nuiAnRKst6SBU75F5u2ph",
    "worlddp": "doxcnhMLt3h1ZXLtf9Rxvgil2xf",
    "capital": "doxcnbf10R2GDMVuEgkCY0Lg2Be",
}
def a(k): return f"{DOC}#{B[k]}"

# 卡片按两大类分组：💰 资本动向 / 🔬 前沿技术
POINTS = ("💰 **资本动向**\n"
    f"•  **Sandstone** 完成 3000 万美元 A 轮，Lightspeed 领投——企业内部法务 AI 成法律科技资本下一个重点方向  [↗]({a('capital')})\n"
    "🔬 **前沿技术**\n"
    f"•  Anthropic 正式发布 **Claude Fable 5**：首个公开的 Mythos 级模型，$10/$50 定价、100 万 token 上下文，能力越代跃升同时首次给模型装上会拒绝的安全分类器  [↗]({a('fable5')})\n"
    f"•  **Google 发布 Gemini 3.5 Live Translate**：70+ 语言端到端实时语音翻译、保留语调语速，产品与 API 同日上线  [↗]({a('gemini')})\n"
    f"•  **Yann LeCun 团队 WorldDP**：世界模型负责想清楚、扩散策略负责做精准，分层操控在多阶段机器人任务上一致超越基线  [↗]({a('worlddp')})")

def card_a():
    return {
        "config": {"wide_screen_mode": True},
        "header": {"template": "blue", "title": {"tag": "plain_text", "content": f"HH Research Daily · {DATE}"}},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": "☕️ 一杯咖啡的时间，带您了解今日 AI 资讯"}},
            {"tag": "div", "text": {"tag": "lark_md", "content": POINTS}},
            {"tag": "hr"},
            {"tag": "action", "actions": [{"tag": "button", "text": {"tag": "plain_text", "content": "查看完整日报 →"}, "type": "primary", "url": DOC}]},
        ],
    }

def main():
    to = sys.argv[sys.argv.index("--to") + 1] if "--to" in sys.argv else SELF_EMAIL
    card = card_a()
    if "--send" not in sys.argv:
        print(json.dumps(card, ensure_ascii=False, indent=2)); print("\n预览（未发）。--send 推给", to); return
    r = FeishuBotPublisher().send_card_to_recipients([to], card)
    print("form A:", "✅ sent" if r.get("sent") else "✗ failed", r)

if __name__ == "__main__":
    main()
