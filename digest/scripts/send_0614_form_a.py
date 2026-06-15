#!/usr/bin/env python3
"""HH Research Daily 2026-06-14 精选版 · form A 卡（晨报体：自然完整句、少标点堆叠），默认推本人。"""
import os, sys, json
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_H, "..", "src"))
from dotenv import load_dotenv
load_dotenv(os.path.join(_H, "..", ".env"))
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher

DOC = "https://my.feishu.cn/wiki/WRv9wkuEuiy6iYkH5eNcxPvmnWb"
DATE = "2026-06-14"
SELF_EMAIL = "hlguo@hillhouseinvestment.com"
B = {
    "skhynix": "doxcn05o0m7SWsL3yhnMbUu34ah",
    "zhipu": "doxcndAu1F8TFIu4ftuyi6OKsTh",
    "anthropic": "doxcnrEJNol1JSXQKOtSERJxAhh",
    "capital": "doxcnnndkzCqs6mUItVoWDLQtfc",
}
def a(k): return f"{DOC}#{B[k]}"

POINTS = ("💰 **资本动向**\n"
    f"•  **SK 海力士**拟最快 8 月赴纳斯达克上市、募资至多 140 亿美元。它生产 AI 芯片离不开的 HBM 高带宽内存，是英伟达最大的内存供应商，市值已破万亿。  [↗]({a('skhynix')})\n"
    f"•  另有两笔值得留意：Meta 据彭博已切断与 Manus 的系统对接、强制解除 20 亿美元收购（北京要求），前 DOGE 成员则从 a16z、红杉融资约 1.3 亿美元做 AI 政务安全。  [↗]({a('capital')})\n"
    "🔬 **前沿技术**\n"
    f"•  智谱开源旗舰 **GLM-5.2** 采用最宽松的 MIT 协议、支持 100 万 token 上下文，前代在真实软件工程基准上已反超 GPT-5.2。就在 Anthropic 旗舰被监管下架的同一周，它把开源做成了企业对冲断供风险的保险，闭源的能力溢价正被侵蚀。  [↗]({a('zhipu')})\n"
    f"•  Anthropic 旗舰被停用一事有新进展：举报者据报道正是其投资方亚马逊，CEO 向白宫预警后触发出口管制。主动自曝安全风险反成监管把柄，业内对监管边界也出现不同声音。  [↗]({a('anthropic')})")

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
