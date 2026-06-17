"""
把 QiuTian 的 world-model 论文数据导入 Alex 的 investment-research-database。
直接调他后端的 API，幂等可重跑。

用法:
    python import_to_alex_db.py [--api http://localhost:8000]

前提: Alex 的后端在跑。
"""
import json
import httpx
import argparse
import time
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "backend" / "data" / "world_model_export.json"

# Taxonomy: lane/row → topic entities
LANE_NAMES = {
    "rl_based": "RL-Based World Models",
    "video_gen": "Video-Generative World Models",
    "latent_space": "Latent-Space World Models",
    "vla": "Policy / VLA",
}

ROW_DESCRIPTIONS = {
    "rssm_based": "RSSM-based (PlaNet / Dreamer系列)",
    "transformer_wm": "Transformer World Model (TD-MPC系列)",
    "diffusion_planning": "Diffusion Planning (Diffuser系列)",
    "diffusion_video": "Diffusion Video Generation (Sora/Cosmos)",
    "autoregressive_video": "Autoregressive Video (Genie 2/LWM)",
    "3dgs_nerf": "3DGS / NeRF World Modeling",
    "jepa_based": "JEPA-based (V-JEPA系列)",
    "dino_based": "DINO-based World Models",
    "slot_based": "Slot-based / Object-Centric",
    "vla_llm": "LLM/VLM + Action (RT-2/Octo)",
    "vla_diffusion": "Diffusion Policy (π0系列)",
    "vla_driving": "Driving VLA (GAIA-1/DriveVLA)",
}


def ensure_entity(client, name, entity_type, metadata=None):
    """幂等创建 entity，返回 id"""
    payload = {
        "name": name,
        "canonical_name": name,
        "entity_type": entity_type,
        "metadata": metadata or {},
    }
    r = client.post("/entities/ensure", json=payload)
    if r.status_code in (200, 201):
        return r.json()["id"]
    print(f"  [WARN] ensure {entity_type}/{name} failed: {r.status_code} {r.text[:100]}")
    return None


def add_relation(client, subject_id, relation_type, object_id):
    """添加关系（忽略重复）"""
    payload = {
        "subject_entity_id": subject_id,
        "relation_type": relation_type,
        "object_entity_id": object_id,
        "confidence": 1.0,
        "extracted_by": "import_to_alex_db.py",
    }
    r = client.post(f"/entities/{subject_id}/relations", json=payload)
    if r.status_code in (200, 201):
        return True
    if r.status_code == 409:
        return True  # already exists
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000", help="Alex 后端 API 地址")
    args = parser.parse_args()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    papers = data["papers"]
    rows_meta = data["rows"]
    print(f"Loaded {len(papers)} papers from {DATA_FILE.name}")

    client = httpx.Client(base_url=args.api, timeout=30)

    # 1. 创建 topic entities (lanes + rows)
    print("\n=== Creating topic entities ===")
    lane_ids = {}
    for lane_key, lane_name in LANE_NAMES.items():
        eid = ensure_entity(client, lane_name, "topic", {"lane_key": lane_key, "level": "lane"})
        lane_ids[lane_key] = eid
        print(f"  Lane: {lane_name} → {eid}")

    row_ids = {}
    for row_meta in rows_meta:
        row_key = row_meta["id"]
        row_name = ROW_DESCRIPTIONS.get(row_key, row_meta["name"])
        lane_key = row_meta["lane"]
        eid = ensure_entity(client, row_name, "topic", {
            "row_key": row_key,
            "lane_key": lane_key,
            "level": "row",
            "examples": row_meta.get("description", ""),
        })
        row_ids[row_key] = eid
        print(f"  Row: {row_name} → {eid}")
        # row SUBTOPIC_OF lane
        if eid and lane_ids.get(lane_key):
            add_relation(client, eid, "SUBTOPIC_OF", lane_ids[lane_key])

    # 2. 创建 paper entities + relations
    print(f"\n=== Creating {len(papers)} paper entities ===")
    created = 0
    for i, p in enumerate(papers):
        title = p.get("full_title") or p["title"]
        metadata = {
            "short_title": p["title"],
            "year": p["year"],
            "quarter": p["quarter"],
            "lane": p["lane"],
            "row": p["row"],
            "org": p.get("org", ""),
            "cited_by_count": p.get("cited_by_count", 0),
            "impact_score": p.get("impact_score", 0),
            "arxiv_id": p.get("arxiv_id", ""),
        }
        homepage = f"https://arxiv.org/abs/{p['arxiv_id']}" if p.get("arxiv_id") else None

        paper_id = ensure_entity(client, title, "paper", metadata)
        if not paper_id:
            continue
        created += 1

        # paper FOCUSES_ON row topic
        row_id = row_ids.get(p["row"])
        if row_id:
            add_relation(client, paper_id, "FOCUSES_ON", row_id)

        # paper AUTHORED by authors (create person entities)
        authors = p.get("authors") or []
        for author in authors[:5]:  # top 5 authors
            person_id = ensure_entity(client, author, "person", {
                "source": "world_model_papers",
                "primary_lane": p["lane"],
            })
            if person_id:
                add_relation(client, paper_id, "AUTHORED", person_id)

        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(papers)} ({created} created)")
            time.sleep(0.1)  # gentle on the API

    print(f"\n=== Done! Created/ensured {created} papers ===")
    print("Topics:", len(lane_ids) + len(row_ids))
    print("Check the graph at your frontend's /graph page")


if __name__ == "__main__":
    main()
