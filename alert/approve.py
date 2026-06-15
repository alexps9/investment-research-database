#!/usr/bin/env python3
"""审核待发送的推送。逐批展示，输入 y 确认推送、n 丢弃、q 退出。"""

import json
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sender import send_feishu

PENDING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pending")


def main():
    if not os.path.isdir(PENDING_DIR):
        print("没有待审核消息。")
        return

    files = sorted(f for f in os.listdir(PENDING_DIR) if f.endswith(".json"))
    if not files:
        print("没有待审核消息。")
        return

    total_items = 0
    for fname in files:
        fpath = os.path.join(PENDING_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else [data]
        total_items += len(items)

    print(f"共 {len(files)} 个批次，{total_items} 条待审核：\n")
    approved = 0
    rejected = 0

    for fname in files:
        fpath = os.path.join(PENDING_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else [data]

        print("═" * 50)
        print(f"批次: {fname}  ({len(items)} 条)")
        print("═" * 50)

        remaining = []
        quit_flag = False

        for item in items:
            print("─" * 50)
            print(f"来源: @{item.get('username', '?')}  时间: {item.get('created_at', '?')}")
            print(f"类型: {item.get('event_type', '?')}")
            print()
            print(item.get("message", "(无内容)"))
            print()

            while True:
                choice = input("  [y] 推送  [n] 丢弃  [q] 退出 → ").strip().lower()
                if choice in ("y", "n", "q"):
                    break
                print("  请输入 y / n / q")

            if choice == "q":
                remaining.append(item)
                quit_flag = True
                break
            elif choice == "y":
                ok = send_feishu(item["message"])
                if ok:
                    print("  ✓ 已推送")
                else:
                    print("  ✓ 已推送 (dry run)")
                approved += 1
            else:
                rejected += 1
                print("  ✗ 已丢弃")

        if quit_flag:
            # 把未审核的写回
            remaining.extend(items[items.index(remaining[0]) + 1:])
            if remaining:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(remaining, f, ensure_ascii=False, indent=2)
            else:
                os.remove(fpath)
            print(f"\n退出。已推送 {approved}，丢弃 {rejected}，剩余未审核。")
            return

        # 整批审完，删除文件
        os.remove(fpath)

    print("─" * 50)
    print(f"\n全部审核完毕。推送 {approved} 条，丢弃 {rejected} 条。")


if __name__ == "__main__":
    main()
