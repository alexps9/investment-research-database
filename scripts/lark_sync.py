"""
飞书多维表格双向同步脚本。

用法:
  python scripts/lark_sync.py push    # 本地数据 → 飞书（首次建表+推送）
  python scripts/lark_sync.py pull    # 飞书 → 本地 JSON
  python scripts/lark_sync.py status  # 查看同步状态
"""
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ── 配置 ─────────────────────────────────────────────────────────────────────

APP_ID = "cli_aa8fd45e637d1be9"
APP_SECRET = "52X0t69fPs3aMU4qQGba1caREIzbDUdN"
BASE_URL = "https://open.feishu.cn/open-apis"

# 同步状态文件
STATE_FILE = Path(__file__).parent / ".lark-sync-state.json"
DATA_FILE = Path(__file__).parent.parent / "backend" / "app" / "data" / "world_model_data.py"
JSON_OUT = Path(__file__).parent.parent / "frontend" / "src" / "data" / "world-model-data.json"


# ── API 工具 ──────────────────────────────────────────────────────────────────

def api_request(method, path, token, body=None):
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        err_body = e.read().decode()
        print(f"API Error {e.code}: {err_body}")
        raise


def get_tenant_token():
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    body = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req) as resp:
        data = json.loads(resp.read())
    if data.get("code") != 0:
        raise RuntimeError(f"Failed to get token: {data}")
    return data["tenant_access_token"]


# ── 表结构定义 ────────────────────────────────────────────────────────────────

PAPER_FIELDS = [
    {"field_name": "id", "type": 1},           # 文本
    {"field_name": "title", "type": 1},
    {"field_name": "year", "type": 2},          # 数字
    {"field_name": "quarter", "type": 2},
    {"field_name": "paradigm", "type": 1},
    {"field_name": "layer", "type": 1},
    {"field_name": "lane", "type": 1},
    {"field_name": "row", "type": 1},
    {"field_name": "path", "type": 1},
    {"field_name": "size", "type": 1},
    {"field_name": "builds_on", "type": 1},     # JSON array as text
    {"field_name": "application", "type": 1},   # track/赛道
    {"field_name": "institution", "type": 1},   # 机构
    {"field_name": "cited_by_count", "type": 2},
]


# ── Push: 本地 → 飞书 ────────────────────────────────────────────────────────

def load_papers_from_backend():
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
    from app.data.world_model_data import PAPERS
    return PAPERS


def create_bitable(token):
    """创建一个新的多维表格 App"""
    # 先创建一个文件夹里的 bitable
    resp = api_request("POST", "/bitable/v1/apps", token, {
        "name": "World Model 论文图谱",
    })
    if resp.get("code") != 0:
        raise RuntimeError(f"Create bitable failed: {resp}")
    app_token = resp["data"]["app"]["app_token"]
    print(f"Created bitable: {app_token}")
    return app_token


def create_table(token, app_token):
    """在 bitable 里创建 papers 表"""
    # 先尝试获取已有的表（新建 bitable 自带一张默认表）
    resp = api_request("GET", f"/bitable/v1/apps/{app_token}/tables", token)
    if resp.get("code") == 0 and resp.get("data", {}).get("items"):
        table_id = resp["data"]["items"][0]["table_id"]
        print(f"Using existing table: {table_id}")
        return table_id

    resp = api_request("POST", f"/bitable/v1/apps/{app_token}/tables", token, {
        "table": {"name": "Papers", "default_view_name": "全部论文"}
    })
    if resp.get("code") != 0:
        raise RuntimeError(f"Create table failed: {resp}")
    table_id = resp["data"]["table_id"]
    print(f"Created table: {table_id}")
    return table_id


