#!/usr/bin/env python3
"""HH Research Daily 2026-06-11 精选版 · form A 卡（咖啡句 + 两大类要点 + docx 锚点），默认推本人。"""
import os, sys, json
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_H, "..", "src"))
from dotenv import load_dotenv
load_dotenv(os.path.join(_H, "..", ".env"))
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher

DOC = "https://my.feishu.cn/wiki/CLnfwRPY6ii4Ylkn43bcF39sngh"
DATE = "2026-06-11"
SELF_EMAIL = "hlguo@hillhouseinvestment.com"  # 本人在 hres-bot 应用下的 email（FEISHU_BOT_RECIPIENT_OPENIDS 首位）
B = {
    "amodei": "doxcnWwlTI0RDjGpeS3s30vE33c",
    "diffusiongemma": "doxcnNegIzLsBf1hpWVymRUgkDe",
    "spark": "doxcncTF7UlqVouOMUNM7SmnLkh",
    "capital": "doxcn77VlAeeceefRPPP73ZTuMb",
}
def a(k): return f"{DOC}#{B[k]}"

# 卡片按两大类分组：💰 资本动向 / 🔬 前沿技术
POINTS = ("💰 **资本动向**\n"
    f"•  **Warner Music** 收购 **Sureel AI**——这家初创能识别 AI 生成音乐借鉴了谁的作品、版权费该付给谁；版权方从起诉 AI 转向买入溯源技术  [↗]({a('capital')})\n"
    "🔬 **前沿技术**\n"
    f"•  **Anthropic CEO Amodei 万字长文呼吁给 AI 立规矩**：新模型上线前先过安全测试、由第三方把关、管住高端芯片流向，同天再掏 1.5 亿美元培养 AI 人才  [↗]({a('amodei')})\n"
    f"•  **Google 开源 DiffusionGemma**：26B MoE 扩散语言模型，H100 单卡突破 1000 tokens/s、最高 4 倍提速——文本扩散路线正面挑战自回归范式  [↗]({a('diffusiongemma')})\n"
    f"•  **World Labs 开源 Spark 2.0**：AI 生成的 3D 世界直接在浏览器流畅运行，手机也能即点即进——解决 3D 内容分发的最后一公里  [↗]({a('spark')})")

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
