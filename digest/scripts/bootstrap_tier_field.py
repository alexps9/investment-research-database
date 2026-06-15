#!/usr/bin/env python3
"""Bootstrap Bitable whitelist tier / entity_type / source_authority fields.

Reads config/p0_whitelist.yml snapshot and writes back the classified values
to Bitable using record-upsert (sequential, 0.5s spacing per lark-base SKILL).

Usage:
    python scripts/bootstrap_tier_field.py            # actually write
    python scripts/bootstrap_tier_field.py --dry-run  # preview only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

BASE_TOKEN = "UdwrbpCMoasCs3snCvbcKgbsnfc"
WHITELIST_TABLE_ID = "tblpVgQBAkPptnip"
SNAPSHOT_PATH = "config/p0_whitelist.yml"


def upsert_one(record_id: str, fields: dict[str, str]) -> tuple[bool, str]:
    """Upsert one record. Returns (success, error_message)."""
    result = subprocess.run(
        ["lark-cli", "base", "+record-upsert",
         "--as", "user",
         "--base-token", BASE_TOKEN,
         "--table-id", WHITELIST_TABLE_ID,
         "--record-id", record_id,
         "--json", json.dumps(fields, ensure_ascii=False)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return (False, f"exit {result.returncode}: {result.stderr[:200]}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return (False, f"json decode: {e}; stdout: {result.stdout[:200]}")
    if not payload.get("ok"):
        err = payload.get("error", {})
        return (False, f"{err.get('code')}: {err.get('message', str(err))[:200]}")
    return (True, "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Bitable tier fields")
    parser.add_argument("--dry-run", action="store_true", help="preview only")
    parser.add_argument("--limit", type=int, default=None, help="limit row count (debug)")
    args = parser.parse_args()

    print(f"📥 Loading snapshot from {SNAPSHOT_PATH}...")
    snapshot = yaml.safe_load(Path(SNAPSHOT_PATH).read_text())
    entities = snapshot["entities"]
    if args.limit:
        entities = entities[:args.limit]
    print(f"   {len(entities)} entities to process")

    if args.dry_run:
        print("🌵 DRY-RUN: not writing Bitable")
        for e in entities[:10]:
            print(f"  would set {e['record_id']}: tier={e['tier']}, "
                  f"entity_type={e['entity_type']}, source_authority={e['source_authority']}")
        if len(entities) > 10:
            print(f"  ... and {len(entities) - 10} more")
        return 0

    print(f"✍️ Writing to Bitable (sequential, 0.5s spacing)...")
    success = 0
    failed = []
    for i, e in enumerate(entities, 1):
        fields = {
            "tier": e["tier"],
            "entity_type": e["entity_type"],
            "source_authority": e["source_authority"],
        }
        ok, err = upsert_one(e["record_id"], fields)
        if ok:
            success += 1
        else:
            failed.append((e["record_id"], e["name"], err))
        if i % 50 == 0:
            print(f"   [{i}/{len(entities)}]  success={success}  failed={len(failed)}")
        time.sleep(0.5)  # SKILL: serial with 0.5-1s spacing

    print(f"\n📊 Final: success={success}/{len(entities)}, failed={len(failed)}")
    if failed:
        print("\n❌ Failed rows:")
        for rid, name, err in failed[:20]:
            print(f"   {rid}  {name}  → {err}")
        if len(failed) > 20:
            print(f"   ... and {len(failed) - 20} more")
        return 2
    print("✅ All rows updated successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
