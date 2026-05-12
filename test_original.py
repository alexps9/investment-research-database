import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Search for original Attention is All You Need (2017)
        resp = await client.get("https://api.openalex.org/works", params={
            "search": '"Attention Is All You Need"',
            "per-page": 5,
            "select": "id,title,cited_by_count,publication_year,concepts"
        })
        data = resp.json()
        print("=== Original Transformer paper ===")
        for r in data.get("results", []):
            if "2017" in str(r.get("publication_year")) or r.get("cited_by_count", 0) > 30000:
                print(f"ID: {r['id']}")
                print(f"Title: {r['title']}")
                print(f"Year: {r['publication_year']}")
                print(f"Citations: {r['cited_by_count']}")
                print("Concepts:")
                for c in r.get("concepts", [])[:8]:
                    print(f"  {c['id']}: {c['display_name']} (score:{c.get('score')})")
                print()
                break

asyncio.run(main())
