"""
Parse HH Research Pipeline signal-source CSV and generate INSERT SQL for Supabase.

Usage:
    python import_sources_csv.py

Output: ../import_sources.sql
"""
import csv
import uuid
import re
import sys
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent / "assets" / "HH Research Pipeline_信号源_全字段 · 生产原始.csv"
OUT_PATH = Path(__file__).parent.parent / "import_sources.sql"

# ── value normalisers ──────────────────────────────────────────────────────────

def pg_str(v: str | None) -> str:
    """Encode the value as hex and let PostgreSQL decode it.
    convert_from(decode('<hex>', 'hex'), 'UTF8') has ZERO quoting/escaping
    issues — the hex string only contains [0-9a-f] characters."""
    if v is None or v.strip() == "":
        return "NULL"
    s = v.strip().replace("\r", "").replace("\n", " ")
    # Drop any control characters that are genuinely unrepresentable
    s = "".join(ch for ch in s if ord(ch) >= 32)
    hex_val = s.encode("utf-8", errors="replace").hex()
    return f"convert_from(decode('{hex_val}','hex'),'UTF8')"


def pg_float(v: str | None) -> str:
    if v is None or v.strip() == "":
        return "NULL"
    try:
        return str(float(v.strip()))
    except ValueError:
        return "NULL"


def pg_ts(v: str | None) -> str:
    """Best-effort ISO timestamp or NULL."""
    if v is None or v.strip() == "":
        return "NULL"
    s = v.strip().replace("'", "''")
    return f"'{s}'"


ACTIVITY_MAP = {
    "非常": "very_active",
    "非常活跃": "very_active",
    "很活跃": "very_active",
    "活跃": "active",
    "一般": "normal",
    "不活跃": "inactive",
    "inactive": "inactive",
    "active": "active",
    "very_active": "very_active",
}

def map_activity(v: str | None) -> str:
    if not v:
        return "unknown"
    return ACTIVITY_MAP.get(v.strip(), "normal")


ENTITY_TYPE_MAP = {
    "company": "organization",
    "person": "person",
    "lab": "organization",
    "media": "organization",
    "academic": "person",
    "organization": "organization",
}

def map_source_type(v: str | None) -> str:
    if not v:
        return "person"
    return ENTITY_TYPE_MAP.get(v.strip().lower(), v.strip())


SECTOR_MAP = {
    "业界": "industry",
    "学界": "academia",
    "其他": "other",
    "媒体": "media",
}

def map_sector(v: str | None) -> str:
    if not v:
        return "other"
    return SECTOR_MAP.get(v.strip(), v.strip())


