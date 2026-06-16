#!/usr/bin/env python3
import urllib.request, json, traceback

QUESTIONS = [
    "test",
    "\u6700\u8fd1\u6709\u54ea\u4e9b\u91cd\u8981\u6a21\u578b\u53d1\u5e03\uff1f",  # 最近有哪些重要模型发布？
]

for q in QUESTIONS:
    print(f"\n>>> Question: {q}")
    try:
        req = urllib.request.Request(
            'http://localhost:9000/qa',
            data=json.dumps({'question': q}).encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=utf-8'},
            method='POST'
        )
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode('utf-8'))
        print(f"    STATUS: 200 OK")
        print(f"    ANSWER: {data['answer'][:400]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"    HTTP {e.code}: {body[:500]}")
    except Exception as e:
        print(f"    ERROR: {e}")
        traceback.print_exc()
