"""Import the world-model paper dataset into the entity knowledge graph.

Idempotent and re-runnable. Designed to run **inside the backend container** so
it reuses the app's async DB session / Supabase credentials:

    docker compose -f docker-compose.server.yml exec backend \
        python scripts/import_world_model_papers.py --reindex

What it creates (all matched/deduped by (canonical_name, entity_type)):
  - topic entities for the 4 lanes + 12 rows, with row --SUBTOPIC_OF--> lane
  - 186 paper entities (entity_type="paper"): name=full_title, homepage_url=arXiv
    /DOI/OpenAlex url, no PDF — only title, authors and a source url, per spec.
  - person entities for paper authors (capped per paper); existing people are
    reused via exact name/alias match, and optionally via vector search.
  - relations: paper --AUTHORED--> person, paper --FOCUSES_ON--> row-topic,
    and paper<->paper edges from the dataset `connections`
    (inherits=>BUILT_ON, borrows=>RELATED_TO, competes=>COMPETES_WITH).

To keep the import fast over a cross-region Supabase link, entities get
client-side UUIDs and everything is flushed in a single transaction (no
per-row round-trip).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import uuid
from pathlib import Path

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Entity, EntityRelation

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "world_model_export.json"

# Friendly display names for the taxonomy (lane / row keys -> human labels).
LANE_NAMES = {
    "rl_based": "RL-Based World Models",
    "video_gen": "Video-Generative World Models",
    "latent_space": "Latent-Space World Models",
    "vla": "Policy / VLA World Models",
}
ROW_NAMES = {
    "rssm_based": "RSSM-based World Models (PlaNet / Dreamer)",
    "transformer_wm": "Transformer World Models (TD-MPC)",
    "diffusion_planning": "Diffusion Planning (Diffuser)",
    "diffusion_video": "Diffusion Video Generation (Sora / Cosmos)",
    "autoregressive_video": "Autoregressive Video (Genie / LWM)",
    "3dgs_nerf": "3DGS / NeRF World Modeling",
    "jepa_based": "JEPA-based World Models (V-JEPA)",
    "dino_based": "DINO-based World Models",
    "slot_based": "Slot-based / Object-Centric World Models",
    "vla_llm": "LLM/VLM + Action (RT-2 / Octo)",
    "vla_diffusion": "Diffusion Policy (pi-0)",
    "vla_driving": "Driving VLA (GAIA-1 / DriveVLA)",
}
# dataset connection type -> graph relation type (subject builds on / relates object)
CONNECTION_RELATIONS = {
    "inherits": "BUILT_ON",
    "borrows": "RELATED_TO",
    "competes": "COMPETES_WITH",
}


def _paper_url(p: dict) -> str | None:
    if p.get("arxiv_id"):
        return f"https://arxiv.org/abs/{p['arxiv_id']}"
    if p.get("doi"):
        return f"https://doi.org/{p['doi']}"
    if p.get("openalex_id"):
        oid = p["openalex_id"].rsplit("/", 1)[-1]
        return f"https://openalex.org/{oid}"
    return None


def _paper_intro(p: dict) -> str:
    authors = p.get("authors") or []
    who = "、".join(authors[:3]) + ("等" if len(authors) > 3 else "") if authors else ""
    org = p.get("org") or ""
    yr = p.get("year")
    cite = p.get("cited_by_count") or 0
    bits = []
    if p.get("full_title") and p.get("full_title") != p.get("title"):
        bits.append(f"《{p['full_title']}》")
    if yr:
        bits.append(f"{yr} 年")
    if who:
        bits.append(f"由 {who}{('（' + org + '）') if org else ''} 提出")
    head = "，".join(bits)
    tail = f"被引约 {cite} 次。" if cite else ""
    return (head + ("。" if head else "") + tail).strip() or (p.get("title") or "")


class Importer:
    def __init__(self, db, max_authors: int, vector_match: bool):
        self.db = db
        self.max_authors = max_authors
        self.vector_match = vector_match
        # (entity_type, lower-label) -> Entity, indexed under name + canonical + aliases
        self.index: dict[tuple[str, str], Entity] = {}
        self.triples: set[tuple[str, str, str]] = set()
        self.created_entities = 0
        self.reused_entities = 0
        self.created_relations = 0

    async def load(self) -> None:
        rows = (await self.db.execute(select(Entity))).scalars().all()
        for e in rows:
            self._index(e)
        # alias matching for people
        from app.models import EntityAlias
        aliases = (await self.db.execute(select(EntityAlias))).scalars().all()
        ent_by_id = {e.id: e for e in rows}
        for a in aliases:
            ent = ent_by_id.get(a.entity_id)
            if ent is not None and a.alias:
                self.index.setdefault((ent.entity_type, a.alias.strip().lower()), ent)
        triples = (await self.db.execute(
            select(EntityRelation.subject_entity_id, EntityRelation.object_entity_id,
                   EntityRelation.relation_type)
        )).all()
        self.triples = {(s, o, t) for s, o, t in triples}

    def _index(self, e: Entity) -> None:
        for label in (e.name, e.canonical_name):
            if label:
                self.index.setdefault((e.entity_type, label.strip().lower()), e)

    def get_or_create(self, name: str, etype: str, *, homepage_url: str | None = None,
                      introduction: str | None = None, metadata: dict | None = None) -> Entity:
        nm = (name or "").strip()
        key = (etype, nm.lower())
        ent = self.index.get(key)
        if ent is not None:
            self.reused_entities += 1
            return ent
        ent = Entity(
            id=str(uuid.uuid4()), name=nm, canonical_name=nm, entity_type=etype,
            homepage_url=homepage_url, introduction=introduction, metadata_=metadata or {},
        )
        self.db.add(ent)
        self._index(ent)
        self.created_entities += 1
        return ent

    def relate(self, subj: Entity, rel: str, obj: Entity) -> None:
        if subj is None or obj is None or subj.id == obj.id:
            return
        triple = (subj.id, obj.id, rel)
        if triple in self.triples:
            return
        self.triples.add(triple)
        self.db.add(EntityRelation(
            id=str(uuid.uuid4()), subject_entity_id=subj.id, object_entity_id=obj.id,
            relation_type=rel, confidence=1.0, extracted_by="world_model_import",
        ))
        self.created_relations += 1

    async def match_person(self, author: str) -> Entity:
        """Reuse an existing person by exact name/alias, optionally by vector
        search, else create a new person entity."""
        nm = (author or "").strip()
        exact = self.index.get(("person", nm.lower()))
        if exact is not None:
            self.reused_entities += 1
            return exact
        if self.vector_match and nm:
            hit = await self._vector_person(nm)
            if hit is not None:
                self.reused_entities += 1
                return hit
        return self.get_or_create(nm, "person", metadata={"source": "world_model_papers"})

    async def _vector_person(self, name: str) -> Entity | None:
        """Strict semantic match against existing person entities (guards against
        false positives by requiring a high score + shared name token)."""
        try:
            from app.services import semantic
            hits = await semantic.semantic_search(self.db, name, object_types=["entity"], limit=5)
        except Exception:
            return None
        tokens = {t for t in name.lower().split() if len(t) > 2}
        for h in hits:
            if h.get("score", 0) < 0.92:
                continue
            ent = next((e for (et, _l), e in self.index.items()
                        if et == "person" and e.id == h["object_id"]), None)
            if ent is None:
                continue
            if tokens & {t for t in ent.name.lower().split() if len(t) > 2}:
                return ent
        return None

    async def run(self, data: dict) -> None:
        await self.load()

        # 1. taxonomy: lanes + rows (topic entities)
        lane_ents: dict[str, Entity] = {}
        for lane in data.get("lanes", []):
            lid = lane["id"]
            name = LANE_NAMES.get(lid, lane.get("title") or lid)
            lane_ents[lid] = self.get_or_create(
                name, "topic",
                metadata={"lane_key": lid, "level": "lane", "color": lane.get("color")},
            )
        row_ents: dict[str, Entity] = {}
        for row in data.get("rows", []):
            rid = row["id"]
            name = ROW_NAMES.get(rid, row.get("title") or rid)
            row_ents[rid] = self.get_or_create(
                name, "topic",
                introduction=row.get("subtitle"),
                metadata={"row_key": rid, "lane_key": row.get("lane"), "level": "row",
                          "subtitle": row.get("subtitle")},
            )
            lane = lane_ents.get(row.get("lane"))
            if lane is not None:
                self.relate(row_ents[rid], "SUBTOPIC_OF", lane)

        # 2. papers + authors + topic links
        paper_by_did: dict[str, Entity] = {}
        for p in data.get("papers", []):
            title = p.get("full_title") or p.get("title")
            if not title:
                continue
            paper = self.get_or_create(
                title, "paper",
                homepage_url=_paper_url(p),
                introduction=_paper_intro(p),
                metadata={
                    "short_title": p.get("title"), "year": p.get("year"),
                    "quarter": p.get("quarter"), "lane": p.get("lane"), "row": p.get("row"),
                    "org": p.get("org"), "arxiv_id": p.get("arxiv_id"), "doi": p.get("doi"),
                    "openalex_id": p.get("openalex_id"),
                    "cited_by_count": p.get("cited_by_count"), "impact_score": p.get("impact_score"),
                    "dataset_id": p.get("id"), "source": "world_model_papers",
                },
            )
            if p.get("id"):
                paper_by_did[p["id"]] = paper

            row = row_ents.get(p.get("row"))
            if row is not None:
                self.relate(paper, "FOCUSES_ON", row)

            for author in (p.get("authors") or [])[: self.max_authors]:
                if not author or not author.strip():
                    continue
                person = await self.match_person(author)
                self.relate(paper, "AUTHORED", person)

        # 3. paper<->paper connections
        for c in data.get("connections", []):
            subj = paper_by_did.get(c.get("source_id"))
            obj = paper_by_did.get(c.get("target_id"))
            rel = CONNECTION_RELATIONS.get(c.get("type"), "RELATED_TO")
            if subj is not None and obj is not None:
                self.relate(subj, rel, obj)

        await self.db.commit()


async def main() -> None:
    ap = argparse.ArgumentParser(description="Import world-model papers into the entity graph.")
    ap.add_argument("--file", default=str(DEFAULT_DATA), help="path to world_model_export.json")
    ap.add_argument("--max-authors", type=int, default=6, help="max authors linked per paper")
    ap.add_argument("--vector-match", action="store_true",
                    help="use semantic search to link authors to existing people (needs embeddings)")
    ap.add_argument("--reindex", action="store_true",
                    help="rebuild entity embeddings after import (so papers are searchable)")
    args = ap.parse_args()

    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    print(f"Loaded {len(data.get('papers', []))} papers, {len(data.get('lanes', []))} lanes, "
          f"{len(data.get('rows', []))} rows, {len(data.get('connections', []))} connections")

    async with AsyncSessionLocal() as db:
        imp = Importer(db, max_authors=args.max_authors, vector_match=args.vector_match)
        await imp.run(data)
        print(f"Entities: +{imp.created_entities} created, {imp.reused_entities} reused")
        print(f"Relations: +{imp.created_relations} created")

        if args.reindex:
            from app.services import semantic
            print("Reindexing entity embeddings…")
            counts = await semantic.reindex(db, object_types=["entity"])
            print(f"Reindexed: {counts}")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
