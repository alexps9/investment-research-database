#!/usr/bin/env python3
"""HH Research Daily 2026-06-13 精选版 · form A 卡（咖啡句 + 两大类要点 + docx 锚点），默认推本人。
文案口径：专业投研晨报体——动词准确、每条两句递进、判断克制、少标点堆叠（见 feedback_card_copy_natural_language）。"""
import os, sys, json
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_H, "..", "src"))
from dotenv import load_dotenv
load_dotenv(os.path.join(_H, "..", ".env"))
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher

DOC = "https://my.feishu.cn/wiki/VeNvwXznziawPAkLBkTcoT0Pn3b"
DATE = "2026-06-13"
SELF_EMAIL = "hlguo@hillhouseinvestment.com"
B = {
    "spacex": "doxcn6Xc6u1Ms0UsX6c9gTH0Kcb",
    "anthropic": "doxcnyVVIM6r7KLoDJQEvj1Vdrd",
    "legg": "doxcnZcT4XHfA3Zoeb3u1XoYSog",
    "capital": "doxcneRs7g27L8ybXfwJorKqqgb",
}
def a(k): return f"{DOC}#{B[k]}"

POINTS = ("🔬 **前沿技术**\n"
    f"•  **SpaceX**（纳斯达克 SPCX）首日大涨 19% 完成史上最大 IPO。对 AI 投研真正的看点不在规模，而在它今年已并入 xAI：公开市场第一次有了可交易的前沿 AI 敞口，但只占约两成（其余是火箭与 Starlink）。这把 xAI 标到约 2500 至 4500 亿美元，低于仍在私募的 OpenAI 与 Anthropic，也为后续 AI 公司上市定了第一个锚。  [↗]({a('spacex')})\n"
    f"•  美国政府以国家安全为由下达出口管制指令，勒令 **Anthropic** 全面停用旗舰模型 Fable 5 与 Mythos 5，所有客户即刻受影响。一款正在服务数亿用户的商用模型因一纸指令一夜关停，前沿 AI 的监管尾部风险第一次变成现实。  [↗]({a('anthropic')})\n"
    f"•  **DeepMind** 联合创始人 Shane Legg 发布从通用人工智能迈向超级智能的路线图，梳理出四条可能路径。他特别提醒，多个专业智能体协作涌现的潜力，是当前研究界最被低估的一条。  [↗]({a('legg')})\n"
    "💰 **资本动向**\n"
    f"•  欧洲开源模型龙头 **Mistral** 据传正在募集 **30 亿欧元**，估值有望翻倍至 200 亿欧元。若消息属实，意味着资本对头部开源模型公司的热情并未退潮，欧洲 AI 的估值水平正加速向美国看齐。  [↗]({a('capital')})")

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
