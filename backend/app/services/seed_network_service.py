"""
Seed network service: builds citation network from seed papers
with hand-labeled path tags and hand-crafted citation edges.

Key differences from search mode:
- Papers are fetched by known Work IDs (not searched)
- Citation edges are hand-defined (OpenAlex has no refs for arXiv preprints)
- Communities = hand-labeled paths (A/B/C/D), not Louvain
"""

from typing import Dict, List, Optional

from app.data.seed_papers import (
    PATH_NAMES,
    PATH_TO_COMMUNITY,
    SEED_CITATIONS,
    SEED_PAPERS,
    get_seed_map,
    get_seed_work_ids,
)
from app.models.schemas import (
    GraphMetadata,
    GraphResponse,
    Link,
    Node,
    Paper,
)
from app.services.openalex_client import OpenAlexClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def _fetch_all_seed_papers(client: OpenAlexClient) -> List[Paper]:
    """
    Fetch all seed papers, with fallback for papers not found in batch query.
    Some OpenAlex IDs (e.g. W6xxx) don't work in pipe-separated filters.
    """
    work_ids = get_seed_work_ids()
    papers = await client.fetch_works_by_ids(work_ids)

    fetched_ids = {p.id for p in papers}
    missing_ids = [wid for wid in work_ids if wid not in fetched_ids]

    if missing_ids:
        logger.info(f"Batch missed {len(missing_ids)} papers, fetching individually: {missing_ids}")
        for wid in missing_ids:
            try:
                single = await client.fetch_works_by_ids([wid])
                if not single:
                    # Try direct endpoint as last resort
                    from app.services.openalex_client import OpenAlexAPIError
                    resp = await client._retry_request(
                        f"{client.BASE_URL}/works/{wid}",
                        {"select": "id,title,publication_year,cited_by_count,authorships,"
                         "referenced_works,doi,abstract_inverted_index"},
                    )
                    data = resp.json()
                    papers.append(client._parse_work(data))
                    logger.info(f"Fetched {wid} via direct endpoint")
                else:
                    papers.extend(single)
            except Exception as e:
                logger.warning(f"Failed to fetch {wid}: {e}")

    return papers


async def build_seed_network() -> GraphResponse:
    """
    Build citation network from seed papers.

    Unlike search mode, this:
    1. Fetches papers by known IDs (with fallback)
    2. Uses hand-crafted citation edges (not OpenAlex refs)
    3. Uses hand-labeled paths (not Louvain communities)
    """
    seed_map = get_seed_map()

    async with OpenAlexClient() as client:
        papers = await _fetch_all_seed_papers(client)

    if not papers:
        raise ValueError("No seed papers fetched from OpenAlex")

    logger.info(f"Fetched {len(papers)} / {len(SEED_PAPERS)} seed papers")

    # Build nodes
    paper_map = {p.id: p for p in papers}
    nodes: List[Node] = []
    for paper in papers:
        seed = seed_map.get(paper.id)
        community = PATH_TO_COMMUNITY[seed.path] if seed else 0
        nodes.append(Node(
            id=paper.id,
            title=paper.title,
            cited_by_count=paper.cited_by_count,
            publication_year=paper.publication_year,
            community=community,
        ))

    # Build edges from hand-crafted citations
    valid_ids = {p.id for p in papers}
    links: List[Link] = []
    for source_id, target_id in SEED_CITATIONS:
        if source_id in valid_ids and target_id in valid_ids:
            links.append(Link(source=source_id, target=target_id))

    metadata = GraphMetadata(
        total_nodes=len(nodes),
        total_links=len(links),
        communities=len(PATH_NAMES),
        community_names=PATH_NAMES,
        avg_clustering=0.0,
    )

    return GraphResponse(nodes=nodes, links=links, metadata=metadata)


async def get_seed_papers_detail(path: Optional[str] = None) -> List[Dict]:
    """
    Get seed papers with full metadata + path labels.

    Args:
        path: Optional filter by path letter (A/B/C/D)
    """
    seed_map = get_seed_map()

    async with OpenAlexClient() as client:
        papers = await _fetch_all_seed_papers(client)

    paper_map: Dict[str, Paper] = {p.id: p for p in papers}

    results = []
    for seed in SEED_PAPERS:
        if path and seed.path != path:
            continue
        paper = paper_map.get(seed.work_id)
        if paper:
            results.append({
                "paper": paper,
                "path": seed.path,
                "tech_tags": seed.tech_tags,
                "primary_tag": seed.primary_tag,
            })

    return results
