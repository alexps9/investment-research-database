import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Use search= (keyword) instead of concept filter to find original paper
        resp = await client.get("https://api.openalex.org/works", params={
            "search": "transformer attention",
            "per-page": 30,
            "sort": "cited_by_count:desc",
            "filter": "publication_year:2017",
            "select": "id,title,cited_by_count,publication_year"
        })
        data = resp.json()
        print("=== 2017 papers with 'transformer attention' ===")
        for r in data.get("results", [])[:15]:
            print(f"{r['cited_by_count']:>5} cite | {r['publication_year']} | {r['title'][:60]}")

asyncio.run(main())
