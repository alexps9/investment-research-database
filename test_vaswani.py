import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Search by author Vaswani
        resp = await client.get("https://api.openalex.org/works", params={
            "filter": "author.id:A1969197896,publication_year:2017",
            "per-page": 5,
            "select": "id,title,cited_by_count,publication_year"
        })
        data = resp.json()
        print("=== Vaswani 2017 papers ===")
        for r in data.get("results", []):
            print(f"ID: {r['id']}")
            print(f"Title: {r['title']}")
            print(f"Year: {r['publication_year']}")
            print(f"Citations: {r['cited_by_count']}")
            print()

asyncio.run(main())
