"""
Citation Network Builder Tests - TDD Approach

Coverage Target: >= 85%
"""

import pytest

from app.models.schemas import GraphConstructionError, GraphResponse, Paper
from app.services.citation_network import CitationNetworkBuilder

# ============================================================================
# Test 1: Build Network - Success
# ============================================================================


def test_build_network_creates_valid_graph():
    """
    RED: Write this test FIRST, see it FAIL
    GREEN: Implement build_network() to make it pass

    Input: 10 papers with references
    Expected: GraphResponse with correct node/link counts
    """
    # Arrange: Create test papers
    papers = [
        Paper(
            id=f"W{i}",
            title=f"Paper {i}",
            cited_by_count=i * 10,
            publication_year=2020 + i,
            reference_ids=[f"W{j}" for j in range(max(0, i - 2), i)],  # Cite previous 2 papers
        )
        for i in range(10)
    ]

    # Act
    builder = CitationNetworkBuilder()
    graph = builder.build_network(papers)

    # Assert
    assert isinstance(graph, GraphResponse)
    assert graph.metadata.total_nodes == 10

    # Papers cite previous ones, so edges = 0 + 1 + 2 + 2 + 2 + ... = 16
    expected_edges = sum(min(i, 2) for i in range(10))
    assert graph.metadata.total_links == expected_edges

    # Verify all nodes have communities
    assert all(node.community is not None for node in graph.nodes)

    # Verify node data
    node0 = next(n for n in graph.nodes if n.id == "W0")
    assert node0.title == "Paper 0"
    assert node0.cited_by_count == 0
    assert node0.publication_year == 2020


# ============================================================================
# Test 2: Build Network - Community Detection
# ============================================================================


def test_build_network_assigns_communities():
    """
    Test community detection with clear clusters

    Create 2 separate clusters:
    - Cluster 1: Papers 0-4 (interconnected)
    - Cluster 2: Papers 5-9 (interconnected)
    - No edges between clusters

    Expected: 2 communities detected
    """
    papers = []

    # Cluster 1: Papers 0-4
    for i in range(5):
        papers.append(
            Paper(
                id=f"W{i}",
                title=f"Cluster1 Paper {i}",
                cited_by_count=100,
                publication_year=2020,
                reference_ids=[f"W{j}" for j in range(5) if j != i][:2],  # Cite 2 others in cluster
            )
        )

    # Cluster 2: Papers 5-9
    for i in range(5, 10):
        papers.append(
            Paper(
                id=f"W{i}",
                title=f"Cluster2 Paper {i}",
                cited_by_count=200,
                publication_year=2021,
                reference_ids=[f"W{j}" for j in range(5, 10) if j != i][
                    :2
                ],  # Cite 2 others in cluster
            )
        )

    builder = CitationNetworkBuilder()
    graph = builder.build_network(papers)

    # Should detect 2 communities
    assert graph.metadata.communities >= 2

    # All nodes should have communities
    assert all(node.community is not None for node in graph.nodes)


# ============================================================================
# Test 3: Build Network - Isolated Nodes
# ============================================================================


def test_build_network_handles_isolated_nodes():
    """
    Test handling of papers with no references (isolated nodes)

    Input: 5 papers, none cite each other
    Expected: 5 nodes, 0 edges, 5 communities (each isolated)
    """
    papers = [
        Paper(
            id=f"W{i}",
            title=f"Isolated Paper {i}",
            cited_by_count=50,
            publication_year=2020,
            reference_ids=[],  # No references
        )
        for i in range(5)
    ]

    builder = CitationNetworkBuilder()
    graph = builder.build_network(papers)

    assert graph.metadata.total_nodes == 5
    assert graph.metadata.total_links == 0

    # Each isolated node gets its own community
    assert graph.metadata.communities == 5

    # All nodes should have community assignments
    assert all(node.community is not None for node in graph.nodes)


# ============================================================================
# Test 4: Build Network - Citation Direction
# ============================================================================


def test_build_network_validates_citation_direction():
    """
    Test that edges point in correct direction

    Given: Paper A cites Paper B
    Expected: Edge from A to B (not B to A)
    """
    papers = [
        Paper(
            id="W1",
            title="Paper A",
            cited_by_count=10,
            publication_year=2020,
            reference_ids=["W2"],  # A cites B
        ),
        Paper(
            id="W2", title="Paper B", cited_by_count=100, publication_year=2019, reference_ids=[]
        ),
    ]

    builder = CitationNetworkBuilder()
    graph = builder.build_network(papers)

    # Verify edge exists and direction is correct
    assert graph.metadata.total_links == 1

    link = graph.links[0]
    assert link.source == "W1"  # A cites B
    assert link.target == "W2"


# ============================================================================
# Test 5: Build Network - Empty Input
# ============================================================================


def test_build_network_handles_empty_input():
    """
    Test error handling for empty input

    Input: Empty list []
    Expected: GraphConstructionError with clear message
    """
    builder = CitationNetworkBuilder()

    with pytest.raises(GraphConstructionError) as exc_info:
        builder.build_network([])

    error = exc_info.value
    assert "empty paper list" in error.message.lower()
    assert error.details["papers_count"] == 0


