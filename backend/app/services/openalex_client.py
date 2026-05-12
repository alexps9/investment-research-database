"""
OpenAlex API client with async HTTP, retry logic, and transparent error handling

Performance Targets:
- Fetch 50 papers: < 5 seconds
- Fetch 50 references (parallel): < 10 seconds
- Rate limit compliance: < 10 req/s

Error Handling Philosophy:
- All errors must be transparent
- Include context: query, endpoint, status, response
- Provide actionable suggestions
"""

import asyncio
from typing import Dict, List, Optional

import httpx

from app.models.schemas import OpenAlexAPIError, Paper
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAlexClient:
    """
    Async client for OpenAlex API with retry and rate limiting

    API Documentation: https://docs.openalex.org/

    Features:
    - Async HTTP with httpx
    - Exponential backoff retry (max 3 attempts)
    - Rate limiting (max 10 concurrent requests)
    - Transparent error reporting
    - Automatic pagination support
    """

    BASE_URL = "https://api.openalex.org"
    TIMEOUT = 30.0  # seconds
    MAX_RETRIES = 3
    MAX_CONCURRENT = 10  # OpenAlex polite pool recommendation

    def __init__(self, max_concurrent: int = MAX_CONCURRENT):
        """
        Initialize OpenAlex client

        Args:
            max_concurrent: Maximum concurrent requests (rate limiting)
        """
        self._base_url = self.BASE_URL
        self._max_retries = self.MAX_RETRIES
        self._timeout = self.TIMEOUT
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Create async HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            limits=httpx.Limits(max_connections=max_concurrent * 2),
            headers={"User-Agent": "AcademicPaperAnalysisTool/1.0"},
        )

    async def _resolve_concept_id(self, query: str) -> Optional[str]:
        """
        Resolve a search query to the best matching OpenAlex concept ID.

        Uses /concepts?search=<query> and returns the top concept's ID.
        Falls back to None if no concept found (caller will use keyword search).

        Args:
            query: User's search term (e.g., "transformer")

        Returns:
            OpenAlex concept ID string (e.g., "C119857082") or None
        """
        url = f"{self._base_url}/concepts"
        params = {
            "search": query.strip(),
            "per-page": 1,
            "select": "id,display_name,works_count",
        }
        try:
            response = await self._retry_request(url, params)
            results = response.json().get("results", [])
            if results:
                raw_id = results[0]["id"]  # e.g. "https://openalex.org/C119857082"
                return raw_id.split("/")[-1]
        except Exception:
            pass  # concept lookup failure is non-fatal — fall back to keyword search
        return None

    async def fetch_papers(self, query: str, limit: int = 50) -> List[Paper]:
        """
        Fetch papers by search query using concept-based filtering when possible.

        Strategy:
        1. Resolve query → OpenAlex concept ID via /concepts?search=
        2. If concept found: filter by concept ID + CS concept, sort by cited_by_count desc
           This ensures foundational papers (e.g. "Attention Is All You Need") are included
           even if their titles don't contain the query keyword.
        3. If no concept found: fall back to keyword search (original behavior)

        Args:
            query: Search query string
            limit: Maximum number of papers to return (1-100)

        Returns:
            List of Paper objects

        Raises:
            ValueError: If query is empty or limit out of range
            OpenAlexAPIError: If API request fails
        """
        # Input validation
        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty. "
                "Provide a search term (e.g., 'machine learning', 'neural networks')."
            )

        if limit < 1 or limit > 100:
            raise ValueError(
                f"Limit must be between 1 and 100, got {limit}. "
                "OpenAlex API restricts per-page results to 100."
            )

        # Step 1: Try to resolve query to a concept ID
        concept_id = await self._resolve_concept_id(query.strip())
        if concept_id:
            logger.info(f"Query '{query}' resolved to concept ID: {concept_id}")
        else:
            logger.info(f"Query '{query}' resolved to no concept, falling back to keyword search")

        # Step 2: Build search params — concept-based preferred over keyword
        url = f"{self._base_url}/works"
        if concept_id:
            # Concept filter: returns papers tagged with this concept regardless of title.
            # NOTE: Do NOT filter by type:article — key ML papers (NeurIPS/ICML/arXiv) are
            # classified as "preprint" in OpenAlex. Type filter would exclude them.
            # C41008148 = Computer Science (keep domain scoping).
            # Fetch extra (2×limit) to allow post-filtering by concept relevance score.
            params = {
                "per-page": min(limit * 2, 200),
                "sort": "cited_by_count:desc",
                "filter": f"publication_year:2015-2026,concepts.id:{concept_id},concepts.id:C41008148",
                "select": "id,title,cited_by_count,publication_year,referenced_works,doi,authorships,concepts",
            }
        else:
            # Fallback: keyword search in title/abstract
            params = {
                "search": query.strip(),
                "per-page": limit,
                "sort": "cited_by_count:desc",
                "filter": "publication_year:2015-2026,type:article,concepts.id:C41008148",
                "select": "id,title,cited_by_count,publication_year,referenced_works,doi,authorships",
            }

        # Execute with retry
        response = await self._retry_request(url, params)

        # Parse response
        try:
            data = response.json()
            results = data.get("results", [])

            if not results:
                return []

            if concept_id:
                # Filter by concept relevance score >= 0.4 to remove loosely-tagged noise.
                # Also remove known OpenAlex data-error papers (inflated citations / wrong topic).
                _BLOCKLIST = {
                    "W4385245566",  # MizAR 60 for Mizar 50 — math paper, wrong topic
                    "W2896457183",  # AI-Assisted Pipeline — health AI, inflated in transformer results
                }
                MIN_SCORE = 0.2  # Lowered to include BERT/GPT papers with lower Transformer concept scores
                results = [
                    w for w in results
                    if w.get("id", "").split("/")[-1] not in _BLOCKLIST
                    and any(
                        c.get("id", "").endswith(concept_id) and c.get("score", 0) >= MIN_SCORE
                        for c in w.get("concepts", [])
                    )
                ][:limit]

            papers = [self._parse_work(work) for work in results]
            return papers

        except (KeyError, ValueError, TypeError) as e:
            raise OpenAlexAPIError(
                message=f"Failed to parse OpenAlex response for query '{query}'",
                status_code=response.status_code,
                details={"error": str(e), "response_preview": str(response.text)[:200]},
                suggestion="OpenAlex API format may have changed. Check docs at https://docs.openalex.org/",
            )

    async def fetch_works_by_ids(self, work_ids: List[str]) -> List[Paper]:
        """
        Fetch full metadata for multiple papers by their OpenAlex Work IDs.

        Uses pipe-separated filter for batch retrieval in a single request.

        Args:
            work_ids: List of OpenAlex Work IDs (e.g., ["W4384648639", "W4387356039"])

        Returns:
            List of Paper objects with full metadata (including abstract, institutions)

        Raises:
            OpenAlexAPIError: If API request fails
            ValueError: If work_ids is empty
        """
        if not work_ids:
            raise ValueError("work_ids must not be empty")

        # Build pipe-separated filter: openalex_id:W123|W456|W789
        full_urls = "|".join(f"https://openalex.org/{wid}" for wid in work_ids)
        params = {
            "filter": f"openalex_id:{full_urls}",
            "per-page": str(min(len(work_ids), 50)),
            "select": "id,title,publication_year,cited_by_count,authorships,"
            "referenced_works,doi,abstract_inverted_index",
        }

        logger.info(f"Fetching {len(work_ids)} works by ID")
        response = await self._retry_request(f"{self.BASE_URL}/works", params)
        data = response.json()
        results = data.get("results", [])

        papers = []
        for work in results:
            try:
                papers.append(self._parse_work(work))
            except (KeyError, TypeError) as e:
                logger.warning(f"Failed to parse work: {e}")

        logger.info(f"Successfully fetched {len(papers)}/{len(work_ids)} papers")
        return papers

    async def fetch_references(self, work_id: str) -> List[str]:
        """
        Fetch reference IDs for a single paper

        Args:
            work_id: OpenAlex Work ID (e.g., "W2123456789")

        Returns:
            List of reference Work IDs

        Raises:
            ValueError: If work_id is invalid format
            OpenAlexAPIError: If API request fails
        """
        # Validate Work ID format
        if not work_id or not work_id.startswith("W"):
            raise ValueError(
                f"Invalid Work ID format: '{work_id}'. "
                "Expected format: W followed by digits (e.g., 'W2123456789')."
            )

        # Build request
        url = f"{self._base_url}/works/{work_id}"
        params = {"select": "referenced_works"}

        # Execute with retry
        response = await self._retry_request(url, params)

        # Parse response
        try:
            data = response.json()
            references = data.get("referenced_works", [])

            # Filter out None values and extract Work IDs
            return [ref for ref in references if ref]

        except (KeyError, ValueError, TypeError) as e:
            raise OpenAlexAPIError(
                message=f"Failed to parse references for work '{work_id}'",
                status_code=response.status_code,
                details={"error": str(e)},
                suggestion="Check if Work ID exists at https://openalex.org/" + work_id,
            )

    async def fetch_all_references(self, work_ids: List[str]) -> Dict[str, List[str]]:
        """
        Fetch references for multiple papers in parallel

        Uses semaphore to limit concurrent requests (rate limiting).

        Args:
            work_ids: List of OpenAlex Work IDs

        Returns:
            Dict mapping work_id -> list of reference IDs

        Raises:
            OpenAlexAPIError: If fetching fails for ANY paper
                (transparent: includes all error details)

        Performance:
            50 papers: < 10 seconds (with max_concurrent=10)
        """

        async def fetch_with_semaphore(work_id: str):
            """Fetch with rate limiting"""
            async with self._semaphore:
                try:
                    refs = await self.fetch_references(work_id)
                    return work_id, refs
                except Exception as e:
                    return work_id, e

        # Execute all requests in parallel
        tasks = [fetch_with_semaphore(wid) for wid in work_ids]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Separate successes and failures
        references_map = {}
        errors = []

        for work_id, result in results:
            if isinstance(result, Exception):
                errors.append({"work_id": work_id, "error": str(result)})
            else:
                references_map[work_id] = result

        # Transparent error reporting
        if errors:
            error_summary = "; ".join(f"{e['work_id']}: {e['error']}" for e in errors[:3])
            if len(errors) > 3:
                error_summary += f" ...and {len(errors) - 3} more"

            raise OpenAlexAPIError(
                message=f"Failed to fetch references for {len(errors)}/{len(work_ids)} papers",
                details={
                    "failed_count": len(errors),
                    "success_count": len(references_map),
                    "errors": errors,
                },
                suggestion=(
                    f"Check network connectivity and OpenAlex API status. "
                    f"Failed IDs: {[e['work_id'] for e in errors[:3]]}"
                ),
            )

        return references_map

    async def _retry_request(self, url: str, params: dict) -> httpx.Response:
        """
        Execute HTTP request with exponential backoff retry

        Retry Strategy:
        - Attempt 1: immediate
        - Attempt 2: wait 1s
        - Attempt 3: wait 2s
        - Attempt 4: fail with transparent error

        Args:
            url: Request URL
            params: Query parameters

        Returns:
            httpx.Response object

        Raises:
            OpenAlexAPIError: If all retries fail
        """
        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.get(url, params=params)
                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                if attempt == self._max_retries:
                    raise OpenAlexAPIError(
                        message=f"Request timeout after {self._timeout}s (tried {attempt} times)",
                        status_code=0,
                        details={"url": url, "params": params, "timeout": self._timeout},
                        suggestion=(
                            "OpenAlex API may be experiencing high load. "
                            "Try again later or reduce query complexity."
                        ),
                    )
                # Exponential backoff
                await asyncio.sleep(2 ** (attempt - 1))

            except httpx.HTTPStatusError as e:
                # Handle rate limiting (429) with retry
                if e.response.status_code == 429 and attempt < self._max_retries:
                    await asyncio.sleep(2**attempt)  # Longer backoff for rate limit
                    continue

                # Other HTTP errors: fail immediately with transparent message
                raise OpenAlexAPIError(
                    message=f"OpenAlex API returned HTTP {e.response.status_code}",
                    status_code=e.response.status_code,
                    details={"url": url, "params": params, "response": e.response.text[:500]},
                    suggestion=(
                        f"HTTP {e.response.status_code} typically means:\n"
                        f"400: Invalid query syntax\n"
                        f"404: Resource not found\n"
                        f"429: Rate limit exceeded (wait 60s)\n"
                        f"503: Service unavailable (try later)"
                    ),
                )

            except httpx.RequestError as e:
                if attempt == self._max_retries:
                    raise OpenAlexAPIError(
                        message=f"Network error: {type(e).__name__}",
                        status_code=0,
                        details={"url": url, "error": str(e)},
                        suggestion="Check internet connection and firewall settings.",
                    )
                await asyncio.sleep(2 ** (attempt - 1))

    def _parse_work(self, data: dict) -> Paper:
        """
        Parse OpenAlex work JSON to Paper object

        Args:
            data: Raw JSON from OpenAlex /works endpoint

        Returns:
            Paper object

        Raises:
            KeyError, TypeError: If required fields missing
        """
        # Extract author names
        author_names = []
        institutions = []
        seen_institutions: set[str] = set()
        for authorship in data.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                author_names.append(name)
            # Extract institutions from each authorship
            for inst in authorship.get("institutions", []):
                inst_name = inst.get("display_name")
                if inst_name and inst_name not in seen_institutions:
                    institutions.append(inst_name)
                    seen_institutions.add(inst_name)

        # Process reference IDs: extract W1234567890 from https://openalex.org/W1234567890
        raw_refs = data.get("referenced_works", [])
        reference_ids = [ref.split("/")[-1] for ref in raw_refs if ref]

        publication_year = data.get("publication_year", 1900)
        cited_by_count = data.get("cited_by_count", 0)

        # Sanity cap: OpenAlex occasionally has inflated citation counts (data errors).
        # Cap at 10k citations per year since publication — well above any real ML paper's
        # actual rate (~5-6k/yr for top papers like Swin/ViT), catches obvious outliers.
        years_since_pub = max(1, 2025 - publication_year)
        cited_by_count = min(cited_by_count, years_since_pub * 10_000)

        # Reconstruct abstract from inverted index
        abstract = None
        abstract_inv = data.get("abstract_inverted_index")
        if abstract_inv:
            try:
                word_positions: list[tuple[int, str]] = []
                for word, positions in abstract_inv.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join(w for _, w in word_positions)
            except (TypeError, ValueError):
                abstract = None

        return Paper(
            id=data["id"].split("/")[-1],  # Extract W1234567890 from URL
            title=data["title"] or "Untitled",
            cited_by_count=cited_by_count,
            publication_year=publication_year,
            reference_ids=reference_ids,
            doi=data.get("doi"),
            author_names=author_names[:5],  # Limit to 5 authors
            abstract=abstract,
            institutions=institutions[:10],  # Limit to 10 institutions
        )

    async def close(self):
        """Close HTTP client (cleanup)"""
        await self._client.aclose()

    async def __aenter__(self):
        """Context manager support"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        await self.close()
