#!/usr/bin/env python3
"""HH Research Daily 2026-06-09 精编版 · form A 卡（咖啡句+说人话要点+docx锚点），默认推本人。"""
import os, sys, json
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_H, "..", "src"))
from dotenv import load_dotenv
load_dotenv(os.path.join(_H, "..", ".env"))
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher

DOC = "https://my.feishu.cn/docx/GCIFdrXWkoRSGgxiw13c8a3Gnqe"
DATE = "2026-06-09"
B = {
    "apple": "doxcnP2UU1YT67Xqxy00fg2f52e",
    "openai": "doxcnTazXYv5YZVJJFzSI3b1fne",
    "limmt": "doxcn1MaNYsCOxCABUdBgHEMPbd",
    "nocot": "doxcnu6SynzgnIJsQw3rG8Dc9Gd",
}
def a(k): return f"{DOC}#{B[k]}"

POINTS = ("📌 **今日要点**\n"
    f"•  蒂姆·库克主持的最后一届苹果大会，发布全新语音伙伴“Siri AI”，背后是 Gemini 大模型  [↗]({a('apple')})\n"
    f"•  OpenAI 继 Anthropic 后秘密提交 IPO 申请，估值传闻达 $1 万亿，将成 AI 行业估值锚点  [↗]({a('openai')})\n"
    f"•  王鹤团队提出人形机器人动作追踪新框架：仅用不足 3% 的高质量动作数据训出追踪能力  [↗]({a('limmt')})\n"
    f"•  Ryan Greenblatt 与艾伦·图灵研究所发现 AI 不输出思维链的“隐推理”能力年年翻倍，GPT-5.5 已超 3 分钟  [↗]({a('nocot')})")

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
    to = sys.argv[sys.argv.index("--to") + 1] if "--to" in sys.argv else "hlguo@hillhouseinvestment.com"
    card = card_a()
    if "--send" not in sys.argv:
        print(json.dumps(card, ensure_ascii=False, indent=2)); print("\n预览（未发）。--send 推给", to); return
    r = FeishuBotPublisher().send_card_to_recipients([to], card)
    print("form A:", "✅ sent" if r.get("sent") else "✗ failed", r)

if __name__ == "__main__":
    main()