# ============================================================================
# Test 6: Build Network - Performance (Large Graph)
# ============================================================================


@pytest.mark.slow
def test_build_network_performance_large_graph():
    """
    Performance test: 500 papers with 1000+ citations in < 5 seconds

    Run with: pytest -m slow
    """
    import time

    # Create 500 papers, each cites 2-3 random previous papers
    papers = []
    for i in range(500):
        num_refs = min(3, i)  # Cite up to 3 previous papers
        ref_ids = [f"W{j}" for j in range(max(0, i - 3), i)]

        papers.append(
            Paper(
                id=f"W{i}",
                title=f"Paper {i}",
                cited_by_count=i,
                publication_year=2000 + (i // 50),
                reference_ids=ref_ids,
            )
        )

    builder = CitationNetworkBuilder()

    start = time.time()
    graph = builder.build_network(papers)
    elapsed = time.time() - start

    # Verify results
    assert graph.metadata.total_nodes == 500
    assert graph.metadata.total_links > 1000

    # Performance target
    assert elapsed < 5.0, f"Took {elapsed}s, target < 5s"


# ============================================================================
# Additional Unit Tests
# ============================================================================


def test_add_paper_creates_node():
    """Test adding individual paper as node"""
    builder = CitationNetworkBuilder()
    paper = Paper(
        id="W123", title="Test Paper", cited_by_count=50, publication_year=2020, reference_ids=[]
    )

    builder.add_paper(paper)

    assert builder._graph.has_node("W123")
    assert builder._graph.nodes["W123"]["title"] == "Test Paper"


def test_add_citation_creates_edge():
    """Test adding citation as directed edge"""
    builder = CitationNetworkBuilder()

    # Add nodes first
    builder._graph.add_node("W1", title="A", cited_by_count=0, publication_year=2020)
    builder._graph.add_node("W2", title="B", cited_by_count=0, publication_year=2019)

    # Add edge
    builder.add_citation("W1", "W2")

    assert builder._graph.has_edge("W1", "W2")
    assert not builder._graph.has_edge("W2", "W1")  # Directed


def test_add_citation_validates_nodes_exist():
    """Test error when trying to add edge with missing nodes"""
    builder = CitationNetworkBuilder()

    with pytest.raises(GraphConstructionError) as exc_info:
        builder.add_citation("W1", "W2")

    assert "not in graph" in exc_info.value.message.lower()


def test_build_network_invalid_input_type():
    """Test error handling for invalid input type"""
    builder = CitationNetworkBuilder()

    with pytest.raises(GraphConstructionError) as exc_info:
        builder.build_network("not a list")

    assert "Expected list" in exc_info.value.message


def test_build_network_with_exception_during_construction():
    """Test transparent error handling when unexpected exception occurs"""
    builder = CitationNetworkBuilder()

    # Create a paper with invalid data that might cause issues
    class BrokenPaper:
        """Mock paper that raises error when accessing attributes"""

        @property
        def id(self):
            raise ValueError("Simulated error")

    broken_papers = [BrokenPaper()]

    with pytest.raises(GraphConstructionError) as exc_info:
        builder.build_network(broken_papers)

    error = exc_info.value
    assert "Failed to build citation network" in error.message
    assert "papers_count" in error.details
    assert "nodes_added" in error.details


def test_calculate_communities_no_edges():
    """Test community detection with no edges (all isolated nodes)"""
    builder = CitationNetworkBuilder()

    # Add isolated nodes
    for i in range(3):
        builder.add_paper(
            Paper(
                id=f"W{i}",
                title=f"Paper {i}",
                cited_by_count=10,
                publication_year=2020,
                reference_ids=[],
            )
        )

    community_map = builder.calculate_communities()

    # Each isolated node should be in its own community
    assert len(set(community_map.values())) == 3


def test_calculate_avg_clustering_no_edges():
    """Test clustering calculation with no edges"""
    builder = CitationNetworkBuilder()

    # Add isolated nodes
    builder.add_paper(
        Paper(id="W1", title="Paper 1", cited_by_count=10, publication_year=2020, reference_ids=[])
    )

    avg_clustering = builder._calculate_avg_clustering()
    assert avg_clustering == 0.0


def test_validate_graph_with_self_loop():
    """Test that self-loops are detected and raise error"""
    builder = CitationNetworkBuilder()

    # Manually create a self-loop (bypass normal add_citation logic)
    builder._graph.add_node(
        "W1", title="Test", cited_by_count=10, publication_year=2020, community=0
    )
    builder._graph.add_edge("W1", "W1")  # Self-loop

    with pytest.raises(GraphConstructionError) as exc_info:
        builder._validate_graph()

    assert "self-loops" in exc_info.value.message.lower()


def test_validate_graph_missing_attributes():
    """Test validation catches missing node attributes"""
    builder = CitationNetworkBuilder()

    # Add node with missing attributes
    builder._graph.add_node(
        "W1", title="Test", cited_by_count=10
    )  # Missing publication_year and community

    with pytest.raises(GraphConstructionError) as exc_info:
        builder._validate_graph()

    assert "missing attributes" in exc_info.value.message.lower()