def setup_fields(token, app_token, table_id):
    """添加字段（跳过默认已有的第一个文本字段）"""
    # 先获取已有字段
    resp = api_request("GET", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields", token)
    existing = {f["field_name"] for f in resp.get("data", {}).get("items", [])}

    for field in PAPER_FIELDS:
        if field["field_name"] in existing:
            continue
        resp = api_request("POST", f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields", token, field)
        if resp.get("code") != 0:
            print(f"  Warning: field {field['field_name']} creation issue: {resp.get('msg')}")
        else:
            print(f"  Created field: {field['field_name']}")


def push_papers(token, app_token, table_id, papers):
    """批量推送论文到飞书"""
    records = []
    for p in papers:
        records.append({
            "fields": {
                "id": p.id,
                "title": p.title,
                "year": p.year,
                "quarter": p.quarter,
                "paradigm": p.paradigm,
                "layer": p.layer,
                "lane": p.lane,
                "row": p.row,
                "path": p.path,
                "size": p.size,
                "builds_on": json.dumps(p.builds_on or []),
                "application": getattr(p, "application", ""),
                "institution": "",
                "cited_by_count": p.cited_by_count,
            }
        })

    # 飞书批量上限 500 条
    batch_size = 500
    total_created = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        resp = api_request("POST",
            f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            token, {"records": batch})
        if resp.get("code") != 0:
            print(f"  Batch push error: {resp.get('msg')}")
        else:
            total_created += len(batch)
            print(f"  Pushed {total_created}/{len(records)} records")

    return total_created


def do_push():
    print("=== Push: 本地 → 飞书 ===\n")
    token = get_tenant_token()
    print(f"Got token: {token[:10]}...\n")

    papers = load_papers_from_backend()
    print(f"Loaded {len(papers)} papers from backend\n")

    # 检查是否已有 state
    state = load_state()
    if state.get("app_token") and state.get("table_id"):
        print(f"Found existing bitable: {state['app_token']}")
        app_token = state["app_token"]
        table_id = state["table_id"]
    else:
        app_token = create_bitable(token)
        table_id = create_table(token, app_token)

    # 始终确保字段存在
    setup_fields(token, app_token, table_id)

    count = push_papers(token, app_token, table_id, papers)
    print(f"\nDone! Pushed {count} papers to Lark Bitable.")

    # 保存状态
    save_state({
        "app_token": app_token,
        "table_id": table_id,
        "last_push": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "paper_count": count,
    })
    print(f"State saved to {STATE_FILE}")
    print(f"\nBitable URL: https://www.feishu.cn/base/{app_token}")


# ── Pull: 飞书 → 本地 ────────────────────────────────────────────────────────

def do_pull():
    print("=== Pull: 飞书 → 本地 ===\n")
    state = load_state()
    if not state.get("app_token"):
        print("Error: No bitable configured. Run 'push' first.")
        return

    token = get_tenant_token()
    app_token = state["app_token"]
    table_id = state["table_id"]

    # 分页拉取所有记录
    all_records = []
    page_token = None
    while True:
        path = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=500"
        if page_token:
            path += f"&page_token={page_token}"
        resp = api_request("GET", path, token)
        if resp.get("code") != 0:
            print(f"Error: {resp.get('msg')}")
            return
        items = resp.get("data", {}).get("items", [])
        all_records.extend(items)
        if not resp["data"].get("has_more"):
            break
        page_token = resp["data"]["page_token"]

    print(f"Pulled {len(all_records)} records from Lark\n")

    # 转换为 Paper 格式
    papers = []
    for rec in all_records:
        f = rec["fields"]
        papers.append({
            "id": f.get("id", ""),
            "title": f.get("title", ""),
            "year": int(f.get("year", 2024)),
            "quarter": int(f.get("quarter", 1)),
            "paradigm": f.get("paradigm", ""),
            "layer": f.get("layer", "arch"),
            "lane": f.get("lane", ""),
            "row": f.get("row", ""),
            "path": f.get("path", "trunk"),
            "size": f.get("size", "md"),
            "builds_on": json.loads(f.get("builds_on", "[]")),
            "application": f.get("application", ""),
            "institution": f.get("institution", ""),
            "cited_by_count": int(f.get("cited_by_count", 0)),
        })

    # 保存为 JSON
    out_path = Path(__file__).parent / "lark-papers.json"
    out_path.write_text(json.dumps(papers, ensure_ascii=False, indent=2))
    print(f"Saved to {out_path}")
    print(f"\nPapers pulled: {len(papers)}")
    print("Next: review lark-papers.json, then update backend data if needed.")

    save_state({**state, "last_pull": time.strftime("%Y-%m-%dT%H:%M:%S")})


# ── Status ────────────────────────────────────────────────────────────────────

def do_status():
    state = load_state()
    if not state:
        print("No sync state found. Run 'push' to initialize.")
        return
    print("=== Lark Sync Status ===\n")
    print(f"  Bitable App:  {state.get('app_token', 'N/A')}")
    print(f"  Table ID:     {state.get('table_id', 'N/A')}")
    print(f"  Last Push:    {state.get('last_push', 'never')}")
    print(f"  Last Pull:    {state.get('last_pull', 'never')}")
    print(f"  Paper Count:  {state.get('paper_count', 0)}")
    if state.get("app_token"):
        print(f"\n  URL: https://www.feishu.cn/base/{state['app_token']}")


# ── State 管理 ────────────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "push":
        do_push()
    elif cmd == "pull":
        do_pull()
    elif cmd == "status":
        do_status()
    else:
        print(__doc__)
