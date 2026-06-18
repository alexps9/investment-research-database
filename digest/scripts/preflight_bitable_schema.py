#!/usr/bin/env python3
"""v8.0 Bitable schema preflight.

Verifies that all v8-required fields exist in the Bitable whitelist and
signals tables before pipeline runs. Used by daily-pipeline-main as a
fail-fast check.

Exits 0 if schema valid; exits 2 with diff report if missing fields.

Usage:
    python scripts/preflight_bitable_schema.py
    python scripts/preflight_bitable_schema.py --quiet   # only print errors
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

BASE_TOKEN = "UdwrbpCMoasCs3snCvbcKgbsnfc"
WHITELIST_TABLE_ID = "tblpVgQBAkPptnip"
SIGNALS_TABLE_ID = "tbllGsqhy4swhzkz"

REQUIRED_WHITELIST_FIELDS = {
    "tier",               # P0+, P0, P1, P2
    "entity_type",        # company / person / lab / university / media / investor / benchmark_org
    "source_authority",   # official / founder / employee / third_party / media / unknown
}

REQUIRED_SIGNALS_FIELDS = {
    "event_type",
    "m1_score", "m2_score", "m3_score", "m4_score", "m5_score",
    "constraint_pass",
    "constraint_rule",
    "auto_headline",
    "edge_case",
    "final_selected",
    "primary_org",
    "canonical_event_key",
}


def _list_fields(base_token: str, table_id: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["lark-cli", "base", "+field-list",
         "--as", "user",
         "--base-token", base_token,
         "--table-id", table_id],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"field-list failed for {table_id}: {result.stderr[:200]}")
    payload = json.loads(result.stdout)
    if not payload.get("ok"):
        raise RuntimeError(f"field-list error: {payload}")
    return payload["data"]["fields"]


def check_table(name: str, table_id: str, required: set[str]) -> tuple[bool, set[str]]:
    fields = _list_fields(BASE_TOKEN, table_id)
    present = {f["name"] for f in fields}
    missing = required - present
    return (len(missing) == 0, missing)


def main() -> int:
    parser = argparse.ArgumentParser(description="v8.0 Bitable schema preflight")
    parser.add_argument("--quiet", action="store_true", help="only print errors")
    args = parser.parse_args()

    all_pass = True
    report = []

    for label, table_id, required in (
        ("whitelist (信号源)", WHITELIST_TABLE_ID, REQUIRED_WHITELIST_FIELDS),
        ("signals (信号)", SIGNALS_TABLE_ID, REQUIRED_SIGNALS_FIELDS),
    ):
        try:
            ok, missing = check_table(label, table_id, required)
        except Exception as e:
            print(f"❌ {label} ({table_id}): {e}", file=sys.stderr)
            return 2
        if not ok:
            all_pass = False
            report.append(f"❌ {label} ({table_id}) missing: {sorted(missing)}")
        elif not args.quiet:
            report.append(f"✅ {label}: all {len(required)} v8 fields present")

    for line in report:
        print(line)

    if not all_pass:
        print("\n❌ v8 schema preflight FAILED", file=sys.stderr)
        print("   Run scripts/bootstrap_v8_schema.sh to create missing fields", file=sys.stderr)
        return 2

    if not args.quiet:
        print("\n✅ v8 schema preflight PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
