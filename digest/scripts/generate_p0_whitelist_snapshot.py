#!/usr/bin/env python3
"""Generate config/p0_whitelist.yml snapshot from Bitable whitelist table.

Applies tiering rules per Plan v3 §5.1 + R1-R5 refinements:
  - 活跃=非常                                  → P0
  - 活跃=一般 AND 组织 ∈ 顶级机构             → P0
  - 简介含 CEO/Founder/Chief AND 顶级机构      → P0
  - 公司官方账号 (硬编码列表)                  → P0+
  - 创业公司 11 人 (硬编码拆细 mapping)        → 按 Plan v3 §5.4
  - 名字 ∈ {TechCrunch, 独立媒体, 独立播客}    → P1
  - 其他                                       → P2

By default DRY-RUN (生成 YAML, 不写 Bitable).
With --write-bitable: also update Bitable tier / entity_type / source_authority.

Usage:
    python scripts/generate_p0_whitelist_snapshot.py
    python scripts/generate_p0_whitelist_snapshot.py --write-bitable
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

BASE_TOKEN = "UdwrbpCMoasCs3snCvbcKgbsnfc"
WHITELIST_TABLE_ID = "tblpVgQBAkPptnip"

# ============================================================
# Tiering rules (Plan v3 §5.1 + R1-R5)
# ============================================================

TOP_TIER_LABS = {
    "OpenAI", "Anthropic", "Google", "Google DeepMind", "Meta",
    "Microsoft", "xAI", "Apple", "NVIDIA", "Alphabet",
    "Deepseek", "Mistral AI",
    "Stanford", "MIT", "UCB", "UC Berkeley", "CMU", "Princeton", "Tsinghua",
}

# R1: 媒体/独立 → P1
MEDIA_OR_INDIVIDUAL = {
    "TechCrunch", "独立媒体", "独立播客", "独立开发者", "独立研究员",
    "Hacker News", "作家", "播客", "高管教练", "生产力专家",
    "AI 安全研究", "AI安全研究",
    "Intuition Machine",
}

# R2: 创业公司 11 人 → 拆细 (Plan v3 §5.4)
STARTUP_COMPANY_RESOLUTION = {
    "Andrew Ng":         {"org": "DeepLearning.AI",         "tier": "P0"},  # 公司 P0+ 另列
    "Ross Taylor":       {"org": "前 Meta reasoning lead (待 verify)", "tier": "P0"},
    "Kyle Corbitt":      {"org": "OpenPipe AI",             "tier": "P0"},
    "François Chollet":  {"org": "ARC Prize Foundation",    "tier": "P0"},
    "Jiaming Song":      {"org": "Luma AI",                 "tier": "P0+"},
    "Andrej Karpathy":   {"org": "Eureka Labs",             "tier": "P0+"},
    "Daniel Han":        {"org": "Unsloth AI",              "tier": "P0"},
    "hardmaru":          {"org": "Sakana AI",               "tier": "P0+"},
    "Georges Harik":     {"org": "Investor",                "tier": "P1"},  # R2-Georges = A
    "Brett Adcock":      {"org": "Figure AI",               "tier": "P0+"},
    "Junnan Li":         {"org": "Rhymes AI",               "tier": "P0"},
}

# R3/R4: 公司/lab 官方账号 → P0+
COMPANY_OFFICIAL_ACCOUNTS = {
    # 顶级实验室官方
    "OpenAI", "OpenAI Developers",
    "Anthropic",
    "GoogleAI", "Google AI", "Google Deepmind", "Google DeepMind", "Google AI Developers",
    "Meta", "Reality Labs at Meta",
    "MSR", "Microsoft Research",
    "xAI",
    "NVIDIA AI", "NVIDIA AI Developer",
    "Deepseek", "DeepSeek",
    "Mistral AI",
    "Alibaba Cloud",
    # P0 单条公司 (Plan v3 §5.4 + 已知)
    "Apple",
    "Perplexity",
    "Liquid AI",
    "Epoch AI",
    "Gradient AI",
    "Genmo",
    "Scale AI",
    "Physical Intelligence",
    "World Labs",
    "Isomorphic Labs",
    "Ella Mind AI",
    "Playground AI",
    "Sierra AI",
    "Together AI",
    "AGI House",
    "EleutherAI",
    "Keen Technologies",
    "Rabbit inc",
    "The Humanoid Hub",
    "TensorFlow",  # framework 但有官方账号
}

# C-level / Founder keywords in bio
EXEC_KEYWORDS = (
    "ceo", "co-founder", "cofounder", " founder", "chief scientist",
    "chief ai", "head of", "president of", "vp of", " vp ", "co founder",
)


def fetch_all_whitelist() -> list[dict[str, Any]]:
    """Fetch all rows from whitelist table (paginated)."""
    rows = []
    offset = 0
    limit = 200
    while True:
        result = subprocess.run(
            ["lark-cli", "base", "+record-list",
             "--as", "user",
             "--base-token", BASE_TOKEN,
             "--table-id", WHITELIST_TABLE_ID,
             "--limit", str(limit),
             "--offset", str(offset),
             "--format", "json",
             "--field-id", "名字",
             "--field-id", "组织",
             "--field-id", "业界/学界/其他",
             "--field-id", "活跃情况",
             "--field-id", "简介",
             "--field-id", "Twitter"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"record-list failed: {result.stderr[:300]}")
        payload = json.loads(result.stdout)
        data = payload["data"]
        fields_order = data["fields"]  # ['名字', '组织', '业界/学界/其他', '活跃情况', '简介', 'Twitter']
        record_ids = data["record_id_list"]
        rows_data = data["data"]
        for record_id, vals in zip(record_ids, rows_data):
            row = {"record_id": record_id}
            for i, fname in enumerate(fields_order):
                row[fname] = vals[i]
            rows.append(row)
        if not data.get("has_more", False):
            break
        offset += limit
    return rows


def _first(v: Any) -> Any:
    """If list, return first element; else return as-is."""
    if isinstance(v, list):
        return v[0] if v else None
    return v


def classify(row: dict[str, Any]) -> dict[str, str]:
    """Apply tiering rules. Returns dict with tier/entity_type/source_authority/notes."""
    name = (row.get("名字") or "").strip()
    org = _first(row.get("组织")) or ""
    cat = _first(row.get("业界/学界/其他")) or ""
    active = _first(row.get("活跃情况")) or ""
    bio = (row.get("简介") or "").lower()

    # R1: 媒体/独立 → P1
    if name in MEDIA_OR_INDIVIDUAL or org in MEDIA_OR_INDIVIDUAL:
        return {
            "tier": "P1",
            "entity_type": "media" if name in {"TechCrunch", "独立媒体"} else "person",
            "source_authority": "media" if name in {"TechCrunch", "独立媒体"} else "third_party",
            "notes": "R1: 媒体/独立账号降 P1",
        }

    # R3/R4: 公司官方账号 → P0+ company
    if name in COMPANY_OFFICIAL_ACCOUNTS:
        return {
            "tier": "P0+",
            "entity_type": "company",
            "source_authority": "official",
            "notes": "R3/R4: 公司官方账号 P0+",
        }

    # R2: 创业公司 11 人拆细
    if name in STARTUP_COMPANY_RESOLUTION:
        meta = STARTUP_COMPANY_RESOLUTION[name]
        return {
            "tier": meta["tier"],
            "entity_type": "person",
            "source_authority": "founder" if "founder" in bio or "ceo" in bio else "employee",
            "notes": f"R2: 拆细到 {meta['org']}",
        }

    # 顶级机构 (P0+ company already filtered out)
    is_top_tier_org = org in TOP_TIER_LABS

    # 活跃=非常 → P0
    if active == "非常":
        tier = "P0"
        # 公司高管 + 顶级 → 可能 P0+ (但这种少数；保守标 P0 + 看 bio)
        if is_top_tier_org and any(kw in bio for kw in EXEC_KEYWORDS):
            tier = "P0+"
        return {
            "tier": tier,
            "entity_type": "person" if cat in ("业界", "学界", "") else _entity_type_from_cat(cat),
            "source_authority": "founder" if "founder" in bio or "ceo" in bio else "employee",
            "notes": "活跃=非常",
        }

    # 活跃=一般 + 顶级机构 → P0
    if active == "一般" and is_top_tier_org:
        return {
            "tier": "P0",
            "entity_type": "person",
            "source_authority": "founder" if "founder" in bio or "ceo" in bio else "employee",
            "notes": "活跃=一般 + 顶级机构",
        }

    # bio 含高管词 + 顶级 → P0
    if is_top_tier_org and any(kw in bio for kw in EXEC_KEYWORDS):
        return {
            "tier": "P0",
            "entity_type": "person",
            "source_authority": "founder" if "founder" in bio or "ceo" in bio else "employee",
            "notes": "高管词 + 顶级机构",
        }

    # 活跃=一般 (非顶级) → P1
    if active == "一般":
        return {
            "tier": "P1",
            "entity_type": "person",
            "source_authority": "employee",
            "notes": "活跃=一般 (非顶级)",
        }

    # 其他 → P2
    return {
        "tier": "P2",
        "entity_type": "person",
        "source_authority": "employee" if cat == "业界" else "third_party",
        "notes": f"默认 P2 (活跃={active or '空'})",
    }


def _entity_type_from_cat(cat: str) -> str:
    if cat == "学界":
        return "person"  # academics 仍是 person，但所属 organization 可能 = university
    if cat == "业界":
        return "person"
    return "person"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate P0 whitelist YAML snapshot")
    parser.add_argument("--output", default="config/p0_whitelist.yml")
    parser.add_argument("--write-bitable", action="store_true",
                        help="ALSO update Bitable tier/entity_type/source_authority fields")
    args = parser.parse_args()

    print("📥 Fetching whitelist from Bitable...")
    rows = fetch_all_whitelist()
    print(f"   {len(rows)} rows fetched")

    print("🔖 Classifying...")
    classified = []
    tier_counts: dict[str, int] = {"P0+": 0, "P0": 0, "P1": 0, "P2": 0}
    for row in rows:
        c = classify(row)
        tier_counts[c["tier"]] += 1
        classified.append({
            "record_id": row["record_id"],
            "name": row.get("名字"),
            "org_in_bitable": _first(row.get("组织")) or "",
            "category": _first(row.get("业界/学界/其他")) or "",
            "active": _first(row.get("活跃情况")) or "",
            "twitter": row.get("Twitter"),
            **c,
        })

    snapshot = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "base_token": BASE_TOKEN,
            "table_id": WHITELIST_TABLE_ID,
            "total_rows": len(classified),
            "p0_plus_count": tier_counts["P0+"],
            "p0_count": tier_counts["P0"],
            "p1_count": tier_counts["P1"],
            "p2_count": tier_counts["P2"],
            "version": "v8.0",
        },
        "entities": classified,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        yaml.safe_dump(snapshot, f, allow_unicode=True, sort_keys=False, width=120)

    print(f"\n📊 Tier 分布:")
    for tier in ("P0+", "P0", "P1", "P2"):
        bar = "█" * (tier_counts[tier] // 4)
        print(f"   {tier:5s}  {tier_counts[tier]:4d}  {bar}")
    print(f"\n✅ Snapshot written to {output_path}")

    if args.write_bitable:
        print("\n⚠️  --write-bitable not yet implemented in this script.")
        print("   Use scripts/bootstrap_tier_field.py (Phase 1 follow-up) after user review.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
