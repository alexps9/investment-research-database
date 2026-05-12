import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Get papers with Transformer concept, sorted by citation, year 2015-2024
        resp = await client.get("https://api.openalex.org/works", params={
            "filter": "concepts.id:C66322947,publication_year:2015-2024,concepts.id:C41008148",
            "per-page": 100,
            "sort": "cited_by_count:desc",
            "select": "id,title,cited_by_count,publication_year,concepts"
        })
        data = resp.json()
        
        # Find the original paper
        print("=== Searching for Attention Is All You Need in top 100 ===")
        found = None
        for r in data.get("results", []):
            if "attention" in r.get("title", "").lower() and "need" in r.get("title", "").lower():
                found = r
                print(f"FOUND: {r['title']}")
                print(f"  Year: {r['publication_year']}, Citations: {r['cited_by_count']}")
                print(f"  ID: {r['id']}")
                break
        
        if not found:
            print("Not in top 100. Checking 101-200...")
            # Get next page
            resp2 = await client.get("https://api.openalex.org/works", params={
                "filter": "concepts.id:C66322947,publication_year:2015-2024,concepts.id:C41008148",
                "per-page": 100,
                "sort": "cited_by_count:desc",
                "page": 2,
                "select": "id,title,cited_by_count,publication_year"
            })
            data2 = resp2.json()
            for r in data2.get("results", []):
                if "attention" in r.get("title", "").lower() and "need" in r.get("title", "").lower():
                    print(f"FOUND in 101-200: {r['title']}")
                    print(f"  Year: {r['publication_year']}, Citations: {r['cited_by_count']}")
                    break

asyncio.run(main())
