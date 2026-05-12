"""
Citation Network Builder using NetworkX

Constructs directed citation graphs with community detection.

Algorithm:
1. Create directed graph (DiGraph)
2. Add nodes (papers) with attributes
3. Add edges (citations) from references
4. Detect communities using Louvain algorithm
5. Calculate graph metrics

Performance Targets:
- 500 nodes: < 5 seconds
- 1000 nodes: < 10 seconds
"""

from typing import Dict, List
import re
from collections import Counter

import networkx as nx
from networkx.algorithms import community

from app.models.schemas import (
    GraphConstructionError,
    GraphMetadata,
    GraphResponse,
    Link,
    Node,
    Paper,
)


class CitationNetworkBuilder:
    """
    Builder for citation network graphs

    Uses NetworkX DiGraph (directed) to represent citation relationships:
    - Edge from A to B means "A cites B"
    - Community detection via Louvain algorithm
    - Supports graphs with 1000+ nodes
    """

    def __init__(self) -> None:
        """Initialize empty directed graph"""
        self._graph: nx.DiGraph = nx.DiGraph()

    def build_network(self, papers: List[Paper]) -> GraphResponse:
        """
        Build complete citation network from papers

        Process:
        1. Validate input
        2. Add all papers as nodes
        3. Add citations as directed edges
        4. Detect communities
        5. Calculate metrics
        6. Convert to GraphResponse

        Args:
            papers: List of Paper objects from OpenAlex

        Returns:
            GraphResponse with nodes, links, metadata

        Raises:
            GraphConstructionError: If construction fails

        Example:
            builder = CitationNetworkBuilder()
            graph = builder.build_network(papers)
            print(f"{graph.metadata.total_nodes} nodes, {graph.metadata.communities} communities")
        """
        # Validate input
        if not papers:
            raise GraphConstructionError(
                message="Cannot build graph from empty paper list", details={"papers_count": 0}
            )

        if not isinstance(papers, list):
            raise GraphConstructionError(
                message=f"Expected list of Paper objects, got {type(papers)}",
                details={"type": str(type(papers))},
            )

        try:
            # Step 1: Add all papers as nodes (these are the "main" papers from search)
            main_ids = set()
            for paper in papers:
                self.add_paper(paper)
                main_ids.add(paper.id)

            # Step 2: Add citations ONLY between main papers (no placeholder nodes)
            # This keeps the graph clean and dense
            for paper in papers:
                for ref_id in paper.reference_ids:
                    if ref_id in main_ids:
                        self.add_citation(paper.id, ref_id)

            # Step 3: Detect communities
            community_map = self.calculate_communities()

            # Assign communities to nodes
            for node_id, comm_id in community_map.items():
                self._graph.nodes[node_id]["community"] = comm_id

            # Step 4: Calculate metrics
            avg_clustering = self._calculate_avg_clustering()

            # Step 4.5: Generate community names from paper titles
            community_names = self._generate_community_names(community_map)

            # Step 5: Validate graph
            self._validate_graph()

            # Step 6: Convert to response format
            return self.to_graph_response(
                num_communities=len(set(community_map.values())),
                avg_clustering=avg_clustering,
                community_names=community_names,
            )

        except Exception as e:
            # Transparent error handling
            if isinstance(e, GraphConstructionError):
                raise

            raise GraphConstructionError(
                message=f"Failed to build citation network: {type(e).__name__}",
                details={
                    "error": str(e),
                    "papers_count": len(papers),
                    "nodes_added": self._graph.number_of_nodes(),
                    "edges_added": self._graph.number_of_edges(),
                },
            )

    def add_paper(self, paper: Paper) -> None:
        """
        Add paper as node to graph

        Node attributes:
        - title: Paper title
        - cited_by_count: Citation count
        - publication_year: Year
        - community: Will be set later

        Args:
            paper: Paper object
        """
        self._graph.add_node(
            paper.id,
            title=paper.title,
            cited_by_count=paper.cited_by_count,
            publication_year=paper.publication_year,
            community=None,
        )

    def add_citation(self, source_id: str, target_id: str) -> None:
        """
        Add citation as directed edge

        Edge direction: source -> target means "source cites target"

        Args:
            source_id: Paper that cites
            target_id: Paper that is cited
        """
        if source_id == target_id:
            return

        if not self._graph.has_node(source_id):
            raise GraphConstructionError(
                message=f"Source node '{source_id}' not in graph", details={"source_id": source_id}
            )

        if not self._graph.has_node(target_id):
            raise GraphConstructionError(
                message=f"Target node '{target_id}' not in graph", details={"target_id": target_id}
            )

        self._graph.add_edge(source_id, target_id)

    def calculate_communities(self) -> Dict[str, int]:
        """
        Detect communities using Louvain algorithm

        Algorithm: Louvain (best for citation networks)
        - Time complexity: O(n log n)
        - Works on undirected graph (convert temporarily)

        Returns:
            Dict mapping node_id -> community_id

        Handles isolated nodes: Assigns separate community per isolated node
        """
        # Convert to undirected for community detection
        undirected = self._graph.to_undirected()

        # Louvain community detection with lower resolution to get fewer, larger communities
        try:
            communities = community.louvain_communities(undirected, resolution=0.8)
        except Exception:
            # Fallback for graphs without edges
            if self._graph.number_of_edges() == 0:
                # Each node is its own community
                communities = [{node} for node in self._graph.nodes()]
            else:
                raise

        # Convert to dict
        community_map = {}
        for comm_id, nodes in enumerate(communities):
            for node in nodes:
                community_map[node] = comm_id

        # Merge tiny communities (size 1) into nearest neighbor's community
        # This prevents dozens of singleton communities
        comm_sizes = Counter(community_map.values())
        tiny_comms = {c for c, sz in comm_sizes.items() if sz == 1}
        if tiny_comms:
            # Collect non-tiny community IDs for round-robin fallback
            non_tiny = [c for c in sorted(comm_sizes) if c not in tiny_comms]
            if not non_tiny:
                non_tiny = [comm_sizes.most_common(1)[0][0]]
            rr_idx = 0

            for node_id in list(community_map.keys()):
                if community_map[node_id] not in tiny_comms:
                    continue
                # Find a neighbor with a non-tiny community
                neighbors = list(undirected.neighbors(node_id))
                reassigned = False
                for nb in neighbors:
                    nb_comm = community_map.get(nb)
                    if nb_comm is not None and nb_comm not in tiny_comms:
                        community_map[node_id] = nb_comm
                        reassigned = True
                        break
                if not reassigned:
                    # Round-robin among non-tiny communities for balance
                    community_map[node_id] = non_tiny[rr_idx % len(non_tiny)]
                    rr_idx += 1

            # Re-number communities to be contiguous (0, 1, 2, ...)
            unique_comms = sorted(set(community_map.values()))
            remap = {old: new for new, old in enumerate(unique_comms)}
            community_map = {k: remap[v] for k, v in community_map.items()}

        return community_map

    def _calculate_avg_clustering(self) -> float:
        """Calculate average clustering coefficient"""
        if self._graph.number_of_edges() == 0:
            return 0.0

        undirected = self._graph.to_undirected()
        try:
            result: float = nx.average_clustering(undirected)
            return result
        except Exception:
            return 0.0

    # Common academic stopwords to exclude from community naming
    _STOP_WORDS = {
        "a", "an", "the", "of", "for", "and", "or", "in", "on", "to", "with",
        "is", "are", "was", "were", "by", "from", "at", "as", "its", "it",
        "using", "based", "via", "towards", "toward", "through", "between",
        "into", "over", "under", "about", "than", "upon", "after", "before",
        "model", "models", "method", "methods", "approach", "paper", "study",
        "analysis", "learning", "deep", "neural", "network", "networks",
        "new", "novel", "improved", "efficient", "large", "pre", "trained",
        "training", "data", "task", "tasks", "use", "problem", "framework",
        "system", "systems", "review", "survey", "comprehensive", "multi",
        "scale", "high", "low", "end", "two", "one", "self", "cross",
        "referenced", "research", "introduction", "results", "performance",
        "good", "better", "best", "first", "second", "third", "simple",
        "exploring", "limits", "point", "dynamic", "human", "physical",
        "layer", "single", "unified", "general", "generalized", "towards",
        "how", "what", "why", "when", "where", "which", "can", "not",
        "more", "less", "very", "much", "all", "every", "each", "both",
        "well", "real", "time", "world", "free", "open", "only", "also",
        "like", "make", "made", "just", "even", "still", "long", "short",
        "fast", "slow", "few", "many", "other", "same", "different",
        "optimizing", "taxonomic", "without", "beyond", "class",
    }

    def _generate_community_names(self, community_map: Dict[str, int]) -> Dict[str, str]:
        """
        Generate descriptive names for each community from paper titles.

        Extracts top keywords from titles of papers in each community,
        filtering out common stopwords.

        Args:
            community_map: Dict mapping node_id -> community_id

        Returns:
            Dict mapping community_id (str) -> descriptive name
        """
        # Group node IDs by community
        communities: Dict[int, list] = {}
        for node_id, comm_id in community_map.items():
            communities.setdefault(comm_id, []).append(node_id)

        names: Dict[str, str] = {}
        for comm_id, node_ids in communities.items():
            # Collect titles (skip placeholder titles)
            titles = []
            for nid in node_ids:
                title = self._graph.nodes[nid].get("title", "")
                if title and title != "Referenced Paper":
                    titles.append(title.lower())

            if not titles:
                names[str(comm_id)] = f"Cluster {comm_id + 1}"
                continue

            # Extract meaningful words and bigrams
            all_words = []
            all_bigrams = []
            for title in titles:
                words = re.findall(r'[a-z][a-z]+', title)
                meaningful = [w for w in words if w not in self._STOP_WORDS and len(w) > 2]
                all_words.extend(meaningful)
                # Generate bigrams from meaningful words
                for i in range(len(meaningful) - 1):
                    all_bigrams.append(f"{meaningful[i]} {meaningful[i+1]}")

            # Prefer bigrams if they appear enough, else use top unigrams
            bigram_counts = Counter(all_bigrams)
            word_counts = Counter(all_words)

            # Pick best label: top bigram if frequent enough, else top 2 unigrams
            top_bigrams = bigram_counts.most_common(3)
            top_words = word_counts.most_common(5)

            if top_bigrams and top_bigrams[0][1] >= 2:
                # Use top bigram, capitalize
                label = top_bigrams[0][0].title()
            elif len(top_words) >= 2:
                label = f"{top_words[0][0].title()} / {top_words[1][0].title()}"
            elif top_words:
                label = top_words[0][0].title()
            else:
                label = f"Cluster {comm_id + 1}"

            names[str(comm_id)] = label

        return names

    def _validate_graph(self) -> None:
        """
        Validate graph structure

        Checks:
        - All nodes have required attributes
        - All edges are valid
        - No self-loops (paper citing itself)

        Raises:
            GraphConstructionError: If validation fails
        """
        required_attrs = {"title", "cited_by_count", "publication_year", "community"}

        for node_id, attrs in self._graph.nodes(data=True):
            missing = required_attrs - set(attrs.keys())
            if missing:
                raise GraphConstructionError(
                    message=f"Node '{node_id}' missing attributes",
                    details={"missing": list(missing)},
                )

        # Check for self-loops
        self_loops = list(nx.selfloop_edges(self._graph))
        if self_loops:
            raise GraphConstructionError(
                message="Graph contains self-loops (paper citing itself)",
                details={"self_loops": self_loops[:5]},
            )

    def to_graph_response(self, num_communities: int, avg_clustering: float, community_names: Dict[str, str] | None = None) -> GraphResponse:
        """
        Convert NetworkX graph to GraphResponse

        Args:
            num_communities: Number of detected communities
            avg_clustering: Average clustering coefficient

        Returns:
            GraphResponse object
        """
        # Extract nodes
        nodes = [
            Node(
                id=node_id,
                title=attrs["title"],
                cited_by_count=attrs["cited_by_count"],
                publication_year=attrs["publication_year"],
                community=attrs.get("community"),
            )
            for node_id, attrs in self._graph.nodes(data=True)
        ]

        # Extract links
        links = [Link(source=source, target=target) for source, target in self._graph.edges()]

        # Create metadata
        metadata = GraphMetadata(
            total_nodes=len(nodes),
            total_links=len(links),
            communities=num_communities,
            community_names=community_names or {},
            avg_clustering=round(avg_clustering, 3),
        )

        return GraphResponse(nodes=nodes, links=links, metadata=metadata)
