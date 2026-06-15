"""Apply both enrichment phases to Bitable from saved JSON files.

Reads:
  - data/url_enrichment_result.json   (phase 1: scholar / github / personal)
  - data/arxiv_validation_result.json (phase 2: arxiv_homepage / openalex)
And writes 5 fields back to whitelist Bitable.

Doesn't redo discovery (saves ~15 min).

Usage:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/apply_url_enrichment.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

PHASE1 = Path("data/url_enrichment_result.json")
PHASE2 = Path("data/arxiv_validation_result.json")


def write_back(record_id: str, patch: dict[str, Any]) -> tuple[bool, str]:
    """Write fields to one Bitable record."""
    payload = {"patch": patch, "record_id_list": [record_id]}
    rel_tmp = "./data/_tmp_apply_patch.json"
    Path(rel_tmp).parent.mkdir(parents=True, exist_ok=True)
    Path(rel_tmp).write_text(json.dumps(payload, ensure_ascii=False))

    cmd = [
        "lark-cli", "--profile", "personal",
        "base", "+record-batch-update",
        "--base-token", os.environ["HH_BITABLE_APP_TOKEN"],
        "--table-id", os.environ["HH_WHITELIST_TABLE_ID"],
        "--json", f"@{rel_tmp}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        return False, r.stderr[:200]
    try:
        resp = json.loads(r.stdout)
        if resp.get("ok"):
            return True, "ok"
        return False, str(resp.get("error", "unknown"))[:200]
    except json.JSONDecodeError:
        return False, "non-json response"


def main() -> None:
    # Load both JSONs
    p1 = json.loads(PHASE1.read_text(encoding="utf-8")) if PHASE1.exists() else []
    p2 = json.loads(PHASE2.read_text(encoding="utf-8")) if PHASE2.exists() else []
    print(f"Loaded phase 1: {len(p1)} records, phase 2: {len(p2)} records")

    # Index phase 2 by record_id
    p2_by_id = {r["record_id"]: r for r in p2}

    # Build merged patches (one per record_id)
    patches: dict[str, dict[str, Any]] = {}
    for r1 in p1:
        rid = r1["record_id"]
        patch: dict[str, Any] = {}
        for k in ("scholar_url", "github_url", "personal_url"):
            if r1.get(k):
                patch[k] = r1[k]
        if patch:
            patches.setdefault(rid, {}).update(patch)

    for r2 in p2:
        rid = r2["record_id"]
        patch: dict[str, Any] = {}
        if r2.get("arxiv_homepage_url"):
            patch["arxiv_homepage_url"] = r2["arxiv_homepage_url"]
        if r2.get("openalex_url"):
            patch["openalex_url"] = r2["openalex_url"]
        if patch:
            patches.setdefault(rid, {}).update(patch)

    print(f"Total records to update: {len(patches)}")

    # Apply
    ok_count, fail_count = 0, 0
    items = list(patches.items())
    for i, (rid, patch) in enumerate(items):
        ok, msg = write_back(rid, patch)
        if ok:
            ok_count += 1
        else:
            fail_count += 1
            if fail_count <= 3:
                print(f"  [{i+1}] {rid}: FAIL {msg}")
        if (i + 1) % 30 == 0:
            print(f"  ... {i+1}/{len(items)} written, ok={ok_count} fail={fail_count}")
        time.sleep(0.25)

    try:
        Path("./data/_tmp_apply_patch.json").unlink()
    except FileNotFoundError:
        pass

    print(f"\nDone: ok={ok_count}, fail={fail_count}")


if __name__ == "__main__":
    main()
