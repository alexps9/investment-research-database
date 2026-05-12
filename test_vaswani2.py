import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Search for the original 2017 paper by title words
        resp = await client.get("https://api.openalex.org/works", params={
            "search": "Ashish Vaswani Noam Shazeer",
            "per-page": 10,
            "sort": "cited_by_count:desc",
            "select": "id,title,cited_by_count,publication_year,concepts"
        })
        data = resp.json()
        print("=== Papers by Vaswani/Shazeer ===")
        for r in data.get("results", []):
            print(f"\n{r['cited_by_count']} cite | {r['publication_year']}")
            print(f"Title: {r['title']}")
            # Check concepts
            has_tr = False
            for c in r.get("concepts", [])[:8]:
                if "Transformer" in c.get("display_name", ""):
                    has_tr = True
                print(f"  {c['id']}: {c['display_name']} (score:{c.get('score')})")
            if not has_tr:
                print("  ⚠️ NO Transformer concept!")

asyncio.run(main())
