#!/usr/bin/env python3
"""HH Research Daily 2026-06-15 精选版 · form A 卡（晨报体：自然完整句、少标点堆叠、不夸大），默认推本人。"""
import os, sys, json
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_H, "..", "src"))
from dotenv import load_dotenv
load_dotenv(os.path.join(_H, "..", ".env"))
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher

DOC = "https://my.feishu.cn/wiki/VY3vw8aQMiAmn3kkjzKc1oapnhh"
DATE = "2026-06-15"
SELF_EMAIL = "hlguo@hillhouseinvestment.com"
B = {
    "openai": "doxcn75Nc8O15xNOPFHIA3tkoqh",
    "skhynix": "doxcno8pxoH5vmVb7iHiHL8LYSc",
    "qualcomm": "doxcnTVOa9Yds5SDPMwQvmsqHVg",
    "capital": "doxcno56Yt7C2TUnwkLP8GLfaef",
}
def a(k): return f"{DOC}#{B[k]}"

POINTS = ("🔬 **前沿技术**\n"
    f"•  **OpenAI** 成立 Partner Network 并配套 1.5 亿美元，将系统集成商与咨询公司纳入其销售与交付体系，在提供模型之外向企业落地环节延伸。  [↗]({a('openai')})\n"
    f"•  **三星** 5 月底率先送出业界首批 12 层 HBM4E 样品，较龙头 **SK 海力士**领先约半年，后者本月才跟进。HBM 是 AI 加速卡的关键高价值环节之一；海力士正筹划最快 8 月、募资至多 **140 亿美元**赴美上市。  [↗]({a('skhynix')})\n"
    "💰 **资本动向**\n"
    f"•  **Meta** 已切断与 **Manus** 的系统对接，执行北京要求的 **20 亿美元**收购解除；Manus 创始人正寻求约 **10 亿美元**融资以回购公司。  [↗]({a('capital')})")

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
