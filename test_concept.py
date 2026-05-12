import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Test concept resolution
        resp = await client.get("https://api.openalex.org/concepts", params={
            "search": "transformer",
            "per-page": 5,
            "select": "id,display_name,works_count"
        })
        data = resp.json()
        print("=== Concepts for 'transformer' ===")
        for r in data.get("results", []):
            print(f"  {r['id']}: {r['display_name']} ({r.get('works_count',0)} works)")

        # Now test with "attention"
        resp2 = await client.get("https://api.openalex.org/concepts", params={
            "search": "attention mechanism",
            "per-page": 5,
            "select": "id,display_name,works_count"
        })
        data2 = resp2.json()
        print("\n=== Concepts for 'attention mechanism' ===")
        for r in data2.get("results", []):
            print(f"  {r['id']}: {r['display_name']} ({r.get('works_count',0)} works)")

asyncio.run(main())
