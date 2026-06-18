#!/usr/bin/env python3
"""HH Research Daily 2026-06-12 精选版 · form A 卡（咖啡句 + 两大类要点 + docx 锚点），默认推本人。"""
import os, sys, json
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_H, "..", "src"))
from dotenv import load_dotenv
load_dotenv(os.path.join(_H, "..", ".env"))
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher

DOC = "https://my.feishu.cn/wiki/Tsz2wYePCiXzKMkpGRxcUVBvnkh"
DATE = "2026-06-12"
SELF_EMAIL = "hlguo@hillhouseinvestment.com"  # 本人在 hres-bot 应用下的 email（FEISHU_BOT_RECIPIENT_OPENIDS 首位）
B = {
    "prometheus": "doxcn9ltbG4K0XQ6buDcBfglqFd",
    "tcs": "doxcn0oeEPqe1j6h3H0cZLP39cd",
    "recursive": "doxcne2fC68QSKm7PCFTZvf4kjb",
    "capital": "doxcnC1UMIZOj9NOJjKZIbzdQHg",
}
def a(k): return f"{DOC}#{B[k]}"

# 卡片按两大类分组；文案原则（6-12 用户两轮反馈校准）：专业投研晨报口吻——
# 动词准确（完成融资/达成合作，忌"拿到了/扫一眼"），每条两句有递进（事实句+意义句），
# 衔接自然，判断克制；保持易懂，标点以逗号句号为主，避免破折号冒号间隔号堆叠
POINTS = ("💰 **资本动向**\n"
    f"•  贝索斯创立的 **Prometheus** 完成 **120 亿美元**融资，估值达 410 亿美元，创下 Physical AI 领域最大单笔融资纪录。这家公司的目标并非用 AI 替代体力劳动，而是打造能够独立完成工程设计的智能系统。  [↗]({a('prometheus')})\n"
    f"•  另有两笔交易值得关注，专注实体经济智能化的风投 **Base10** 同时完成两支基金募集，研发可重构工厂机器人的初创公司 **Theker** 获得 8500 万美元投资。  [↗]({a('capital')})\n"
    "🔬 **前沿技术**\n"
    f"•  AI 自主开展 AI 研究首次交出可信的成绩单。**Recursive** 的自动研究系统在三项公开基准上，超越了数十位研究者与数百个 AI 智能体协作数月得到的最优方案，训练效率与芯片利用率均有实质提升，AI 改进 AI 正在从设想变为现实。  [↗]({a('recursive')})\n"
    f"•  **Anthropic** 与塔塔咨询达成战略合作并设立专属业务单元。借助头部 IT 服务商的企业客户网络，模型厂商正在打开传统行业的市场入口。  [↗]({a('tcs')})")

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
