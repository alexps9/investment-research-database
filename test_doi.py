import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Search by DOI
        resp = await client.get("https://api.openalex.org/works", params={
            "filter": "doi:10.48550/arXiv.1706.03762",
            "per-page": 5,
            "select": "id,title,cited_by_count,publication_year"
        })
        data = resp.json()
        print("=== By arXiv DOI ===")
        for r in data.get("results", []):
            print(f"ID: {r['id']}")
            print(f"Title: {r['title']}")
            print(f"Citations: {r['cited_by_count']}")
            print()

        # Also try search by exact title
        resp2 = await client.get("https://api.openalex.org/works", params={
            "search": '"Attention Is All You Need"',
            "per-page": 10,
            "select": "id,title,cited_by_count,publication_year"
        })
        data2 = resp2.json()
        print("=== By exact title search ===")
        for r in data2.get("results", []):
            print(f"{r['cited_by_count']} cite | {r['publication_year']} | {r['title']}")

asyncio.run(main())
