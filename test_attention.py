import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Search for the original Transformer paper
        resp = await client.get("https://api.openalex.org/works", params={
            "search": "Attention is all you need",
            "per-page": 3,
            "select": "id,title,cited_by_count,publication_year,concepts"
        })
        data = resp.json()
        print("=== 'Attention Is All You Need' ===")
        for r in data.get("results", []):
            print(f"Title: {r['title']}")
            print(f"Year: {r['publication_year']}")
            print(f"Citations: {r['cited_by_count']}")
            print("Concepts:")
            for c in r.get("concepts", [])[:5]:
                print(f"  {c['id']}: {c['display_name']} (score:{c.get('score')})")
            print()

asyncio.run(main())
