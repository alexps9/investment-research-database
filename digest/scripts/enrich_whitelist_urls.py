"""Enrich the whitelist with Scholar / arXiv / GitHub / personal-site URLs.

Strategy (two-hop):
  1. For each whitelist entry with a twitter_handle, fetch the X profile via
     socialdata.tools. Extract candidate URLs from `url` + `description` +
     `entities.{url,description}.urls[].expanded_url`.
  2. For any candidate that looks like a personal homepage (not already a
     Scholar/arXiv/GitHub link), fetch the HTML and extract additional URLs
     from <a href> tags.
  3. Pick best Scholar / arXiv / GitHub / personal URL and prepare to write
     back to the Bitable whitelist table (4 new fields).

Usage:
    cd "/Users/haolinguo/claude code/HH research/daily-digest"
    .venv/bin/python scripts/enrich_whitelist_urls.py --probe         # 10 entries, no write
    .venv/bin/python scripts/enrich_whitelist_urls.py --dry-run       # all entries, no write
    .venv/bin/python scripts/enrich_whitelist_urls.py --apply         # write to Bitable
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from hh_research.storage.bitable_client import read_whitelist  # noqa: E402

API_KEY = os.environ["SOCIALDATA_API_KEY"]
SOCIALDATA_BASE = os.environ.get("SOCIALDATA_BASE_URL", "https://api.socialdata.tools")

URL_RE = re.compile(r"https?://[^\s\)\]\>\,\;\"'<]+", re.IGNORECASE)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)

# We'll filter these as "social/noise" — never the answer
SOCIAL_DOMAINS = {
    "x.com", "twitter.com", "t.co", "linkedin.com", "instagram.com",
    "youtube.com", "youtu.be", "facebook.com", "tiktok.com", "weibo.com",
    "bilibili.com", "mastodon.social", "threads.net", "bsky.app",
}

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}


def classify(u: str) -> str:
    """Bucket: scholar | arxiv | github | personal | social | other"""
    s = u.lower()
    if "scholar.google" in s:
        return "scholar"
    if "arxiv.org/a/" in s or "arxiv.org/find/" in s:
        return "arxiv"
    if "github.com" in s:
        # Filter out specific repos / issues / PRs — only keep root profile
        parts = s.split("github.com/", 1)
        path = parts[1].rstrip("/") if len(parts) > 1 else ""
        # Profile root has 0-1 path segments; specific repos have 2+
        if path and "/" not in path.strip("/"):
            return "github"
        if not path:
            return "social"  # bare github.com root → noise
        return "github_repo"  # we ignore these
    domain = re.sub(r"^https?://(www\.)?", "", s).split("/")[0]
    if domain in SOCIAL_DOMAINS:
        return "social"
    return "personal"


def fetch_x_profile(handle: str, client: httpx.Client) -> dict[str, Any] | None:
    try:
        resp = client.get(f"{SOCIALDATA_BASE}/twitter/user/{handle}",
                          headers={"Authorization": f"Bearer {API_KEY}"},
                          timeout=30.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:  # noqa: BLE001
        print(f"    !! x profile fetch failed for @{handle}: {e}", file=sys.stderr)
    return None


def extract_urls_from_profile(p: dict) -> list[str]:
    out: list[str] = []
    if p.get("url"):
        out.append(p["url"])
    for kind in ("url", "description"):
        for u in (p.get("entities", {}).get(kind, {}).get("urls") or []):
            ex = u.get("expanded_url") or u.get("url")
            if ex:
                out.append(ex)
    desc = p.get("description") or ""
    out.extend(URL_RE.findall(desc))
    # Dedup preserving order
    seen, uniq = set(), []
    for u in out:
        u = u.rstrip(".,;)")
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def fetch_homepage_urls(homepage_url: str, client: httpx.Client) -> list[str]:
    """Hop 2: Fetch personal homepage and extract <a href> URLs.

    Returns list of unique full URLs (filtered to absolute https/http only).
    """
    out: list[str] = []
    try:
        resp = client.get(homepage_url, headers=UA, follow_redirects=True, timeout=15.0)
        if resp.status_code != 200:
            return out
        html = resp.text
        # Extract from href first (cleanest)
        for href in HREF_RE.findall(html):
            if href.startswith(("http://", "https://")):
                out.append(href)
        # Also fallback to free-text URLs (catches inline mentions)
        for u in URL_RE.findall(html):
            out.append(u)
    except Exception as e:  # noqa: BLE001
        print(f"    !! homepage fetch failed for {homepage_url}: {e}", file=sys.stderr)
    # Dedup preserving order
    seen, uniq = set(), []
    for u in out:
        u = u.rstrip(".,;)")
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def pick_best(urls: list[str]) -> dict[str, str | None]:
    """Pick the first/best URL of each type."""
    result = {"scholar_url": None, "arxiv_homepage_url": None,
              "github_url": None, "personal_url": None}
    for u in urls:
        cls = classify(u)
        if cls == "scholar" and not result["scholar_url"]:
            result["scholar_url"] = u
        elif cls == "arxiv" and not result["arxiv_homepage_url"]:
            result["arxiv_homepage_url"] = u
        elif cls == "github" and not result["github_url"]:
            result["github_url"] = u
        elif cls == "personal" and not result["personal_url"]:
            result["personal_url"] = u
    return result


def enrich_one(entry, client: httpx.Client) -> dict[str, str | None] | None:
    """Two-hop enrichment for one whitelist entry. Returns dict or None on failure."""
    handle = entry.twitter_handle
    if not handle:
        return None

    # Hop 1: X profile
    profile = fetch_x_profile(handle, client)
    if not profile:
        return None
    hop1_urls = extract_urls_from_profile(profile)

    best = pick_best(hop1_urls)

    # Hop 2: if we have a personal URL but no scholar/arxiv/github, fetch homepage
    if best["personal_url"] and not (best["scholar_url"] and best["github_url"]):
        time.sleep(0.4)  # be polite
        hop2_urls = fetch_homepage_urls(best["personal_url"], client)
        # Re-pick from combined list (preserve hop1 priority)
        combined = hop1_urls + hop2_urls
        new_best = pick_best(combined)
        # Merge: prefer hop1 personal_url, but fill in scholar/arxiv/github from hop2
        for k in ("scholar_url", "arxiv_homepage_url", "github_url"):
            if not best[k] and new_best[k]:
                best[k] = new_best[k]

    return best


def write_back(record_id: str, urls: dict[str, str | None]) -> tuple[bool, str]:
    """Write 4 URL fields to one Bitable record. Returns (ok, message)."""
    payload = {
        "patch": {k: v for k, v in urls.items() if v},
        "record_id_list": [record_id],
    }
    rel_tmp = "./data/_tmp_enrich_patch.json"
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="test on 10 entries, no write")
    ap.add_argument("--dry-run", action="store_true", help="all entries, no write")
    ap.add_argument("--apply", action="store_true", help="all entries + write to Bitable")
    ap.add_argument("--limit", type=int, default=0, help="cap number of entries (debug)")
    args = ap.parse_args()

    if not (args.probe or args.dry_run or args.apply):
        print("Pick one mode: --probe / --dry-run / --apply")
        sys.exit(1)

    print("Reading whitelist ...")
    wl = read_whitelist()
    with_handle = [e for e in wl if e.twitter_handle]
    print(f"  total: {len(wl)}, with X handle: {len(with_handle)}")

    if args.probe:
        targets = with_handle[:10]
    elif args.limit > 0:
        targets = with_handle[: args.limit]
    else:
        targets = with_handle

    print(f"  enriching {len(targets)} entries ...\n")

    results: list[tuple[str, str, dict]] = []
    counts = {"scholar_url": 0, "arxiv_homepage_url": 0, "github_url": 0, "personal_url": 0}

    with httpx.Client() as client:
        for i, entry in enumerate(targets):
            try:
                best = enrich_one(entry, client)
            except Exception as e:  # noqa: BLE001 — one bad entry shouldn't kill the whole run
                print(f"  [{i+1}/{len(targets)}] {entry.name}: enrichment crashed: {e}")
                continue
            if best is None:
                print(f"  [{i+1}/{len(targets)}] {entry.name}: profile fetch failed")
                continue
            for k, v in best.items():
                if v:
                    counts[k] += 1
            tag = " ".join(
                f"{k.split('_')[0]}={'✓' if best[k] else '·'}" for k in
                ("scholar_url", "arxiv_homepage_url", "github_url", "personal_url")
            )
            print(f"  [{i+1}/{len(targets)}] {entry.name:<28s} {tag}")
            results.append((entry.record_id, entry.name, best))

            # Checkpoint every 30 entries — write JSON so we don't lose state on crash
            if (i + 1) % 30 == 0:
                _checkpoint = Path("data/url_enrichment_result.json")
                _checkpoint.parent.mkdir(parents=True, exist_ok=True)
                _checkpoint.write_text(
                    json.dumps(
                        [{"record_id": r[0], "name": r[1], **r[2]} for r in results],
                        ensure_ascii=False, indent=2,
                    ),
                    encoding="utf-8",
                )

    # Stats
    print("\n=== Coverage stats ===")
    for k, v in counts.items():
        pct = (v / len(targets) * 100) if targets else 0
        print(f"  {k:24s} {v:3d}/{len(targets)} ({pct:.0f}%)")

    # Save full result for inspection
    out_path = Path("data/url_enrichment_result.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            [{"record_id": r[0], "name": r[1], **r[2]} for r in results],
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nFull result saved to: {out_path}")

    if args.apply:
        print(f"\n=== Applying writes to Bitable for {len(results)} records ===")
        ok_count, fail_count = 0, 0
        for i, (rid, name, urls) in enumerate(results):
            if not any(urls.values()):
                continue
            ok, msg = write_back(rid, urls)
            if ok:
                ok_count += 1
            else:
                fail_count += 1
                print(f"  [{i+1}] {name}: FAIL {msg}")
            if (i + 1) % 30 == 0:
                print(f"  ... {i+1}/{len(results)} written, ok={ok_count} fail={fail_count}")
            time.sleep(0.25)  # rate limit

        # Cleanup tmp
        try:
            Path("./data/_tmp_enrich_patch.json").unlink()
        except FileNotFoundError:
            pass

        print(f"\nDone: ok={ok_count}, fail={fail_count}")


if __name__ == "__main__":
    main()
