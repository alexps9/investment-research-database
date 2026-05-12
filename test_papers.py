import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Search with the correct concept ID
        resp = await client.get("https://api.openalex.org/works", params={
            "filter": "concepts.id:C66322947,publication_year:2015-2024,concepts.id:C41008148",
            "per-page": 10,
            "sort": "cited_by_count:desc",
            "select": "id,title,cited_by_count,publication_year,concepts"
        })
        data = resp.json()
        print("=== Papers for Transformer concept (C66322947) ===")
        for r in data.get("results", [])[:10]:
            # Check concept scores
            tr_score = None
            for c in r.get("concepts", []):
                if c["id"].endswith("C66322947"):
                    tr_score = c.get("score")
                    break
            print(f"  {r['cited_by_count']:>5} cite | {r['publication_year']} | {r['title'][:50]}... (score:{tr_score})")

asyncio.run(main())
