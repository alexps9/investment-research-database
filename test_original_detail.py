import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Get full details of the original paper
        resp = await client.get("https://api.openalex.org/works/W2626778328")
        r = resp.json()
        print("=== Attention is all you need ===")
        print(f"Title: {r.get('title')}")
        print(f"Year: {r.get('publication_year')}")
        print(f"Citations: {r.get('cited_by_count')}")
        print("Concepts:")
        for c in r.get("concepts", []):
            print(f"  {c['id']}: {c['display_name']} (score:{c.get('score')})")

        # Check if it has the Transformer concept
        has_tr = any(c["id"].endswith("C66322947") for c in r.get("concepts", []))
        print(f"\nHas Transformer concept (C66322947): {has_tr}")

asyncio.run(main())