def new_uuid() -> str:
    return str(uuid.uuid4())


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    seen_orgs: set[str] = set()   # track org names already in org_inserts
    source_inserts: list[str] = []
    account_inserts: list[str] = []
    org_inserts: list[str] = []

    with open(CSV_PATH, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = row.get("名字", "").strip()
            if not name:
                continue

            # ── organisation lookup / create ───────────────────────────────
            org_name = row.get("组织", "").strip()
            # Use a subquery so we always resolve the *actual* id from the DB,
            # regardless of whether the org was pre-existing or just inserted.
            org_id_sql = "NULL"
            if org_name:
                if org_name not in seen_orgs:
                    seen_orgs.add(org_name)
                    org_inserts.append(
                        f"INSERT INTO organizations (id, name, org_type) "
                        f"VALUES (gen_random_uuid(), {pg_str(org_name)}, 'company') "
                        f"ON CONFLICT (name) DO NOTHING;"
                    )
                # resolve at query time — safe whether the row was just inserted or already existed
                org_id_sql = f"(SELECT id FROM organizations WHERE name = {pg_str(org_name)} LIMIT 1)"

            sid = new_uuid()
            twitter_url = row.get("Twitter", "").strip() or None
            activity_status = map_activity(row.get("活跃情况"))
            source_type = map_source_type(row.get("entity_type"))
            sector = map_sector(row.get("业界/学界/其他"))

            avg_days = pg_float(row.get("avg_interval_days"))
            last_tweet = pg_ts(row.get("last_tweet_at"))

            col_vals = {
                "id":                 f"'{sid}'",
                "name":               pg_str(name),
                "source_type":        f"'{source_type}'",
                "organization_id":    org_id_sql,
                "affiliation_type":   f"'{sector}'",
                "role_title":         pg_str(row.get("简介")),
                "description":        pg_str(row.get("简介")),
                "activity_status":    f"'{activity_status}'",
                "importance_score":   "0.5",
                "reliability_score":  "0.5",
                "is_active":          "true",
                # extended columns
                "tier":               pg_str(row.get("tier")),
                "sector":             f"'{sector}'",
                "research_focus":     pg_str(row.get("研究方向")),
                "tier_reason":        pg_str(row.get("tier_reason")),
                "notes":              pg_str(row.get("备注")),
                "source_authority":   pg_str(row.get("source_authority")),
                "last_tweet_at":      last_tweet,
                "avg_interval_days":  avg_days,
                "arxiv_author_query": pg_str(row.get("arxiv_author_query")),
                "affiliation_regex":  pg_str(row.get("affiliation_regex")),
                "orcid":              pg_str(row.get("orcid")),
                "twitter_url":        pg_str(twitter_url),
                "openalex_url":       pg_str(row.get("openalex_url")),
                "scholar_url":        pg_str(row.get("scholar_url")),
                "github_url":         pg_str(row.get("github_url")),
                "personal_url":       pg_str(row.get("personal_url")),
                "arxiv_homepage_url": pg_str(row.get("arxiv_homepage_url")),
            }

            # organization_id is a subquery → must use INSERT … SELECT, not INSERT … VALUES
            # Split columns into plain-value columns and the one subquery column.
            plain_cols = {k: v for k, v in col_vals.items() if k != "organization_id"}
            cols_str = ", ".join(plain_cols.keys())
            vals_str = ", ".join(plain_cols.values())
            source_inserts.append(
                f"INSERT INTO sources ({cols_str}, organization_id) "
                f"SELECT {vals_str}, {org_id_sql} "
                f"WHERE NOT EXISTS (SELECT 1 FROM sources WHERE name = {pg_str(name)});"
            )

            # Resolve source id at query time (handles pre-existing rows too)
            src_id_sql = f"(SELECT id FROM sources WHERE name = {pg_str(name)} LIMIT 1)"

            # ── source_accounts: twitter ───────────────────────────────────
            if twitter_url:
                handle_match = re.search(r"x\.com/([^/?]+)", twitter_url)
                handle = handle_match.group(1) if handle_match else None
                account_inserts.append(
                    f"INSERT INTO source_accounts (id, source_id, platform, handle, url, is_primary) "
                    f"VALUES (gen_random_uuid(), {src_id_sql}, 'x', {pg_str(handle)}, {pg_str(twitter_url)}, true) "
                    f"ON CONFLICT (platform, url) DO NOTHING;"
                )

            # ── source_accounts: other URLs ───────────────────────────────
            extra_urls = [
                ("google_scholar",  row.get("scholar_url", "").strip()),
                ("github",          row.get("github_url", "").strip()),
                ("homepage",        row.get("personal_url", "").strip()),
                ("openalex",        row.get("openalex_url", "").strip()),
                ("arxiv",           row.get("arxiv_homepage_url", "").strip()),
            ]
            for platform, url in extra_urls:
                if url:
                    account_inserts.append(
                        f"INSERT INTO source_accounts (id, source_id, platform, url) "
                        f"VALUES (gen_random_uuid(), {src_id_sql}, '{platform}', {pg_str(url)}) "
                        f"ON CONFLICT (platform, url) DO NOTHING;"
                    )

    # ── write SQL file ─────────────────────────────────────────────────────────
    lines = [
        "-- ============================================================",
        "-- HH Research: Signal-source import from CSV",
        "-- Generated by import_sources_csv.py",
        "-- Run this in Supabase SQL Editor (batched, safe ON CONFLICT)",
        "-- ============================================================",
        "",
        "BEGIN;",
        "",
        "-- 1. Organisations",
    ]
    lines.extend(org_inserts)
    lines += ["", "-- 2. Sources"]
    lines.extend(source_inserts)
    lines += ["", "-- 3. Source accounts (Twitter / Scholar / GitHub …)"]
    lines.extend(account_inserts)
    lines += ["", "COMMIT;", ""]

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK {len(org_inserts)} organisations")
    print(f"OK {len(source_inserts)} sources")
    print(f"OK {len(account_inserts)} accounts")
    print(f"Written to {OUT_PATH}")


if __name__ == "__main__":
    main()
