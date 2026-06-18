"""Bulk-fill arxiv_author_query for the whitelist.

Strategy:
- For each whitelist entry:
  - Skip if name == organization (org entry, not a person)
  - Skip if name contains any Chinese/CJK character (need manual pinyin mapping)
  - Otherwise: auto-set arxiv_author_query = f'au:"{name}"'
- DRY-RUN by default. Pass --apply to actually write to Bitable.

Usage:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/bulk_fill_arxiv_query.py             # dry-run, prints stats + 10 samples
    .venv/bin/python scripts/bulk_fill_arxiv_query.py --apply     # writes to Bitable
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.storage.bitable_client import read_whitelist  # noqa: E402

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
# Strip CJK chars AND parenthesized content (often Chinese annotations), then clean whitespace.
STRIP_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf()()\[\]【】]+")


def strip_cjk(name: str) -> str:
    """Extract the English-only portion of a mixed-script name."""
    cleaned = STRIP_RE.sub(" ", name)
    # Collapse multiple spaces
    return " ".join(cleaned.split())


def classify(entry) -> tuple[str, str | None]:
    """Return (action, proposed_value).

    action: 'skip-org' | 'skip-cjk' | 'skip-empty' | 'set' | 'set-stripped'
    """
    name = (entry.name or "").strip()
    if not name:
        return "skip-empty", None
    if entry.organization and entry.organization.strip() == name:
        return "skip-org", None
    if CJK_RE.search(name):
        # Try to extract English-only portion
        stripped = strip_cjk(name)
        # Need at least a first + last name to be useful (2+ tokens, each >= 2 chars)
        tokens = [t for t in stripped.split() if len(t) >= 2]
        if len(tokens) >= 2:
            return "set-stripped", f'au:"{" ".join(tokens)}"'
        return "skip-cjk", None
    return "set", f'au:"{name}"'


def apply_updates(updates: list[tuple[str, str]], sleep_between: float = 0.3) -> None:
    """Apply {record_id: arxiv_author_query} updates via lark-cli record-batch-update."""
    app_token = os.environ["HH_BITABLE_APP_TOKEN"]
    table_id = os.environ["HH_WHITELIST_TABLE_ID"]

    # Batch-update does one patch across many records, which doesn't fit our case.
    # Use record-upsert or record-batch-update grouped by patch. Easiest: loop record-update.
    # But CLI supports record-batch-update with {patch, record_id_list} — all records get SAME patch.
    # Since each record has unique query string, we need per-record updates.
    # Use record-upsert-like workflow: call +record-batch-update once per unique patch.

    # Group by patch
    by_patch: dict[str, list[str]] = {}
    for rid, query in updates:
        by_patch.setdefault(query, []).append(rid)

    # Each unique patch -> one API call
    print(f"    grouping into {len(by_patch)} unique patches (expected ≈ len(updates))")

    # lark-cli requires --json @path to be a relative path within cwd.
    # We use "./data/_tmp_whitelist_update.json" directly.
    rel_tmp = "./data/_tmp_whitelist_update.json"
    tmp_path = Path(rel_tmp)
    tmp_path.parent.mkdir(parents=True, exist_ok=True)

    success = 0
    for i, (query, rids) in enumerate(by_patch.items()):
        payload = {"patch": {"arxiv_author_query": query}, "record_id_list": rids}
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False))
        cmd = [
            "lark-cli", "--profile", "personal", "base", "+record-batch-update",
            "--base-token", app_token, "--table-id", table_id,
            "--json", f"@{rel_tmp}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            resp = json.loads(result.stdout)
            if resp.get("ok"):
                success += len(rids)
            else:
                print(f"    [{i + 1}/{len(by_patch)}] FAIL: {resp.get('error')}")
        else:
            print(f"    [{i + 1}/{len(by_patch)}] rc={result.returncode}: {result.stderr[:200]}")
        if (i + 1) % 20 == 0:
            print(f"    ... {i + 1}/{len(by_patch)} patches done")
        # Rate-limit mitigation: Feishu batch-update has ~20 req/s limit, play safe.
        if sleep_between:
            import time
            time.sleep(sleep_between)

    try:
        tmp_path.unlink()
    except FileNotFoundError:
        pass

    print(f"    updated {success}/{sum(len(v) for v in by_patch.values())} records")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually write to Bitable (default: dry-run)")
    args = parser.parse_args()

    print("Reading whitelist ...")
    wl = read_whitelist()
    print(f"  {len(wl)} entries")

    counts = {"skip-org": 0, "skip-cjk": 0, "skip-empty": 0, "set": 0, "set-stripped": 0, "already-set": 0}
    updates: list[tuple[str, str]] = []
    samples: dict[str, list[tuple[str, str | None]]] = {}

    for entry in wl:
        if entry.arxiv_author_query:
            counts["already-set"] += 1
            continue
        action, value = classify(entry)
        counts[action] += 1
        if action in ("set", "set-stripped"):
            updates.append((entry.record_id, value))  # type: ignore[arg-type]
        if len(samples.get(action, [])) < 5:
            samples.setdefault(action, []).append((entry.name, value))

    print("\nClassification summary:")
    for k, v in counts.items():
        print(f"  {k:12s} {v}")

    print("\nSamples:")
    for action, items in samples.items():
        if items:
            print(f"  {action}:")
            for name, val in items:
                print(f"    {name!r:30s} -> {val!r}")

    if not args.apply:
        print("\nDRY-RUN only. Run with --apply to write to Bitable.")
        return

    print(f"\nApplying {len(updates)} updates to Bitable ...")
    apply_updates(updates)
    print("Done.")


if __name__ == "__main__":
    main()
