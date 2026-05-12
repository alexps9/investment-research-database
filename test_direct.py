import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Try searching by DOI - Transformer paper DOI is 10.5555/3295222.3295349
        resp = await client.get("https://api.openalex.org/works/W2741809808")
        print("=== Direct lookup W2741809808 ===")
        if resp.status_code == 200:
            r = resp.json()
            print(f"Title: {r.get('title')}")
            print(f"Year: {r.get('publication_year')}")
            print(f"Citations: {r.get('cited_by_count')}")
            print("Concepts:")
            for c in r.get("concepts", [])[:5]:
                print(f"  {c['id']}: {c['display_name']} (score:{c.get('score')})")
        else:
            print(f"Status: {resp.status_code}")

asyncio.run(main())
