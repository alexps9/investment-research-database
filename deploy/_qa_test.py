#!/usr/bin/env python3
import urllib.request, json, traceback

try:
    req = urllib.request.Request(
        'http://localhost:9000/qa',
        data=json.dumps({'question': 'test'}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    resp = urllib.request.urlopen(req, timeout=60)
    print("SUCCESS:", resp.read().decode())
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
