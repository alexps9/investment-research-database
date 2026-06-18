#!/usr/bin/env python3
"""2026-06-13 三路广播：form A 卡(企业群 webhook + 飞书订阅 1-1) + H Link(文字=一杯咖啡那句，与周末一致)。
默认 dry-run；--send 真发；--hlink-all 用 G0+G1 全部 H Link 收件人(否则默认 OPENIDS)。"""
import os, sys
os.environ.setdefault("LARK_CLI_NO_PROXY", "1")
_H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _H)
from send_0613_form_a import card_a, DOC  # noqa: E402  (also loads .env + src path)
from send_digest_to_enterprise import send as ent_send  # noqa: E402
from send_digest_to_feishu_bot import load_active_subscribers_from_bitable  # noqa: E402
from hh_research.publish.feishu_bot_publisher import FeishuBotPublisher  # noqa: E402
from hh_research.publish.hlink_publisher import HLinkPublisher  # noqa: E402

TITLE = "HH Research Daily · 2026-06-13"
HLINK_LINES = ["☕️ 一杯咖啡的时间，带您了解今日 AI 资讯", "", "查看完整日报 →"]

def main():
    send = "--send" in sys.argv
    hlink_all = "--hlink-all" in sys.argv
    form = card_a()
    recips, blog = load_active_subscribers_from_bitable()
    if hlink_all:
        ids = []
        for g in ("H_LINK_RECIPIENT_OPENIDS_G0", "H_LINK_RECIPIENT_OPENIDS_G1"):
            ids += [s.strip() for s in os.environ.get(g, "").split(",") if s.strip()]
        hrecips = list(dict.fromkeys(ids))
    else:
        hrecips = [s.strip() for s in os.environ.get("H_LINK_RECIPIENT_OPENIDS", "").split(",") if s.strip()]
    bar = "=" * 60
    print(bar)
    print(f"三路广播 · {TITLE}   {'[SEND]' if send else '[DRY-RUN]'}")
    print(f"  Route1 企业群 webhook : form A 卡")
    print(f"  Route2 飞书订阅 1-1   : {len(recips)} 人 · form A 卡")
    print(f"  Route3 H Link        : {len(hrecips)} 人{' (G0+G1 全部)' if hlink_all else ' (默认 OPENIDS)'} · 文字=一杯咖啡")
    print(bar)
    print("【H Link 文字预览】")
    print("\n".join(HLINK_LINES))
    print(bar)
    if not send:
        print("[dry-run] 未发送。加 --send 真发；加 --hlink-all 发全部 H Link。")
        return
    url = os.environ.get("HH_LARK_ENTERPRISE_WEBHOOK_URL"); secret = os.environ.get("HH_LARK_ENTERPRISE_WEBHOOK_SECRET")
    r1 = ent_send(url, secret, {"msg_type": "interactive", "card": form})
    ok1 = r1.get("code") == 0 or r1.get("StatusCode") == 0
    print(f"Route1 企业群: {'✅' if ok1 else '✗'} {r1}")
    r2 = FeishuBotPublisher().send_card_to_recipients(recips, form)
    print(f"Route2 飞书订阅: ✅ sent={len(r2.get('sent', []))} failed={len(r2.get('failed', []))}")
    r3 = HLinkPublisher().send_textcard(hrecips, TITLE, HLINK_LINES, DOC)
    print(f"Route3 H Link: error_code={r3.get('error_code')} skipped={r3.get('result', {}).get('_local_skipped_open_ids')}")
    print(bar); print("三路广播完成")

if __name__ == "__main__":
    main()
